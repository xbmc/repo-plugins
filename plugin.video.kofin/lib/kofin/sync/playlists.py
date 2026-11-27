"""One-way materialization of Jellyfin playlists as native Kodi playlists.

Each Audio playlist is one ``.m3u8`` under
``special://profile/playlists/music/Kofin/``, named after the playlist's title
(``_unique_stem``, no ``kofin`` prefix). The folder is the ownership boundary —
never touch sibling files under ``playlists/music/``. Video playlists go to
``playlists/video/Kofin/``, beside the per-library smart playlists written at
the end of this module.
"""

from __future__ import annotations

import os
import re
import shutil
import sys
import unicodedata
import xml.etree.ElementTree as etree
from typing import (
    Any,
    NamedTuple,
)
from collections.abc import Iterable

import xbmcvfs

from kofin.core import settings
from kofin.core.log import Logger
from kofin.core.api import paged
from kofin.sync import kofindb as jellyfin_db
from kofin.sync.policy import reference_checksum
from kofin.sync.nodes import fs, video

LOG = Logger(__name__)

FOLDER_NAME = "Kofin"
PLAYLISTS_MUSIC = "special://profile/playlists/music"
PAGE_SIZE = 100

# How a managed playlist folder gets the addon's own icon instead of Kodi's
# generic folder glyph. Kodi looks only for the names in its folder-art lists
# (advancedsettings ``<musicthumbs>`` and the video equivalent), which hold
# ``folder.jpg`` and not ``folder.png``. It picks the decoder off the bytes,
# so the addon's PNG goes in under the .jpg name and keeps its alpha. The file
# is a copy of the node tree's icon (video.NODE_ROOT_ICON). A folder Kodi has
# already listed shows the icon only on a cold listing.
FOLDER_ICON = "folder.jpg"
FOLDER_ICON_SOURCE = "kofin-node.png"

# A Downloaded-music smart playlist an earlier version wrote; removed when
# the .m3u8 is written (write_downloaded_music_list).
DOWNLOADED_MUSIC_XSP = "Downloaded music.xsp"

# The Downloaded-music view, as a plain playlist of the downloaded songs: their
# rows keep their plugin URLs, so a path rule on the downloads folder matches
# nothing (write_downloaded_music_list). Exempt from the prune like the .xsp, and
# its stem is reserved, so a server playlist of that title takes "(2)" rather
# than the two writing over each other.
DOWNLOADED_MUSIC_M3U8 = "Downloaded music.m3u8"
RESERVED_STEMS = frozenset({os.path.splitext(DOWNLOADED_MUSIC_M3U8)[0].lower()})
OURS = frozenset({DOWNLOADED_MUSIC_XSP, DOWNLOADED_MUSIC_M3U8})


VIDEO_VIEW_TYPES = frozenset({"movies", "tvshows", "musicvideos"})
AUDIO_ITEM_TYPES = frozenset({"Audio"})
VIDEO_ITEM_TYPES = frozenset(
    {"Movie", "Episode", "MusicVideo", "Video", "Trailer", "TvChannel"}
)
VIDEO_MEDIA_TYPES = frozenset({"movie", "episode", "musicvideo"})


# A stop for a server that over-reports ``TotalRecordCount`` and re-emits
# earlier rows on later pages. Paging ends on a short page, so this only bites
# when full pages keep coming; a playlist longer than this is not real.
MAX_PLAYLIST_ITEMS = 20000

# Characters the filesystem or playlist path cannot carry. Keep the server
# name otherwise intact (Unicode allowed).
_UNSAFE = re.compile(r'[/\\<>:"|?*\x00-\x1f]')

# A file name has at most 255 bytes. A playlist's is its stem, " (n)" while
# another playlist has the same title, and ".m3u8.tmp" while it is written.
MAX_STEM_BYTES = 255 - len(" (9999)") - len(".m3u8.tmp")


class Entry(NamedTuple):
    """One playlist line, with what Kodi needs to render it before playback.

    ``path`` is the line the resolver gives; the rest fills the ``#EXTINF``
    header so the file reads correctly on its own (Kodi replaces the label
    from the song row once the list resolves, but a playlist that has to state
    a duration — "Total duration" before anything is queued — has one).
    """

    path: str
    title: str
    artist: str = ""
    track: int = 0
    duration: int = 0


