"""Jellyfin playlists as Kodi playlist files, resolved through the catalogue.

An entry is an item the pass has acknowledged, its line the resolver URL Kodi
filed the row under (a song's file in its album directory, a video's query
URL) and its label the server's own playlist listing. Order and duplicates
are the server's; the managed folders, the file naming, the state tables and
the prune rules are the shared module's (sync/playlists.py).
"""

import re
from typing import TYPE_CHECKING, Any, Optional
from collections.abc import Iterable

from kofin.core.log import Logger
from kofin.sync import dynamic, kofindb, playlists, private
from . import paths
from .store import Store

if TYPE_CHECKING:
    from kofin.core.api import Api

LOG = Logger(__name__)

VIDEO_KINDS = ("Movie", "Episode", "MusicVideo")
# The one switch for the generated presentation, the node tree included.
SETTING = dynamic.SETTING


class Resolver:
    def __init__(self, store: Store):
        self.store = store
        self.key = store.namespace

    def entry(self, item: dict[str, Any], side: str) -> Optional[playlists.Entry]:
        """The line for one playlist item, or None when Kodi has no row of it:
        an item outside the selection, or one the pass has not filed yet."""
        item_id = str(item.get("Id") or "")
        entry = self.store.entry(item_id) if item_id else None
        if entry is None:
            return None
        if side == "Audio" and entry.kind != "Audio":
            return None
        if side == "Video" and entry.kind not in VIDEO_KINDS:
            return None
        mapping = self.store.mapping(item_id)
        if mapping is None or mapping.kodi_id is None:
            return None
        if side == "Audio":
            payload = self.store.item(item_id) or {}
            return song_entry(self.key, entry, payload, item)
        return playlists.Entry(
            path=paths.playback_url(
                self.key, entry.kind, entry.library, item_id, entry.parent_id
            ),
            title=str(item.get("Name") or ""),
        )


def items_of_lines(store: Store, lines: Iterable[str]) -> list[tuple[str, str]]:
    """The item id and side ("Audio" or "Video") of each line of a Kodi
    playlist file, ("", "") for a line this build did not file. A line is the
    URL Kodi filed the row under, as Resolver.entry writes one, and carries the
    id (paths.parse_item); a library path names the row, whose owner the
    readback finds. The catalogue says what the item is."""
    from .identity import mapped_item

    found: list[tuple[str, str]] = []
    for line in lines:
        library = re.match(r"(videodb://movies/titles|musicdb://songs)/(\d+)", line)
        if library:
            media = "movie" if library.group(1).startswith("videodb") else "song"
            item_id = mapped_item(int(library.group(2)), media) or ""
        else:
            _, item_id = paths.parse_item(line)
        entry = store.entry(item_id) if item_id else None
        if entry is not None and entry.kind == "Audio":
            found.append((item_id, "Audio"))
        elif entry is not None and entry.kind in VIDEO_KINDS:
            found.append((item_id, "Video"))
        else:
            found.append(("", ""))
    return found


