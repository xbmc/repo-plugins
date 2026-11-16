"""Scanner callbacks never contact Jellyfin or enumerate interactive menus.

Every listing comes from the pinned committed generation, so a scan that
spans minutes sees one complete membership throughout, and nothing here can
turn a server outage into an empty directory.

A music listing cannot fail halfway (``_music_folder``).
"""

import time
from collections.abc import Collection, Iterable
from typing import TYPE_CHECKING, Any, Optional

import xbmcgui
import xbmcplugin

import xbmc

from kofin.core import kodirpc, state
from kofin.sync import private
from kofin.core.log import Logger
from kofin.core.urls import PARAM_MEDIA_SOURCE
from . import capabilities, metadata, paths, walk
from .records import PayloadWindow
from .records import Record
from .store import Store

if TYPE_CHECKING:
    from kofin.plugin.router import Request

# What a listing hands Kodi: (url, item, is a folder).
Entry = tuple[str, xbmcgui.ListItem, bool]

LOG = Logger(__name__)

# The longest a hold listing stays open on its own: the pass releases it,
# and a pass that died takes at most this long to let the scanner go.
HOLD_LIMIT = 600.0


def _roots() -> list[str]:
    """Every scanner root, for Kodi's own walk of the plugin: the bound video
    roots, and the music root of every library with a song."""
    from kofin.sync.private import Database

    with Database() as db:
        Store._prepare(db.cursor)
        roots = [
            row[0]
            for row in db.cursor.execute(
                "SELECT path FROM api_binding ORDER BY path"
            ).fetchall()
            # Every movie folder is bound (native.bind_folders); the root
            # listing names the library roots and the show folders.
            if not getattr(paths.parse(row[0]), "movie", None)
        ]
        for namespace, library in db.cursor.execute(
            "SELECT DISTINCT namespace, library FROM api_entry"
            " WHERE kind='Audio' AND removed IS NULL"
        ).fetchall():
            roots.append(paths.library_dir(namespace, library, "music"))
    return sorted(set(roots))


def _listing(request: "Request", entries: list[Entry], content: str) -> None:
    if content:
        xbmcplugin.setContent(request.handle, content)
    xbmcplugin.addDirectoryItems(request.handle, entries, len(entries))
    xbmcplugin.endOfDirectory(request.handle, succeeded=True, cacheToDisc=False)


def _folders(request: "Request", directories: Iterable[str], label: str) -> None:
    _listing(
        request,
        [(d, xbmcgui.ListItem(label, offscreen=True), True) for d in directories],
        "",
    )


def exists(
    store: Store,
    location: paths.Location,
    item_id: Optional[str],
    source: str = "",
    features: Collection[str] = frozenset(),
) -> bool:
    """Whether Kodi may keep a row: unknown state is unavailable, never proof
    of deletion. Only an explicit committed tombstone says an item is gone,
    and only a movie's own payload says a version file or an extra is: the
    scan that lists the folder adds and never removes, so Clean, which asks
    this per file, is the only way a row the listing no longer names can
    leave."""
    if location.probe:
        # A disc-structure folder Kodi probes for: never a row.
        return False
    if location.walk:
        # The pass's own scan directories: no row is ever filed under one.
        return True
    if item_id:
        state = store.state(item_id)
        if state is not None and state.operation == "remove":
            return False
        if source:
            # A version file exists while the movie still lists its source,
            # on a Kodi that groups versions (video_versions): elsewhere the
            # listing never names one, and a row an earlier Kodi filed goes.
            if "video_versions" not in features:
                return False
            record = store.records(kind="Movie", item_ids=[item_id]).get(item_id)
            if record is None:
                return True
            return any(
                str(s.get("Id")) == source
                for s in metadata.version_sources(record.item)
            )
        return True
    if location.extra:
        # An extra exists while its movie does and its payload still lists
        # the file by that name: the stem and the container both, so a
        # feature whose container moved leaves its old row to Clean.
        movie_id = location.movie or ""
        state = store.state(movie_id)
        if state is not None and state.operation == "remove":
            return False
        record = store.records(kind="Movie", item_ids=[movie_id]).get(movie_id)
        if record is None:
            return True
        return any(
            stem == location.extra
            and paths.video_container_of(feature) == location.extra_container
            for stem, feature in paths.extra_stems(
                metadata.special_features(record.item)
            )
        )
    if location.folder or location.movie:
        return True
    if location.series:
        state = store.state(location.series)
        return not state or state.operation != "remove"
    if location.library:
        prefix = paths.library_root(store.namespace, location.library)
        if any(path.startswith(prefix) for path in store.bindings()):
            return True
        return bool(store.records(library=location.library, pinned=False))
    return True