def managed_dir(root: str | None = None) -> str:
    """Absolute path to the managed playlist folder."""
    if root is not None:
        return root
    base = xbmcvfs.translatePath(PLAYLISTS_MUSIC)
    return os.path.join(base, FOLDER_NAME)


def _icon_source() -> str:
    """Absolute path to the shipped icon, or '' when the addon path is unknown.

    Same defensive posture as ``browse._addon_media``: a missing icon costs a
    folder glyph, and must never cost a playlist refresh.
    """
    try:
        path = settings.addon_path()
    except Exception:  # pragma: no cover - defensive
        return ""
    if not path:
        return ""
    return os.path.join(path, "resources", "media", FOLDER_ICON_SOURCE)


def write_folder_icon(directory: str) -> bool:
    """Put :data:`FOLDER_ICON` in a managed folder. True when it was written.

    Skipped when the file is already the right size, because this runs on the
    playlist poll: rewriting it every pass would churn the folder's mtime for
    nothing (see :func:`_write_text`). Size is the cheap proxy for "the same
    icon" — the only way it changes is a new addon version shipping a new one.
    """
    source = _icon_source()
    if not source or not os.path.isfile(source):
        return False
    target = os.path.join(directory, FOLDER_ICON)
    try:
        if os.path.isfile(target) and os.path.getsize(target) == os.path.getsize(
            source
        ):
            return False
        shutil.copyfile(source, target)
    except OSError:
        LOG.exception("failed to write the playlist folder icon to %s", directory)
        return False
    return True


def write_downloaded_music_list(
    entries: Iterable[Entry], root: str | None = None
) -> bool:
    """The Downloaded-music view as a plain playlist of ``entries``. The
    smart playlist goes when this is written; True if the file was written."""
    directory = managed_dir(root)
    try:
        os.makedirs(directory, exist_ok=True)
    except OSError:
        LOG.exception("cannot create the managed playlist folder %s", directory)
        return False
    write_folder_icon(directory)
    stale = os.path.join(directory, DOWNLOADED_MUSIC_XSP)
    if os.path.exists(stale):
        try:
            os.remove(stale)
        except OSError:
            LOG.exception("failed to remove %s", stale)
    return _write_text(
        os.path.join(directory, DOWNLOADED_MUSIC_M3U8), render_m3u8(entries)
    )


def safe_filename(name: str) -> str:
    """File stem from a Jellyfin playlist name (extension added by caller).

    A name the filesystem encoding cannot carry folds to ASCII, as a
    download's does (``downloads/files.sanitize``), before the unsafe
    characters go: the fold makes some of them (``／`` is ``/``).
    """
    cleaned = (name or "").strip()
    try:
        cleaned.encode(sys.getfilesystemencoding() or "utf-8")
    except UnicodeEncodeError:
        cleaned = (
            unicodedata.normalize("NFKD", cleaned)
            .encode("ascii", "ignore")
            .decode("ascii")
            .strip()
        )
    return _UNSAFE.sub("_", cleaned).rstrip(" .") or "playlist"


def _cut(stem: str) -> str:
    """``stem`` cut to MAX_STEM_BYTES where a character ends."""
    cut = stem.encode("utf-8")[:MAX_STEM_BYTES].decode("utf-8", "ignore")
    return cut.rstrip(" .") or "playlist"


def entry_label(entry: Entry) -> str:
    """The ``#EXTINF`` label Kodi writes for a library song: ``NN. Artist - Title``."""
    label = entry.title or ""
    if entry.artist:
        label = "%s - %s" % (entry.artist, label) if label else entry.artist
    if entry.track:
        label = "%02d. %s" % (entry.track, label) if label else "%02d." % entry.track
    return label


def render_m3u8(entries: Iterable[Entry]) -> str:
    """Build extended m3u8 text."""
    lines = ["#EXTM3U"]
    for entry in entries:
        label = entry_label(entry).replace("\n", " ").replace("\r", "")
        lines.append("#EXTINF:%d,%s" % (entry.duration or -1, label))
        lines.append(entry.path)
    lines.append("")
    return "\n".join(lines)