def song_entry(
    key: str, entry: Any, payload: dict[str, Any], item: dict[str, Any]
) -> playlists.Entry:
    """A song's line: its file in its album directory, labelled from ``item``
    (a server playlist's listing of it, or its payload)."""
    return playlists.Entry(
        path=paths.playback_url(
            key,
            "Audio",
            entry.library,
            entry.item_id,
            entry.parent_id,
            paths.container_of(payload),
        ),
        title=str(item.get("Name") or payload.get("Name") or ""),
        artist=" / ".join(str(a) for a in (item.get("Artists") or [])),
        track=int(item.get("IndexNumber") or 0) & 0xFFFF,
        duration=int((item.get("RunTimeTicks") or 0) // 10_000_000),
    )


def write_downloaded_music(store: Store, root: Optional[str] = None) -> bool:
    """The Downloaded-music view: a playlist of the finished song downloads
    the catalogue places, in album artist, album, disc and track order. A
    download keeps its row's plugin URL, so the view is read from the
    download store, the catalogue's entries and payloads read once each
    however many songs there are."""
    from kofin.downloads import store as downloads

    done = [
        row.jellyfin_id
        for row in downloads.rows(downloads.DONE)
        if row.media_type == "song"
    ]
    entries = store.entries(kind="Audio") if done else {}
    placed = [item_id for item_id in done if item_id in entries]
    payloads = store.payloads(placed)

    def order(item_id: str) -> tuple[str, str, int, int, str]:
        payload = payloads.get(item_id) or {}
        credits = [
            str(a.get("Name") or "")
            for a in payload.get("AlbumArtists") or []
            if isinstance(a, dict)
        ]
        return (
            (" / ".join(credits) or str(payload.get("AlbumArtist") or "")).lower(),
            str(payload.get("Album") or "").lower(),
            int(payload.get("ParentIndexNumber") or 0),
            int(payload.get("IndexNumber") or 0),
            str(payload.get("Name") or "").lower(),
        )

    lines = [
        song_entry(
            store.namespace, entries[item_id], payloads[item_id], payloads[item_id]
        )
        for item_id in sorted((i for i in placed if i in payloads), key=order)
    ]
    return playlists.write_downloaded_music_list(lines, root)


def wanted() -> Optional[bool]:
    return dynamic.wanted()


def enabled_kinds() -> set[str]:
    """Audio and Video sides, from the kinds of the synced libraries."""
    whitelist = {
        x.replace("Mixed:", "") for x in (private.get_sync().get("Whitelist") or [])
    }
    with private.Database() as db:
        views = [
            {"Id": view.view_id, "media_type": view.media_type}
            for view in kofindb.JellyfinDatabase(db.cursor).views()
        ]
    return playlists.enabled_kinds(views, whitelist)


def _drop_side(side: str, state: kofindb.JellyfinDatabase, root: Optional[str]) -> int:
    """The managed files and the states of a side whose last library left
    the selection, the way the whole feature's go when it is turned off."""
    stale = [row for row in state.get_playlist_states() if row[1] == side]
    if not stale:
        return 0
    if side == "Audio":
        removed = playlists.cleanup_managed_playlists(root)
    else:
        removed = playlists.cleanup_video_playlists(root)
    for row in stale:
        state.remove_playlist_state(row[0])
    LOG.debug("%s playlists pruned: no synced library left (%d files)", side, removed)
    return removed


def reconcile(
    api: "Api",
    store: Store,
    music_root: Optional[str] = None,
    video_root: Optional[str] = None,
) -> Optional[dict[str, int]]:
    """Every server playlist of the enabled sides, written and pruned; a
    side with no synced library left loses its files and states, and with
    the switch off both sides do. None while the switch cannot be read."""
    nodes = wanted()
    if nodes is None:
        return None
    if not nodes:
        removed = cleanup(music_root, video_root)
        return {"pruned": removed} if removed else {}
    kinds = enabled_kinds()
    with private.Database() as db:
        state = kofindb.JellyfinDatabase(db.cursor)
        pruned = 0
        if "Audio" not in kinds:
            pruned += _drop_side("Audio", state, music_root)
        if "Video" not in kinds:
            pruned += _drop_side("Video", state, video_root)
        if not kinds:
            return {"pruned": pruned} if pruned else {}
        return playlists.reconcile(
            api,
            kofindb.JellyfinDatabase(db.cursor),
            kinds,
            music_root=music_root,
            video_root=video_root,
            resolver=Resolver(store),
        )


def apply(
    api: "Api",
    store: Store,
    playlist_id: str,
    music_root: Optional[str] = None,
    video_root: Optional[str] = None,
) -> Optional[bool]:
    """One server playlist, written or pruned; None while the switch cannot
    be read."""
    nodes = wanted()
    if nodes is None:
        return None
    if not nodes or not playlist_id:
        return False
    kinds = enabled_kinds()
    if not kinds:
        return False
    item = api.item(playlist_id)
    if not isinstance(item, dict) or not item.get("Id"):
        return False
    with private.Database() as db:
        return playlists.apply_one(
            api,
            kofindb.JellyfinDatabase(db.cursor),
            item,
            kinds,
            music_root=music_root,
            video_root=video_root,
            resolver=Resolver(store),
        )


def owed() -> bool:
    """Whether the switch reads off while the state still records
    playlists, which only the playlists pass takes down."""
    if wanted() is not False:
        return False
    with private.Database() as db:
        return bool(kofindb.JellyfinDatabase(db.cursor).get_playlist_states())


def cleanup(music_root: Optional[str] = None, video_root: Optional[str] = None) -> int:
    """The managed playlists go, both sides, and the state with them; the
    number of files removed."""
    removed = playlists.cleanup_managed_playlists(music_root)
    removed += playlists.cleanup_video_playlists(video_root)
    with private.Database() as db:
        kofindb.JellyfinDatabase(db.cursor).remove_playlist_states()
    return removed