def serve(request: "Request") -> None:
    # One database connection for the life of this interpreter: a scanner
    # that reuses it between listings then pays the open once.
    private.pool_connections(True)
    if request.params.get(paths.FORGET):
        # Refused on purpose: Kodi keeps no listing of a failed request.
        xbmcplugin.endOfDirectory(request.handle, succeeded=False, cacheToDisc=False)
        return
    location = paths.parse(request.base_url)
    action = request.params.get("kodi_action", "")
    if location is None:
        if request.base_url.rstrip("/").endswith("/native"):
            _folders(request, _roots(), "Kofin")
            return
        xbmcplugin.endOfDirectory(request.handle, succeeded=False, cacheToDisc=False)
        return
    if location.hold:
        if action == "check_exists":
            xbmcplugin.setResolvedUrl(
                request.handle, True, xbmcgui.ListItem(path=request.base_url)
            )
            return
        _hold(request, location.hold)
        return
    store = Store(location.key)
    item_id = request.params.get("id") or location.song or ""
    # What this Kodi offers (the feature table) shapes every row listed and
    # every answer about one: read once per request, never per item.
    features = capabilities.features()
    if location.walk and location.library is not None and action != "check_exists":
        if location.part is None:
            _walk_parts(request, store, location.key, location.library)
        else:
            _music_part(request, store, location.key, location.library, location.part)
        return
    if action == "check_exists":
        # The source is in the query, never base_url: Kodi's argv[0], which
        # has none.
        source = request.params.get(PARAM_MEDIA_SOURCE, "")
        xbmcplugin.setResolvedUrl(
            request.handle,
            exists(store, location, item_id, source, features),
            xbmcgui.ListItem(path=request.base_url),
        )
        return
    key = location.key
    if location.library is None or location.content is None:
        prefix = (
            paths.library_root(key, location.library)
            if location.library
            else paths.root(key)
        )
        roots = {p for p in store.bindings() if p.startswith(prefix)}
        roots.update(
            paths.library_dir(key, library, "music")
            for library in store.libraries("Audio")
            if paths.library_dir(key, library, "music").startswith(prefix)
        )
        _folders(request, sorted(roots), "Kofin")
        return
    library = location.library
    if location.content == "music":
        if location.folder is None:
            _music_root(request, store, key, library)
        else:
            _music_folder(request, store, key, library, location.folder, features)
        return
    server = store.server()
    separator = metadata.item_separator()
    if location.content == "tvshows":
        if location.series is None:
            shows = store.records(kind="Series", library=library)
            seasons: dict[str, list[dict[str, Any]]] = {}
            for record in store.records(kind="Season", library=library).values():
                seasons.setdefault(record.parent_id, []).append(record.item)
            # Only the numbering reaches the show hash, and the store keeps
            # it per payload: no episode's payload is read for a show nothing
            # changed in.
            episodes = store.episode_rows(
                library, metadata.episode_row, metadata.EPISODE_ROW_FORMAT
            )
            entries = [
                (
                    paths.show_dir(key, library, series_id),
                    metadata.listitem(
                        record.item,
                        server,
                        key,
                        library,
                        separator,
                        seasons.get(series_id, []),
                        episodes.get(series_id, []),
                        features=features,
                    ),
                    True,
                )
                for series_id, record in sorted(shows.items())
            ]
            _listing(request, entries, "tvshows")
            return
        series_id = location.series
        if action == "refresh_info" and not item_id:
            show = store.records(kind="Series", item_ids=[series_id]).get(series_id)
            if show is None:
                xbmcplugin.endOfDirectory(
                    request.handle, succeeded=False, cacheToDisc=False
                )
                return
            entry = (
                paths.show_dir(key, library, series_id),
                metadata.listitem(
                    show.item,
                    server,
                    key,
                    library,
                    separator,
                    [
                        r.item
                        for r in store.records(
                            kind="Season", parent_id=series_id
                        ).values()
                    ],
                    [
                        r.item
                        for r in store.records(
                            kind="Episode", parent_id=series_id
                        ).values()
                    ],
                    features=features,
                ),
                True,
            )
            _listing(request, [entry], "tvshows")
            return
        records = store.records(
            kind="Episode",
            parent_id=series_id,
            item_ids=[item_id] if action == "refresh_info" else None,
            payloads=False,
        )
        kind, content = "Episode", "episodes"
    else:
        # A movie's URL sits in a folder of its own (paths.movie_dir), so the
        # root lists every movie as a file -- never as folders: Kodi turns a
        # plugin folder in a movies listing into a phantom VIDEO_TS.IFO,
        # because CPluginFile::Exists is unconditionally true
        # (FileItemList.cpp ConvertDiscFoldersToFiles) -- and a folder, bound
        # on demand, lists its one movie for a scan by name.
        kind = "Movie" if location.content == "movies" else "MusicVideo"
        content = location.content
        if location.extras:
            if location.probe:
                # A disc-structure folder Kodi probes for below the extras
                # folder (VIDEO_TS/, BDMV/): an empty listing, so that the
                # directory cache can answer the probe with "no such file".
                _listing(request, [], "")
            elif location.extra:
                # A file in the folder is played, never listed: the router
                # sends a resolved one to the play route and fails the rest.
                xbmcplugin.setResolvedUrl(
                    request.handle, False, xbmcgui.ListItem(path=request.base_url)
                )
            else:
                _extras_folder(
                    request, store, key, library, location.movie or "", features
                )
            return
        wanted = [item_id] if action == "refresh_info" else None
        if kind == "Movie" and location.movie:
            wanted = [location.movie]
        records = store.records(
            kind=kind,
            library=library,
            item_ids=wanted,
            payloads=False,
        )
    if action == "refresh_info" and not records:
        xbmcplugin.endOfDirectory(request.handle, succeeded=False, cacheToDisc=False)
        return
    collections = (
        metadata.collections_of(r.item for r in store.records(kind="BoxSet").values())
        if kind == "Movie"
        else {}
    )
    # Payloads are read a chunk at a time and let go once their ListItem is
    # built.
    entries = []
    window = PayloadWindow(store)
    for record in window.walk(records[i] for i in sorted(records)):
        record_id = record.item_id
        if kind == "Episode" and metadata.episode_numbers(record.item) is None:
            # Kodi cannot file an unnumbered special; it stays dynamic-only.
            continue
        if kind == "Movie":
            entries.extend(
                _movie_entries(
                    record,
                    server,
                    key,
                    library,
                    separator,
                    collections.get(record_id, ""),
                    # The folder scanned by name lists the movie's versions
                    # and extras; the root walk and a refresh (which takes
                    # the first item) list the movie's own file alone.
                    assets=bool(location.movie) and action != "refresh_info",
                    features=features,
                )
            )
            continue
        entries.append(
            (
                paths.playback_url(key, kind, library, record_id, record.parent_id),
                metadata.listitem(
                    record.item,
                    server,
                    key,
                    library,
                    separator,
                    set_name=None,
                    features=features,
                ),
                False,
            )
        )
    _listing(request, entries, content)


