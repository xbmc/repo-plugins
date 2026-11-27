"""A library's album directories as an ordered run of rows to list.

Two listings are made of them. The library's music root names every one,
for a walk Kodi makes on its own account. A scan the pass asks for visits
the ones it names and no others, a part at a time (``paths.MUSIC_PART``),
in the same order under the same labels.
"""

from typing import TYPE_CHECKING, Any, Optional
from collections.abc import Iterable

from . import metadata, paths

if TYPE_CHECKING:
    from .store import Store


def root_folders(store: "Store", library: str) -> set[str]:
    """Every directory the library's root lists: one with a live song, and
    one that still has songs to shed. A tombstone leaves Kodi only through
    the complete listing of its directory, so a directory whose songs are
    all gone stays listed, empty, until a scan has confirmed it."""
    folders = set(store.folders("Audio", library))
    folders.update(
        placed.parent_id
        for placed in store.tombstones().values()
        if placed.kind == "Audio" and placed.library == library and placed.parent_id
    )
    return folders


def rows(
    store: "Store",
    library: str,
    folders: Optional[Iterable[str]] = None,
    albums: Optional[dict[str, dict[str, Any]]] = None,
) -> list[tuple[str, str]]:
    """(folder, label) in label order, for ``folders`` or for the whole root.

    Kodi walks a listing's folders in label order and numbers albums as it
    adds them, so the label is the album's creation date on the server
    (``metadata.folder_label``). ``albums`` is the library's album payloads
    when the caller already holds them.
    """
    wanted = set(folders) if folders is not None else root_folders(store, library)
    if not wanted:
        return []
    if albums is None:
        albums = {
            item_id: record.item
            for item_id, record in store.records(
                kind="MusicAlbum", library=library
            ).items()
        }
    salts = store.salts()
    return sorted(
        (
            (
                folder,
                metadata.folder_label(albums.get(folder), folder, salts.get(folder, 0)),
            )
            for folder in wanted
        ),
        key=lambda row: (row[1], row[0]),
    )


def parts(count: int) -> int:
    """How many parts a plan of ``count`` directories is listed in."""
    return -(-count // paths.MUSIC_PART)