def _unique_stem(name: str, taken: set[str]) -> str:
    base = _cut(safe_filename(name))
    candidate = base
    n = 2
    while candidate.lower() in taken:
        candidate = "%s (%d)" % (base, n)
        n += 1
    taken.add(candidate.lower())
    return candidate


def _stem_matches_title(name: str, filename: str) -> bool:
    """True when ``filename`` is this title, or its ``Title (n)``
    disambiguation, with the title cut as :func:`_unique_stem` cuts it or
    whole: the cut leaves room for a number, and a stored name past it is
    one the filesystem took.

    A membership rewrite keeps that file: recomputing the stem would turn
    ``Title (2).m3u8`` into ``Title.m3u8`` over whoever owns the base name.
    """
    stem = os.path.splitext(filename)[0]
    whole = safe_filename(name)
    return _is_title_stem(stem, whole) or _is_title_stem(stem, _cut(whole))


def _is_title_stem(stem: str, base: str) -> bool:
    if stem == base:
        return True
    prefix = base + " ("
    if not (stem.startswith(prefix) and stem.endswith(")")):
        return False
    number = stem[len(prefix) : -1]
    return number.isdigit() and int(number) >= 2


def assign_playlist_filename(
    name: str, taken: set[str], stored_filename: str | None = None
) -> str:
    """The .m3u8 name to write. Reuses ``stored_filename`` while the title matches.

    ``taken`` holds other names' collisions only; this playlist's stored stem
    must not be in it, or every rewrite mints ``Name (2).m3u8``.
    """
    if stored_filename and _stem_matches_title(name, stored_filename):
        stem = os.path.splitext(stored_filename)[0]
        if stem.lower() not in taken:
            taken.add(stem.lower())
            return stored_filename
    return _unique_stem(name, taken) + ".m3u8"


def _m3u8_stems(directory: str, keep: str | None = None) -> set[str]:
    """Stems already on disk that :func:`_unique_stem` must not reuse.

    ``keep`` is this playlist's current filename, not a collision.
    """
    taken: set[str] = set(RESERVED_STEMS)
    for name in _list_files(directory):
        if not name.endswith(".m3u8"):
            continue
        if keep and name == keep:
            continue
        taken.add(os.path.splitext(name)[0].lower())
    return taken


def enabled_kinds(views: Iterable[Any], whitelist: set[str]) -> set[str]:
    """Audio/Video sides that should materialize, from synced library kinds."""
    kinds: set[str] = set()
    for view in views:
        view_id = getattr(view, "view_id", None) or (
            view.get("Id") if isinstance(view, dict) else None
        )
        media = getattr(view, "media_type", None) or (
            view.get("media_type") if isinstance(view, dict) else None
        )
        if not view_id or view_id not in whitelist:
            continue
        if media == "music":
            kinds.add("Audio")
        elif media in VIDEO_VIEW_TYPES:
            kinds.add("Video")
    return kinds


def playlist_side(media_type: str, items: Iterable[dict[str, Any]]) -> str | None:
    """Audio or Video when the playlist is homogeneous; None to skip (mixed/empty type)."""
    declared = media_type or ""
    if declared not in ("Audio", "Video"):
        return None
    seen: set[str] = set()
    for item in items:
        item_type = item.get("Type") or ""
        if not item_type:
            continue
        if item_type in AUDIO_ITEM_TYPES:
            seen.add("Audio")
        elif item_type in VIDEO_ITEM_TYPES:
            seen.add("Video")
        else:
            seen.add(item_type)
        if len(seen) > 1:
            return None
    if seen and declared not in seen:
        return None
    return declared


def _iter_playlist_items(api: Any, playlist_id: str) -> list[dict[str, Any]]:
    """Every entry of the playlist, in its order: an entry may repeat an item,
    so nothing is deduplicated."""
    return list(
        paged(
            lambda start, limit: api.playlist_items(
                playlist_id, start_index=start, limit=limit
            ),
            PAGE_SIZE,
            dedupe=False,
            cap=MAX_PLAYLIST_ITEMS,
            what="playlist %s" % playlist_id,
        )
    )


def _read_text(path: str) -> str | None:
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except OSError:
        return None