# -- movie versions and extras --------------------------------------------------


def _movie_entries(
    record: Record,
    server: str,
    key: str,
    library: str,
    separator: str,
    set_name: str,
    assets: bool,
    features: Collection[str] = frozenset(),
) -> list[Entry]:
    """A movie's file, and with ``assets`` a file per further media source,
    each carrying the whole tag and the source's name as its video asset
    title, and the movie's extras folder (see metadata.Version).

    The extras folder is read only when the pass has warmed Kodi's
    directory cache for it (native._prepare_scan) and the folder's binding
    uses folder names, which the pass sets.
    """
    item = record.item
    url = paths.playback_url(key, "Movie", library, record.item_id)
    # Without video_versions a Kodi cannot group a further file under the
    # movie, so the folder lists the movie's own file alone and the default
    # source plays; the extras folder is Kodi 22's too.
    sources = metadata.version_sources(item) if "video_versions" in features else []

    def row(
        name: str = "", source: Optional[dict[str, Any]] = None
    ) -> xbmcgui.ListItem:
        shown = item
        if source is not None:
            # The version's own streams and runtime, where the source has them.
            shown = dict(item, MediaSources=[source])
            if source.get("MediaStreams"):
                shown["MediaStreams"] = source["MediaStreams"]
            if source.get("RunTimeTicks"):
                shown["RunTimeTicks"] = source["RunTimeTicks"]
        li: xbmcgui.ListItem = metadata.listitem(
            shown,
            server,
            key,
            library,
            separator,
            set_name=set_name,
            features=features,
            version=(
                metadata.Version.of(
                    name, source is None, metadata.unique_ids(item, key)
                )
                if sources
                else None
            ),
        )
        return li

    entries = [(url, row(metadata.version_label(sources[0]) if sources else ""), False)]
    if not assets:
        return entries
    for source in sources[1:]:
        entries.append(
            (
                paths.version_url(key, library, record.item_id, source["Id"]),
                row(metadata.version_label(source), source),
                False,
            )
        )
    if metadata.special_features(item):
        entries.append(
            (
                paths.extras_dir(key, library, record.item_id),
                xbmcgui.ListItem(paths.EXTRAS.rstrip("/"), offscreen=True),
                True,
            )
        )
    return entries


