"""Private desired/applied state for API operations.

confirm() follows a readback of the owned item, never an accepted request.
Failed and superseded work cannot advance applied. Namespaces include server
and user identity; no native IDs are adopted here.
"""

import json
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Optional

from kofin.sync.private import Database
from kofin.sync.model import MediaItem


class BackendMismatch(Exception):
    """A branch switch requires a fresh native library and cleared mappings."""


class EarlierLibrary(BackendMismatch):
    """What the SQL build left, in ``kofin.db`` or in Kodi's library. This
    build adopts none of it, and the way out is the same from all of it: the
    Library status button gives the instructions (``status.show``)."""


def claim_backend(cursor: sqlite3.Cursor, backend: str) -> None:
    if backend not in ("sql", "api"):
        raise ValueError("unknown backend")
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS backend_state (id INTEGER PRIMARY KEY CHECK(id=1), backend TEXT NOT NULL, version INTEGER NOT NULL)"
    )
    row = cursor.execute(
        "SELECT backend, version FROM backend_state WHERE id=1"
    ).fetchone()
    if row is not None:
        if row != (backend, 1):
            raise EarlierLibrary(
                "sync state belongs to another backend/version; start with fresh sync state"
            )
        return
    # A profile the SQL build filed has rows in its mapping table and no
    # marker. Generic private reads remain available; only an adapter claiming
    # these mappings is refused. The table may stand empty (0.9x profiles
    # created it); only rows make it a claim.
    table = cursor.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'jellyfin'"
    ).fetchone()
    legacy = table and cursor.execute("SELECT 1 FROM jellyfin LIMIT 1").fetchone()
    if legacy and backend != "sql":
        raise EarlierLibrary("legacy SQL mappings require a fresh library")
    cursor.execute("INSERT INTO backend_state VALUES (1, ?, 1)", (backend,))


@dataclass(frozen=True)
class ItemState:
    desired: int
    applied: int
    operation: str
    status: str
    error: str


# A TEMP table marks a connection that has run the schema; it goes with the
# connection, so the DDL runs once per connection and never per call.
SCHEMA_READY = "api_schema_ready"


def schema_ready(cursor: sqlite3.Cursor) -> bool:
    return (
        cursor.execute(
            "SELECT 1 FROM sqlite_temp_master WHERE type = 'table' AND name = ?",
            (SCHEMA_READY,),
        ).fetchone()
        is not None
    )


class Catalogue:
    def __init__(self, namespace: str):
        if not namespace:
            raise ValueError("server/user namespace is required")
        self.namespace = namespace

    @classmethod
    def _prepare(cls, cursor: sqlite3.Cursor) -> None:
        """The backend's claim and its tables, once per connection."""
        if schema_ready(cursor):
            return
        cls._create(cursor)
        cursor.execute("CREATE TEMP TABLE %s(x)" % SCHEMA_READY)

    @classmethod
    def _create(cls, cursor: sqlite3.Cursor) -> None:
        claim_backend(cursor, "api")
        cursor.execute("""CREATE TABLE IF NOT EXISTS api_item(
            namespace TEXT NOT NULL, item_id TEXT NOT NULL, kind TEXT NOT NULL,
            payload TEXT NOT NULL, desired INTEGER NOT NULL, applied INTEGER NOT NULL,
            operation TEXT NOT NULL, status TEXT NOT NULL, error TEXT NOT NULL,
            PRIMARY KEY(namespace, item_id))""")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS api_item_status ON api_item(namespace, status)"
        )

    def stage(self, item: MediaItem, operation: str = "upsert") -> int:
        with Database() as db:
            self._prepare(db.cursor)
            return self.stage_in(db.cursor, item, operation)

    def stage_in(
        self, cursor: sqlite3.Cursor, item: MediaItem, operation: str = "upsert"
    ) -> int:
        """Stage within the publisher's transaction, including its snapshot."""
        if operation not in ("upsert", "remove"):
            raise ValueError("unknown operation")
        payload = json.dumps(item.payload, sort_keys=True, separators=(",", ":"))
        row = cursor.execute(
            "SELECT payload, desired, applied, operation FROM api_item WHERE namespace=? AND item_id=?",
            (self.namespace, item.item_id),
        ).fetchone()
        if row and row[0] == payload and row[3] == operation:
            return int(row[1])
        generation = int(row[1]) + 1 if row else 1
        applied = int(row[2]) if row else 0
        cursor.execute(
            """INSERT OR REPLACE INTO api_item VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', '')""",
            (
                self.namespace,
                item.item_id,
                item.kind,
                payload,
                generation,
                applied,
                operation,
            ),
        )
        return generation

    def state(self, item_id: str) -> Optional[ItemState]:
        with Database() as db:
            self._prepare(db.cursor)
            row = db.cursor.execute(
                "SELECT desired, applied, operation, status, error FROM api_item WHERE namespace=? AND item_id=?",
                (self.namespace, item_id),
            ).fetchone()
            return ItemState(*row) if row else None

    def confirm(self, item_id: str, generation: int) -> bool:
        """Acknowledge readback for exactly the current desired generation."""
        with Database() as db:
            self._prepare(db.cursor)
            db.cursor.execute(
                """UPDATE api_item SET applied=desired, status='applied', error=''
                WHERE namespace=? AND item_id=? AND desired=?""",
                (self.namespace, item_id, generation),
            )
            return bool(db.cursor.rowcount)

    def failed(self, item_id: str, generation: int, reason: str) -> None:
        self.failed_many([(item_id, generation, reason)])

    def failed_many(self, rows: Iterable[tuple[str, int, str]]) -> None:
        """One transaction for a batch of failures: a pass whose scanner
        imported nothing fails every row."""
        rows = list(rows)
        if not rows:
            return
        with Database() as db:
            self._prepare(db.cursor)
            db.cursor.executemany(
                """UPDATE api_item SET status='pending', error=?
                WHERE namespace=? AND item_id=? AND desired=?""",
                [
                    (reason, self.namespace, item_id, generation)
                    for item_id, generation, reason in rows
                ],
            )

    def has_pending(self) -> bool:
        """Whether any work is pending, without loading a payload: the tick
        asks this twice a second."""
        with Database() as db:
            self._prepare(db.cursor)
            return bool(
                db.cursor.execute(
                    "SELECT 1 FROM api_item WHERE namespace=? AND status='pending' LIMIT 1",
                    (self.namespace,),
                ).fetchone()
            )

    def pending_signature(self) -> tuple[int, int]:
        """What is pending, as a pair that moves whenever anything is
        published: the number of pending rows and the sum of their
        generations."""
        with Database() as db:
            self._prepare(db.cursor)
            count, generations = db.cursor.execute(
                "SELECT COUNT(*), COALESCE(SUM(desired), 0) FROM api_item"
                " WHERE namespace=? AND status='pending'",
                (self.namespace,),
            ).fetchone()
        return int(count), int(generations)

    def pending(self) -> list[tuple[MediaItem, int, str]]:
        """Replayable desired DTOs and tombstones, ordered deterministically."""
        with Database() as db:
            self._prepare(db.cursor)
            rows = db.cursor.execute(
                "SELECT payload, desired, operation FROM api_item WHERE namespace=? AND status='pending' ORDER BY item_id",
                (self.namespace,),
            ).fetchall()
        return [
            (MediaItem.from_dto(json.loads(payload)), generation, operation)
            for payload, generation, operation in rows
        ]