def _write_text(path: str, content: str) -> bool:
    """Write the file unless it already says this. True when it was written.

    A playlist nobody edited must not churn its mtime — skins sort playlist
    folders by date, and a rewrite invalidates Kodi's directory cache.
    """
    if _read_text(path) == content:
        return False

    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    # Atomic-ish: write temp then replace so a crash mid-write leaves the old file.
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    os.replace(tmp, path)
    return True


def _list_files(directory: str) -> list[str]:
    if not os.path.isdir(directory):
        return []
    return [
        name
        for name in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, name))
    ]


def cleanup_managed_playlists(root: str | None = None) -> int:
    """Remove the managed ``Kofin/`` folder (or empty it). Returns files removed.

    The Downloaded-music view survives the sweep (with the folder icon, which
    exists for whatever remains): this cleanup is "stop mirroring the server's
    playlists", and the downloads view mirrors nothing — turning playlist sync
    off must not take the offline library's music view with it.
    """
    directory = managed_dir(root)
    if not os.path.isdir(directory):
        return 0
    names = _list_files(directory)
    keep = {name for name in names if name in OURS}
    if keep:
        keep.add(FOLDER_ICON)
    removed = 0
    for name in names:
        if name in keep:
            continue
        try:
            os.remove(os.path.join(directory, name))
            removed += 1
        except OSError:
            LOG.exception("failed to remove managed playlist %s", name)
    try:
        if not os.listdir(directory):
            os.rmdir(directory)
    except OSError:
        pass
    LOG.debug("music playlists: cleaned %d managed file(s)", removed)
    return removed


def _audio_ids(items: Iterable[dict[str, Any]]) -> list[str]:
    """Keep server order and duplicates; a playlist may repeat one track."""
    return [
        str(item["Id"])
        for item in items
        if item.get("Id") and (not item.get("Type") or item.get("Type") == "Audio")
    ]


def _entries_for(
    items: list[dict[str, Any]],
    side: str,
    resolver: Any = None,
) -> tuple[list[Entry], int]:
    """The lines of one playlist, in the server's order, duplicates kept.

    The ``resolver`` (``entry(item, side) -> Entry | None``) answers for each
    item the pass has filed (backends/api/playlists.py); an item it has not,
    or an item with no id, is counted missing.
    """
    entries: list[Entry] = []
    missing = 0
    for item in items:
        if not item.get("Id") or resolver is None:
            missing += 1
            continue
        entry = resolver.entry(item, side)
        if entry is None:
            missing += 1
            continue
        entries.append(entry)
    return entries, missing


def write_playlist_file(
    directory: str,
    name: str,
    entries: Iterable[Entry],
    taken: set[str],
    stored_filename: str | None = None,
) -> tuple[str, bool]:
    """Write one .m3u8. Returns (filename, written); ValueError for a name
    that is no entry of ``directory``."""
    filename = assign_playlist_filename(name, taken, stored_filename)
    path = fs.entry(directory, filename)
    return filename, _write_text(path, render_m3u8(entries))


def remove_managed_file(directory: str, filename: str) -> bool:
    path = os.path.join(directory, filename)
    if not filename or not os.path.isfile(path):
        return False
    try:
        os.remove(path)
        return True
    except OSError:
        LOG.exception("failed to remove managed playlist %s", filename)
        return False


def _reserved(side: str, filename: str) -> bool:
    """A music playlist file under a generated view's name (RESERVED_STEMS).
    Only a server playlist stored there before the stem was reserved has one,
    and it is moved off it on its next pass even while its Etag holds."""
    return (
        side == "Audio"
        and bool(filename)
        and os.path.splitext(filename)[0].lower() in RESERVED_STEMS
    )


def _remove_stored(
    directory: str, side: str, filename: str, copy: str | None = None
) -> bool:
    """Remove a server playlist's stored file. A reserved name is the view's,
    which the download list writes over it, so it stands unless
    it still holds exactly ``copy``, the playlist's file under its new name:
    then no view was written there and the file is the playlist's alone."""
    if _reserved(side, filename):
        if copy is None or _read_text(os.path.join(directory, filename)) != (
            _read_text(os.path.join(directory, copy))
        ):
            return False
    return remove_managed_file(directory, filename)


class Materialized(NamedTuple):
    """What writing one playlist's file came to."""

    filename: str
    written: bool  # the file on disk changed
    renamed: bool  # the stored file under another name was removed
    entries: int
    missing: int