def _extras_folder(
    request: "Request",
    store: Store,
    key: str,
    library: str,
    movie_id: str,
    kodi_features: Collection[str] = frozenset(),
) -> None:
    """A movie's extras: a file per special feature, named by its title with
    a video extension, built from the movie's payload."""
    server = store.server()
    record = store.records(kind="Movie", library=library, item_ids=[movie_id]).get(
        movie_id
    )
    features = metadata.special_features(record.item) if record is not None else []
    entries = [
        (
            paths.extra_url(key, library, movie_id, stem, feature),
            metadata.extra_listitem(feature, server, features=kodi_features),
            False,
        )
        for stem, feature in paths.extra_stems(features)
    ]
    LOG.debug("extras folder of movie %s: %d rows", movie_id[:8], len(entries))
    _listing(request, entries, "videos")


def resolve_extra(location: paths.Location) -> str:
    """The item id of the extra a file-style extras URL names, from the
    movie's payload alone: every publish path attaches the features
    (library.attach_extras), so a stem the catalogue does not name is a
    file the listing no longer has, not a lookup to make elsewhere."""
    movie_id = location.movie or ""
    record = (
        Store(location.key).records(kind="Movie", item_ids=[movie_id]).get(movie_id)
    )
    features = metadata.special_features(record.item) if record is not None else []
    for stem, feature in paths.extra_stems(features):
        if stem == location.extra:
            return str(feature["Id"])
    return ""


# -- music ---------------------------------------------------------------------


def _music_root(request: "Request", store: Store, key: str, library: str) -> None:
    """The library's album directories: every live one, and every one that
    still has songs to shed (walk.root_folders)."""
    _album_folders(request, key, library, walk.rows(store, library))


def _music_part(
    request: "Request", store: Store, key: str, library: str, index: int
) -> None:
    """One part of the scan the pass planned (store.plan_walk): its
    directories under the labels planned for them, with no payload read. A
    part the plan does not reach lists nothing, and that costs nothing: no
    song is filed under a part, so a scan of one removes none."""
    _album_folders(
        request, key, library, store.walk_part(library, index, paths.MUSIC_PART)
    )


