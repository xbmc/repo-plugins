"""Accessors for kofin.db's library and playlist tables.

``view`` holds the libraries the viewer can select, by id, name and media
type; ``playlist_state`` the managed playlist files, by playlist id, side,
filename and checksum. Everything outside the pipeline's own ``api_*``
tables reads and writes the two through here, inside a block the caller
owns.
"""

import functools
import sqlite3
from collections import namedtuple
from typing import Any, NamedTuple, Optional

from kofin.core.log import Logger

LOG = Logger(__name__)


class View(NamedTuple):
    """A row of the view table: a server library as the sync lists it."""

    view_id: str
    name: str
    media_type: str


@functools.lru_cache(maxsize=64)
def _row_class(fields: tuple[str, ...]) -> type[tuple[Any, ...]]:
    """One namedtuple class per distinct column list.

    sqlite3 calls the row factory once per row, and ``namedtuple()`` builds a
    class, far too costly to repeat per row. Keyed on the exact column names
    so two queries never share a class by accident; 64 covers every SELECT
    here.
    """
    return namedtuple("Row", fields)


def sqlite_namedtuple_factory(
    cursor: sqlite3.Cursor, row: tuple[Any, ...]
) -> tuple[Any, ...]:
    return _row_class(tuple(col[0] for col in cursor.description))(*row)


class JellyfinDatabase:

    def __init__(self, cursor: sqlite3.Cursor) -> None:
        self.cursor = cursor
        cursor.row_factory = sqlite_namedtuple_factory

    # -- playlist_state --------------------------------------------------------

    def get_playlist_state(self, jellyfin_id: str) -> Optional[tuple[Any, ...]]:
        """(media_type, filename, checksum) or None."""
        self.cursor.execute(
            "SELECT media_type, filename, checksum FROM playlist_state"
            " WHERE jellyfin_id = ?",
            (jellyfin_id,),
        )
        row: Optional[tuple[Any, ...]] = self.cursor.fetchone()
        return row

    def get_playlist_states(self) -> list[tuple[Any, ...]]:
        self.cursor.execute(
            "SELECT jellyfin_id, media_type, filename, checksum FROM playlist_state"
        )
        rows: list[tuple[Any, ...]] = self.cursor.fetchall()
        return rows

    def add_playlist_state(
        self, jellyfin_id: str, media_type: str, filename: str, checksum: str
    ) -> None:
        self.cursor.execute(
            "INSERT OR REPLACE INTO playlist_state"
            "(jellyfin_id, media_type, filename, checksum) VALUES (?, ?, ?, ?)",
            (jellyfin_id, media_type, filename, checksum),
        )

    def remove_playlist_state(self, jellyfin_id: str) -> None:
        self.cursor.execute(
            "DELETE FROM playlist_state WHERE jellyfin_id = ?", (jellyfin_id,)
        )

    def remove_playlist_states(self) -> None:
        self.cursor.execute("DELETE FROM playlist_state")

    def playlist_filename(self, jellyfin_id: str) -> Optional[str]:
        """The managed file's name, '' for a state without one, None for none."""
        self.cursor.execute(
            "SELECT filename FROM playlist_state WHERE jellyfin_id = ?", (jellyfin_id,)
        )
        row = self.cursor.fetchone()
        return None if row is None else str(row[0] or "")

    def playlist_for_file(self, filename: str, side: Optional[str] = None) -> str:
        """The playlist id a managed file belongs to, '' for none; ``side``
        narrows to one of Audio and Video."""
        if side is None:
            self.cursor.execute(
                "SELECT jellyfin_id FROM playlist_state WHERE filename = ?", (filename,)
            )
        else:
            self.cursor.execute(
                "SELECT jellyfin_id FROM playlist_state"
                " WHERE media_type = ? AND filename = ?",
                (side, filename),
            )
        row = self.cursor.fetchone()
        return str(row[0]) if row else ""

    # -- view ------------------------------------------------------------------

    def get_view(self, view_id: str) -> Optional[View]:
        try:
            self.cursor.execute("SELECT * FROM view WHERE view_id = ?", (view_id,))
            row = self.cursor.fetchone()
        except TypeError:
            return None
        return View(*row) if row else None

    def views(self) -> list[Any]:
        """Every library row, as ``View`` tuples."""
        self.cursor.execute("SELECT view_id, view_name, media_type FROM view")
        return [View(*row) for row in self.cursor.fetchall()]

    def view_names(self) -> dict[str, str]:
        self.cursor.execute("SELECT view_id, view_name FROM view")
        return {row[0]: row[1] for row in self.cursor.fetchall()}

    def view_name(self, view_id: str) -> Optional[str]:
        """The library's name, '' for a row without one, None for no row."""
        self.cursor.execute("SELECT view_name FROM view WHERE view_id = ?", (view_id,))
        row = self.cursor.fetchone()
        return None if row is None else str(row[0] or "")

    def view_media(self, view_id: str) -> str:
        """The library's media type, '' for no row."""
        self.cursor.execute("SELECT media_type FROM view WHERE view_id = ?", (view_id,))
        row = self.cursor.fetchone()
        return str(row[0] or "") if row else ""

    def remember_view(self, view_id: str, name: str, media_type: str) -> None:
        self.cursor.execute(
            "INSERT OR REPLACE INTO view VALUES (?,?,?)", (view_id, name, media_type)
        )