def _checksum(playlist: dict[str, Any]) -> str:
    etag = playlist.get("Etag") or ""
    return (reference_checksum(etag) or "") if etag else ""


def _on_disk(directory: str, filename: str) -> bool:
    return bool(filename) and os.path.isfile(os.path.join(directory, filename))


def _stands(stored: Any, side: str, checksum: str, directory: str) -> bool:
    """Whether the stored copy is current: the same side, a filename on disk,
    the Etag's checksum, and not a reserved name. An empty checksum never
    stands: it is the mark of a short write, and of a playlist the server
    gave no Etag. A file the state names but disk no longer holds never
    stands either — the Etag does not move when the file is lost, so without
    this a playlist another writer deleted from the folder (a title starting
    with "kofin" once was) would never be written again."""
    return bool(
        stored
        and stored[0] == side
        and stored[1]
        and checksum
        and stored[2] == checksum
        and not _reserved(side, stored[1])
        and _on_disk(directory, stored[1])
    )


def _materialize(
    state: jellyfin_db.JellyfinDatabase,
    playlist: dict[str, Any],
    items: list[dict[str, Any]],
    side: str,
    stored: Any,
    directory: str,
    taken: set[str],
    resolver: Any,
) -> Materialized:
    """Write the playlist's file, keeping its stored name while the title
    matches, and record the state.

    A write the resolver left short (an entry the pass has not filed yet)
    stays dirty: the server's Etag will not move when Kodi files the item,
    so the checksum is withheld and the next pass resolves again.
    """
    entries, missing = _entries_for(items, side, resolver)
    keep = stored[1] if stored and stored[0] == side else None
    filename, written = write_playlist_file(
        directory,
        playlist.get("Name") or "playlist",
        entries,
        taken,
        stored_filename=keep,
    )
    renamed = bool(stored and stored[1] != filename)
    if renamed:
        _remove_stored(directory, stored[0], stored[1], copy=filename)
    state.add_playlist_state(
        playlist.get("Id") or "",
        side,
        filename,
        "" if resolver is not None and missing else _checksum(playlist),
    )
    if missing:
        LOG.debug(
            "playlist %s: %d item(s), %d not in the Kodi library",
            playlist.get("Name"),
            len(entries),
            missing,
        )
    return Materialized(filename, written, renamed, len(entries), missing)


def apply_one(
    api: Any,
    state: jellyfin_db.JellyfinDatabase,
    playlist: dict[str, Any],
    kinds: set[str],
    music_root: str | None = None,
    video_root: str | None = None,
    resolver: Any = None,
) -> bool:
    """Materialize one server playlist. True when a file was written or removed."""
    playlist_id = playlist.get("Id") or ""
    if not playlist_id:
        return False
    items = _iter_playlist_items(api, playlist_id)
    side = playlist_side(playlist.get("MediaType") or "", items)
    stored = state.get_playlist_state(playlist_id)
    if side is None or side not in kinds:
        if stored:
            directory = (
                managed_dir(music_root)
                if stored[0] == "Audio"
                else managed_video_dir() if video_root is None else video_root
            )
            _remove_stored(directory, stored[0], stored[1])
            state.remove_playlist_state(playlist_id)
            return True
        return False

    directory = (
        managed_dir(music_root)
        if side == "Audio"
        else (video_root if video_root is not None else managed_video_dir())
    )
    if _stands(stored, side, _checksum(playlist), directory):
        return False
    if not os.path.isdir(directory):
        os.makedirs(directory)
    write_folder_icon(directory)
    keep = stored[1] if stored and stored[0] == side else None
    taken = _m3u8_stems(directory, keep=keep)
    done = _materialize(
        state, playlist, items, side, stored, directory, taken, resolver
    )
    return done.written or done.renamed