def _walk_parts(request: "Request", store: Store, key: str, library: str) -> None:
    """The parts of the plan, for whoever lists their parent: Kodi takes a
    directory to exist from the cached listing of its parent when it has
    one, so this listing never leaves a part of the plan out."""
    _folders(
        request,
        [
            paths.music_part(key, library, index)
            for index in range(walk.parts(store.walk_size(library)))
        ],
        "Kofin",
    )


def _album_folders(
    request: "Request", key: str, library: str, rows: Iterable[tuple[str, str]]
) -> None:
    _listing(
        request,
        [
            (
                paths.music_dir(key, library, folder),
                xbmcgui.ListItem(label, offscreen=True),
                True,
            )
            for folder, label in rows
        ],
        "",
    )


RETRY_DELAY = 5.0
KNOWN_PAGE = 500


def _wait(seconds: float) -> bool:
    """Pause inside a listing; True when Kodi is shutting down."""
    return xbmc.Monitor().waitForAbort(seconds)


def _music_folder(
    request: "Request",
    store: Store,
    key: str,
    library: str,
    folder: str,
    features: Collection[str] = frozenset(),
) -> None:
    """One album's complete listing, in one call, however long it takes.

    The scanner never reads the succeeded flag: RetrieveMusicInfo removes
    every song on the path and re-adds what was listed, so a listing that
    failed before any row, raised past dispatch (which ends the directory
    with nothing added) or stopped half way is the directory deleted and
    nothing in the pass putting it back. Nothing short of a complete listing
    is handed over: the store's, or Kodi's own rows read back in full with
    the paged total proving the count. Until one of them answers the listing
    waits, and leaves only with Kodi.

    The store's listing is recorded before it is handed over
    (``Store.note_listed``): a song's tags reach Kodi only through it, and
    the pass reads the record once its scan has ended (``MusicPass.listed``).
    """
    directory = paths.music_dir(key, library, folder)
    began = time.monotonic()
    while True:
        try:
            entries = _song_entries(store, key, library, folder, features)
            _note_listed(store, library, folder)
            break
        except Exception:
            LOG.exception("music listing unavailable for %s", directory)
        try:
            entries = _known_entries(directory)
            LOG.warning(
                "re-listing the %d rows Kodi holds for %s", len(entries), directory
            )
            break
        except Exception:
            LOG.exception("rows Kodi holds for %s could not be proven", directory)
        if _wait(RETRY_DELAY):
            # Shutting down: the scanner is being stopped, and a directory
            # it never hears about is a directory it never touches.
            LOG.warning("abandoning the listing of %s at shutdown", directory)
            return
    built = time.monotonic()
    _listing(request, entries, "songs")
    LOG.debug(
        "music folder %s: %d songs, built in %.2f s, handed over in %.2f s",
        folder[-8:],
        len(entries),
        built - began,
        time.monotonic() - built,
    )


def _note_listed(store: Store, library: str, folder: str) -> None:
    """``Store.note_listed``, never at the listing's expense: a directory
    left unrecorded costs the pass another scan of it."""
    try:
        store.note_listed(library, folder)
    except Exception:
        LOG.exception("music folder %s: its listing was not recorded", folder[-8:])


def _song_entries(
    store: Store,
    key: str,
    library: str,
    folder: str,
    features: Collection[str] = frozenset(),
) -> list[Entry]:
    began = time.monotonic()
    songs = store.records(kind="Audio", library=library, parent_id=folder)
    album = None
    if not folder.startswith(paths.SINGLES):
        found = store.records(kind="MusicAlbum", item_ids=[folder])
        album = found[folder].item if folder in found else None
    LOG.debug(
        "music folder %s: %d songs read in %.2f s",
        folder[-8:],
        len(songs),
        time.monotonic() - began,
    )
    salt = store.salt(folder)
    entries = []
    for item_id, record in sorted(songs.items()):
        url = paths.song_url(
            key, library, folder, item_id, paths.container_of(record.item)
        )
        try:
            li = metadata.song_listitem(record.item, album, salt, features)
        except Exception:
            # One malformed payload must not cost the directory a song.
            LOG.exception("song row reduced to its title: %s", item_id)
            li = metadata.fallback_song_listitem(record.item)
        entries.append((url, li, False))
    return entries


