"""Lookups between Kodi ids and Jellyfin ids.

These serve the play route, the userdata watcher and the Jellyfin actions
menu, not the reconciler: a cache hit still needs ownership verification, and
browsing needs no hit.
"""

from typing import Any, Optional

from kofin.core.settings import Credentials

from . import paths
from .kinds import CONTAINERS, FILED, KINDS, MEDIA, rpc
from .paths import ASCII_SPACE
from .store import Store, namespace

# Kinds whose rows carry no id of ours, found through what the row holds.
FOUND = ("Season", "BoxSet", "MusicAlbum", "MusicArtist")


def current_store() -> Store:
    creds = Credentials.load()
    return Store(namespace(creds.server_id, creds.user_id))


def owner_store() -> Optional[Store]:
    """The store of whichever account the catalogue was filed for, or None
    while nothing has been filed: the report logged out reads it."""
    owner = Store.owner()
    return Store(owner) if owner else None


def mapped_item(kodi_id: int, media: str) -> Optional[str]:
    """The item id behind an owned native row, or None for anything else."""
    kind = MEDIA.get(media) or CONTAINERS.get(media)
    if kind is None:
        return None
    return _mapped(current_store(), kind, kodi_id)


def _details(
    kind: str, kodi_id: int, properties: list[str]
) -> Optional[dict[str, Any]]:
    """Kodi's row, or None when it has no such row."""
    table = KINDS[kind]
    try:
        reply: dict[str, Any] = rpc(
            table.getter, {table.id_param: kodi_id, "properties": properties}
        )
    except RuntimeError:
        return None
    row: dict[str, Any] = reply.get(table.result_key, {})
    return row


def _mapped(store: Store, kind: str, kodi_id: int) -> Optional[str]:
    if kind in FOUND:
        return _found(store, kind, kodi_id)
    properties = ["file", "uniqueid"] if kind in FILED else ["file"]
    row = _details(kind, kodi_id, properties)
    if row is None:
        # No such row for that media type: not ours, whatever it is.
        return None
    if kind == "Audio":
        # A song has no unique id; the URL it is filed under is its identity.
        location, item_id = paths.parse_item(row.get("file") or "")
        if location is None or location.key != store.namespace or not item_id:
            return None
        placed = store.entry(item_id)
        if placed is None or store.mapping(item_id) is None:
            return None
        if location.library != placed.library or location.folder != placed.parent_id:
            return None
        return item_id
    uid = (row.get("uniqueid") or {}).get("kofin", "")
    prefix = store.namespace + ":"
    if not uid.startswith(prefix):
        return None
    item_id = uid[len(prefix) :]
    placed = store.entry(item_id)
    if placed is None or store.mapping(item_id) is None:
        return None
    if kind == "Series":
        # A show is filed as its folder (Readback.owns).
        filed = (row.get("file") or "").rstrip("/") == paths.show_dir(
            store.namespace, placed.library, item_id
        ).rstrip("/")
    else:
        filed = row.get("file") == paths.playback_url(
            store.namespace, kind, placed.library, item_id, placed.parent_id
        )
    return item_id if filed else None


def _found(store: Store, kind: str, kodi_id: int) -> Optional[str]:
    """The item a season, set, album or artist row stands for.

    A season is found the way the pass finds its row (patch.Applier.row_for):
    by its show and number. A set, an album or an artist is one the pass
    acknowledged against the row, so a collection applied without a row never
    stands for a set of the same title. Kodi keeps one row for several of
    ours (one set per title, an album it merged, one artist per name), and
    the first by id stands for it, as it owns an album's or an artist's art
    in the pass (album_owner, artist_owner).
    """
    if kind == "Season":
        row = _details(kind, kodi_id, ["season", "tvshowid"])
        tvshowid = row.get("tvshowid") if row else None
        show = _mapped(store, "Series", tvshowid) if isinstance(tvshowid, int) else None
        if show is None or row is None:
            return None
        numbered = sorted(
            item_id
            for item_id, record in store.records(kind=kind, parent_id=show).items()
            if record.item.get("IndexNumber") is not None
            and int(record.item["IndexNumber"]) == row.get("season")
        )
        return numbered[0] if numbered else None
    candidates = store.mapped_to(kind, kodi_id)
    live = store.known(candidates)
    if kind == "MusicAlbum":
        # Kodi titles an album from its songs' tags, not from the album: the
        # acknowledgement alone says whose row it is.
        owned = [item_id for item_id in candidates if item_id in live]
        return owned[0] if owned else None
    row = _details(kind, kodi_id, ["title"] if kind == "BoxSet" else [])
    if not row:
        return None
    if kind == "BoxSet":
        title = row.get("title")
        named = [
            item_id
            for item_id, item in store.payloads(candidates).items()
            if (item.get("Name") or "").strip(ASCII_SPACE) == title
        ]
    else:
        from .readback import artist_key

        name = artist_key(row.get("artist") or row.get("label"))
        named = [
            item_id
            for item_id, item in store.payloads(candidates).items()
            if artist_key(item.get("Name")) == name
        ]
    named = sorted(item_id for item_id in named if item_id in live)
    return named[0] if named else None


def native_id_for(item_id: str, media: str = "movie") -> Optional[int]:
    """The Kodi id of an imported item, verified; None when it has no row."""
    store = current_store()
    mapping = store.mapping(item_id)
    if not mapping or mapping.kodi_id is None:
        return None
    try:
        if mapped_item(mapping.kodi_id, media) == item_id:
            return mapping.kodi_id
    except RuntimeError:
        pass
    placed = store.entry(item_id)
    kind = MEDIA.get(media)
    if placed is None or kind is None:
        return None
    from .readback import Readback

    readback = Readback(store.namespace)
    if kind == "Audio":
        # One directory: a lookup must not page the whole song library.
        found = readback.directory(placed.library, placed.parent_id)
    else:
        found = readback.scope(kind, placed.library, placed.parent_id)
    row = found.get(item_id)
    if not row:
        return None
    kodi_id: int = row[KINDS[kind].id_param]
    return kodi_id


def library_url(item_id: str) -> Optional[str]:
    """The resolver URL of an imported item, or None when it has no row."""
    store = current_store()
    mapping = store.mapping(item_id)
    placed = store.entry(item_id)
    if not mapping or mapping.kodi_id is None or placed is None:
        return None
    if placed.kind in ("MusicAlbum", "MusicArtist"):
        return None
    container = ""
    if placed.kind == "Audio":
        container = paths.container_of(store.item(item_id) or {})
    return paths.playback_url(
        store.namespace,
        placed.kind,
        placed.library,
        item_id,
        placed.parent_id,
        container,
    )