def reconcile(
    api: Any,
    state: jellyfin_db.JellyfinDatabase,
    kinds: set[str],
    music_root: str | None = None,
    video_root: str | None = None,
    resolver: Any = None,
) -> dict[str, int]:
    """Full list + Etag skip + prune for the enabled sides."""
    stats = {"playlists": 0, "written": 0, "tracks": 0, "skipped": 0, "pruned": 0}
    if not kinds:
        return stats

    listed = api.playlists()
    want_audio: set[str] = set()
    want_video: set[str] = set()
    taken_audio: set[str] = set(RESERVED_STEMS)
    taken_video: set[str] = set()

    audio_dir = managed_dir(music_root)
    video_dir = video_root if video_root is not None else managed_video_dir()
    if "Audio" in kinds and not os.path.isdir(audio_dir):
        os.makedirs(audio_dir)
        write_folder_icon(audio_dir)
    if "Video" in kinds and not os.path.isdir(video_dir):
        os.makedirs(video_dir)
        write_folder_icon(video_dir)

    standing_audio = (
        [
            name
            for name in _list_files(audio_dir)
            if name.endswith(".m3u8") and name not in OURS
        ]
        if os.path.isdir(audio_dir)
        else []
    )
    standing_video = (
        [name for name in _list_files(video_dir) if name.endswith(".m3u8")]
        if os.path.isdir(video_dir)
        else []
    )

    if not listed:
        if standing_audio or standing_video:
            LOG.warning(
                "playlists: the server listed none while managed "
                "playlist(s) stand — skipping the prune rather than emptying "
                "the folder"
            )
        return stats

    def keep(prior: Any) -> None:
        """A playlist the pass could not write keeps its file and state."""
        if prior and prior[0] == "Audio":
            want_audio.add(prior[1])
        elif prior and prior[0] == "Video":
            want_video.add(prior[1])

    for playlist in listed:
        playlist_id = playlist.get("Id") or ""
        if not playlist_id:
            continue
        try:
            items = _iter_playlist_items(api, playlist_id)
        except Exception:
            LOG.exception(
                "playlist %s: items listing failed; keeping prior state", playlist_id
            )
            keep(state.get_playlist_state(playlist_id))
            continue
        side = playlist_side(playlist.get("MediaType") or "", items)
        if side is None or side not in kinds:
            continue
        stored = state.get_playlist_state(playlist_id)
        directory = audio_dir if side == "Audio" else video_dir
        taken = taken_audio if side == "Audio" else taken_video
        want = want_audio if side == "Audio" else want_video
        if stored is not None and _stands(stored, side, _checksum(playlist), directory):
            want.add(stored[1])
            taken.add(os.path.splitext(stored[1])[0].lower())
            stats["playlists"] += 1
            continue
        try:
            done = _materialize(
                state, playlist, items, side, stored, directory, taken, resolver
            )
        except Exception:
            LOG.exception("playlist %s: not written; keeping prior state", playlist_id)
            keep(stored)
            continue
        stats["tracks"] += done.entries
        stats["skipped"] += done.missing
        if done.renamed:
            stats["pruned"] += 1
        want.add(done.filename)
        stats["playlists"] += 1
        if done.written:
            stats["written"] += 1

    _prune(state, kinds, audio_dir, video_dir, want_audio, want_video, stats)
    LOG.debug(
        "playlists: %d playlist(s), %d rewritten, %d track(s), "
        "%d skipped, %d pruned",
        stats["playlists"],
        stats["written"],
        stats["tracks"],
        stats["skipped"],
        stats["pruned"],
    )
    return stats


def _prune(
    state: jellyfin_db.JellyfinDatabase,
    kinds: set[str],
    audio_dir: str,
    video_dir: str,
    want_audio: set[str],
    want_video: set[str],
    stats: dict[str, int],
) -> None:
    """Remove what the listing no longer names: the stored states of the
    enabled sides first, then every managed file the pass did not write."""
    known = {row[0]: row for row in state.get_playlist_states()}
    for playlist_id, media_type, filename, _checksum in list(known.values()):
        if media_type == "Audio" and "Audio" in kinds and filename not in want_audio:
            _remove_stored(audio_dir, "Audio", filename)
            state.remove_playlist_state(playlist_id)
            stats["pruned"] += 1
        elif media_type == "Video" and "Video" in kinds and filename not in want_video:
            remove_managed_file(video_dir, filename)
            state.remove_playlist_state(playlist_id)
            stats["pruned"] += 1

    if "Audio" in kinds:
        for existing in _list_files(audio_dir):
            if existing.endswith(".tmp"):
                try:
                    os.remove(os.path.join(audio_dir, existing))
                except OSError:
                    pass
                continue
            if existing == FOLDER_ICON or existing in OURS:
                continue
            if existing.endswith(".m3u8") and existing not in want_audio:
                try:
                    os.remove(os.path.join(audio_dir, existing))
                    stats["pruned"] += 1
                except OSError:
                    LOG.exception("failed to prune managed playlist %s", existing)
    if "Video" in kinds:
        for existing in _list_files(video_dir):
            if existing.endswith(".m3u8") and existing not in want_video:
                try:
                    os.remove(os.path.join(video_dir, existing))
                    stats["pruned"] += 1
                except OSError:
                    LOG.exception("failed to prune managed playlist %s", existing)