def _known_entries(directory: str) -> list[Entry]:
    """Kodi's own rows for the directory, proven complete, as a listing it
    will keep: the tags are Kodi's readback, the ids and play counts survive
    by file name, and the next pass finds the hash moved and lists the
    directory properly. The paged total must equal the rows read, as
    ``Readback._paged`` demands -- a partial array is a deletion with a
    row left -- and anything else raises for the caller to wait on.
    """
    rows: list[dict[str, Any]] = []
    total = None
    while True:
        reply = kodirpc.call(
            "AudioLibrary.GetSongs",
            {
                "properties": [
                    "file",
                    "title",
                    "artist",
                    "albumartist",
                    "album",
                    "genre",
                    "track",
                    "disc",
                    "duration",
                    "year",
                    "musicbrainztrackid",
                    "musicbrainzalbumid",
                ],
                "filter": {
                    "field": "path",
                    "operator": "startswith",
                    "value": directory,
                },
                "limits": {"start": len(rows), "end": len(rows) + KNOWN_PAGE},
            },
        )
        if not isinstance(reply, dict) or not isinstance(
            reply.get("limits", {}).get("total"), int
        ):
            raise RuntimeError("Kodi did not answer for " + directory)
        count = reply["limits"]["total"]
        if total is not None and count != total:
            raise RuntimeError("Kodi's rows changed while being read")
        total = count
        chunk = reply.get("songs") or []
        rows.extend(chunk)
        if len(rows) >= total:
            break
        if not chunk:
            raise RuntimeError("partial readback of " + directory)
    if len(rows) != total:
        raise RuntimeError("partial readback of " + directory)
    entries = []
    for row in rows:
        if not row.get("file", "").startswith(directory):
            continue
        li = xbmcgui.ListItem(row.get("title") or row.get("label", ""), offscreen=True)
        tag = li.getMusicInfoTag()
        tag.setMediaType("song")
        tag.setTitle(row.get("title") or row.get("label", ""))
        if row.get("album"):
            tag.setAlbum(row["album"])
        if row.get("albumartist"):
            tag.setAlbumArtist(" / ".join(row["albumartist"]))
        if row.get("artist"):
            tag.setArtist(" / ".join(row["artist"]))
        if row.get("genre"):
            tag.setGenres(list(row["genre"]))
        if row.get("track"):
            tag.setTrack(int(row["track"]))
        if row.get("disc"):
            tag.setDisc(int(row["disc"]))
        if row.get("duration"):
            tag.setDuration(int(row["duration"]))
        if row.get("year"):
            tag.setYear(int(row["year"]))
        if row.get("musicbrainztrackid"):
            tag.setMusicBrainzTrackID(row["musicbrainztrackid"])
        if row.get("musicbrainzalbumid"):
            tag.setMusicBrainzAlbumID(row["musicbrainzalbumid"])
        metadata.mark_loaded(li, 0)
        entries.append((row["file"], li, False))
    return entries


# -- the scanner hold ----------------------------------------------------------


def _hold(request: "Request", scanner: str) -> None:
    """Keep the scanner's listing of the hold directory open while the pass
    writes, then list it empty (native.hold).

    The token the service set is the one this listing waits on; a different
    or cleared token ends it, and so does the limit.
    """
    token = state.native_hold(scanner)
    monitor = xbmc.Monitor()
    deadline = time.monotonic() + HOLD_LIMIT
    while token and state.native_hold(scanner) == token:
        if time.monotonic() >= deadline or monitor.waitForAbort(0.25):
            break
    _listing(request, [], "")