def cleanup_video_playlists(root: str | None = None) -> int:
    """Remove managed Jellyfin video .m3u8 files from the video Kofin folder.

    Library smart playlists (.xsp) and the folder icon stay.
    """
    directory = root if root is not None else managed_video_dir()
    if not os.path.isdir(directory):
        return 0
    removed = 0
    for name in _list_files(directory):
        if not name.endswith(".m3u8"):
            continue
        try:
            os.remove(os.path.join(directory, name))
            removed += 1
        except OSError:
            LOG.exception("failed to remove managed video playlist %s", name)
    return removed


def parse_m3u_paths(text: str) -> list[str]:
    """Ordered file lines from an extended m3u, comments skipped."""
    paths: list[str] = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        paths.append(line)
    return paths


# --- the video smart playlists -------------------------------------------------
#
# One .xsp per synced video library, in a managed folder under Kodi's own
# video playlists, written whole every pass. Only the folder icon can carry
# the addon's art (a .tbn beside an .xsp does nothing). Ownership differs from
# the music side above: here the ``kofin`` prefix gates every .xsp deletion,
# and a foreign file other than an ``.m3u8`` is spared.

PLAYLIST_KINDS = ("movies", "tvshows", "musicvideos")


def video_playlists_dir() -> str:
    """Kodi's own video playlist directory -- the user's, not ours."""
    return xbmcvfs.translatePath("special://profile/playlists/video")


def managed_video_dir() -> str:
    """The managed folder inside it -- ours."""
    return os.path.join(video_playlists_dir(), FOLDER_NAME)


def video_playlist_file(view: dict[str, Any]) -> str:
    return "%s%s%s.xsp" % (fs.PREFIX, view["Media"], view["Id"])


def build_video_playlist(view: dict[str, Any], mixed: bool = False) -> etree.Element:
    xml = etree.Element("smartplaylist", {"type": view["Media"]})
    etree.SubElement(xml, "name").text = (
        view["Name"] if not mixed else "%s (%s)" % (view["Name"], view["Media"])
    )
    etree.SubElement(xml, "match").text = "all"
    video.path_rule(xml, view["Path"])
    return xml


def write_video_playlists(entries: Iterable[Any]) -> None:
    """One playlist per video-kind entry; the folder, its icon, and a
    reconcile of whatever else kofin left in there."""
    directory = managed_video_dir()

    if not os.path.isdir(directory):
        os.makedirs(directory)

    write_folder_icon(directory)
    keep = set()

    for view, mixed in entries:
        if view["Media"] not in PLAYLIST_KINDS:
            continue
        name = video_playlist_file(view)
        etree.ElementTree(build_video_playlist(view, mixed)).write(
            fs.entry(directory, name)
        )
        keep.add(name)

    # The ``.m3u8`` files in this folder are the Jellyfin video playlists,
    # owned by the materializer (reconcile/_prune) — not ours to prune here,
    # even one whose title starts with "kofin" and so carries the deletion
    # prefix. Only the smart playlists (.xsp) are this writer's.
    keep.update(name for name in fs.listdir(directory)[1] if name.endswith(".m3u8"))

    for name in fs.remove_managed_entries(directory, keep=keep, label="playlist"):
        LOG.debug("--[ playlists ] pruned stale %s", name)


def remove_video_playlists() -> None:
    """Remove every generated playlist, the managed folder with them.

    The generated files and the folder's own icon go, the folder once it is
    empty; anything else in there is not ours to remove.
    """
    directory = managed_video_dir()
    fs.remove_managed_entries(directory, also=(FOLDER_ICON,), label="playlist")
    fs.remove_empty(directory)
