"""Atomic publication and recovery state for every native kind, in Kofin's
database only.

Three facts, stored once each. ``api_item`` (the shared catalogue table)
holds one payload per item and its desired/applied generations.
``api_entry`` holds membership as intervals: a row says which scanner
directory an item belonged to from generation ``added`` until generation
``removed``, so a directory snapshot at any retained generation is a WHERE
clause rather than a copy of every payload. ``api_native`` is the validated
cache of Kodi identities with a small summary of what was applied -- the
keys Kofin owns and the userdata it last wrote -- never a second copy of the
payload.
"""

import hashlib
import json
import sqlite3
import time
from collections import abc
from dataclasses import dataclass
from typing import Any, Callable, Optional, Union
from collections.abc import Collection, Iterable, Iterator, Sequence

from kofin.sync.catalogue import Catalogue, ItemState
from kofin.sync.model import MediaItem
from kofin.core.log import Logger
from kofin.sync.private import Database
from . import paths
from .kinds import NAMES
from .records import PayloadWindow, Record

LOG = Logger(__name__)

# An episode as its show's hash reads it: id, season and number
# (metadata.episode_row).
EpisodeRow = tuple[str, int, int]


def namespace(server_id: str, user_id: str) -> str:
    if not server_id or not user_id:
        raise ValueError("server and user identity required")
    return hashlib.sha256((server_id + "/" + user_id).encode()).hexdigest()[:32]


def encode(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _digest(value: Any) -> str:
    return hashlib.sha256(encode(value).encode()).hexdigest()[:24]


def payload_hash(payload: Any) -> str:
    """The payload's digest, without ``UserData.Key``.

    The key names the row Jellyfin keeps the user's data under, not anything
    about the item, and the server does not give one answer for it: an album
    whose data was saved under ``<artist>-<album>`` before its MusicBrainz
    release group was known answers with that key or with the release
    group's, depending on Jellyfin's user data cache, which would move an
    unchanged album's hash."""
    userdata = payload.get("UserData") if isinstance(payload, dict) else None
    if isinstance(userdata, dict) and "Key" in userdata:
        payload = dict(
            payload, UserData={k: v for k, v in userdata.items() if k != "Key"}
        )
    return _digest(payload)


def hash_matches(acknowledged: Optional[str], payload: dict[str, Any]) -> bool:
    """Whether an acknowledged digest is this payload's. One made before the
    key left the digest is of the whole payload, and still counts: refusing
    it would have the next repair rewrite every row once."""
    return bool(acknowledged) and acknowledged in (
        payload_hash(payload),
        _digest(payload),
    )


def tombstone(kind: str, item_id: str) -> dict[str, str]:
    """The payload kept for an applied removal: enough to replay, no more."""
    return {"Id": item_id, "Type": kind}


def parent_of(kind: str, payload: dict[str, Any]) -> str:
    """The directory key an item is filed under, '' for a kind with none."""
    if kind in ("Season", "Episode"):
        if not payload.get("SeriesId"):
            raise ValueError("%s %s has no series" % (kind, payload.get("Id")))
        return str(payload["SeriesId"])
    if kind == "Audio":
        return paths.song_folder(payload)
    return ""


@dataclass(frozen=True)
class Entry:
    item_id: str
    kind: str
    library: str
    parent_id: str


# What a pass holds as pending: item id -> (generation, operation, payload).
PendingWork = dict[str, tuple[int, str, dict[str, Any]]]

# What the pass acknowledges a row with: item id, generation, Kodi's id,
# the applied state and the kind.
Acknowledgement = tuple[str, int, Optional[int], dict[str, Any], Optional[str]]


@dataclass(frozen=True)
class Mapping:
    kodi_id: Optional[int]
    applied: dict[str, Any]
    kind: str


# The scanner format of a library whose rows are being removed for a
# rebuild (library.rebuild_stale). It is below every real format, and it is
# in the store because the removal outlives a service restart.
REBUILDING = 0


class Placements(abc.Mapping):
    """The catalogue's placements at one generation, read by the item: a
    pass's own items up front (``preload``), any other as it is asked for,
    and every one at once for a caller that walks the map, or after
    ``WHOLE_AFTER`` single reads, when a caller is reading most of it. A
    pass that holds a few items reads a few rows, where the whole map is
    every item of every library."""

    WHOLE_AFTER = 200

    def __init__(
        self, store: "Store", generation: int, item_ids: Iterable[str] = ()
    ) -> None:
        self._store = store
        self._generation = generation
        self._known: dict[str, Optional[Entry]] = {}
        self._whole: Optional[dict[str, Entry]] = None
        self._misses = 0
        self.preload(item_ids)

    def preload(self, item_ids: Iterable[str]) -> None:
        if self._whole is not None:
            return
        wanted = [i for i in item_ids if i not in self._known]
        if not wanted:
            return
        found = self._store.entries_of(wanted, self._generation)
        for item_id in wanted:
            self._known[item_id] = found.get(item_id)

    @property
    def generation(self) -> int:
        """The catalogue generation these placements were read at."""
        return self._generation

    def whole(self) -> dict[str, Entry]:
        if self._whole is None:
            self._whole = self._store.entries_at(self._generation)
        return self._whole

    def __getitem__(self, item_id: str) -> Entry:
        if self._whole is not None:
            return self._whole[item_id]
        if item_id not in self._known:
            self._misses += 1
            if self._misses > self.WHOLE_AFTER:
                return self.whole()[item_id]
            self.preload([item_id])
        found = self._known[item_id]
        if found is None:
            raise KeyError(item_id)
        return found

    def __iter__(self) -> Iterator[str]:
        return iter(self.whole())

    def __len__(self) -> int:
        return len(self.whole())


class Store(Catalogue):
    @classmethod
    def _create(cls, cursor: sqlite3.Cursor) -> None:
        super()._create(cursor)
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS api_root(
                namespace TEXT PRIMARY KEY, current INTEGER NOT NULL DEFAULT 0,
                pinned INTEGER, server TEXT NOT NULL,
                watermark TEXT NOT NULL DEFAULT '', enumerated REAL NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS api_entry(
                namespace TEXT NOT NULL, item_id TEXT NOT NULL,
                added INTEGER NOT NULL, removed INTEGER,
                kind TEXT NOT NULL, library TEXT NOT NULL, parent_id TEXT NOT NULL,
                PRIMARY KEY(namespace,item_id,added));
            CREATE INDEX IF NOT EXISTS api_entry_live ON api_entry(namespace, removed);
            CREATE INDEX IF NOT EXISTS api_entry_parent ON api_entry(namespace, kind, parent_id);
            CREATE TABLE IF NOT EXISTS api_native(
                namespace TEXT NOT NULL, item_id TEXT NOT NULL, kind TEXT NOT NULL,
                kodi_id INTEGER, applied TEXT NOT NULL DEFAULT '{}',
                PRIMARY KEY(namespace,item_id));
            CREATE TABLE IF NOT EXISTS api_binding(
                namespace TEXT NOT NULL, path TEXT NOT NULL, content TEXT NOT NULL,
                PRIMARY KEY(namespace,path));
            CREATE TABLE IF NOT EXISTS api_salt(
                namespace TEXT NOT NULL, folder TEXT NOT NULL, salt INTEGER NOT NULL,
                PRIMARY KEY(namespace,folder));
            CREATE TABLE IF NOT EXISTS api_walk(
                namespace TEXT NOT NULL, library TEXT NOT NULL, position INTEGER NOT NULL,
                folder TEXT NOT NULL, label TEXT NOT NULL,
                PRIMARY KEY(namespace,library,position));
            CREATE TABLE IF NOT EXISTS api_listed(
                namespace TEXT NOT NULL, library TEXT NOT NULL, folder TEXT NOT NULL,
                PRIMARY KEY(namespace,library,folder));
            CREATE TABLE IF NOT EXISTS api_expected(
                namespace TEXT NOT NULL, item_id TEXT NOT NULL, generation INTEGER NOT NULL,
                expires REAL NOT NULL, payload TEXT NOT NULL,
                PRIMARY KEY(namespace,item_id));
            CREATE TABLE IF NOT EXISTS api_episode_row(
                namespace TEXT NOT NULL, item_id TEXT NOT NULL, generation INTEGER NOT NULL,
                format INTEGER NOT NULL, season INTEGER, episode INTEGER,
                PRIMARY KEY(namespace,item_id));
            CREATE TABLE IF NOT EXISTS api_local_userdata(
                namespace TEXT NOT NULL, item_id TEXT NOT NULL, payload TEXT NOT NULL,
                PRIMARY KEY(namespace,item_id));
            CREATE TABLE IF NOT EXISTS api_setup(
                id INTEGER PRIMARY KEY CHECK(id=1), namespace TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS api_held(
                setting TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS api_rescan(source TEXT PRIMARY KEY);
            CREATE TABLE IF NOT EXISTS api_library(
                namespace TEXT NOT NULL, library TEXT NOT NULL,
                scanner INTEGER NOT NULL,
                PRIMARY KEY(namespace,library));
            CREATE TABLE IF NOT EXISTS api_features(
                namespace TEXT PRIMARY KEY, features TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS api_listing(
                namespace TEXT NOT NULL, library TEXT NOT NULL, fields TEXT NOT NULL,
                PRIMARY KEY(namespace,library));
        """)

    # -- the features of the Kodi the last pass ran on -----------------------

    def features_applied(self) -> Optional[frozenset[str]]:
        """The feature set (capabilities.features) the last completed pass
        shaped its state by; None before any pass stamped one."""
        stamp = self._applied()
        if stamp is None:
            return None
        names = stamp.get("features")
        if not isinstance(names, list):
            return None
        return frozenset(name for name in names if isinstance(name, str))

    def serializer_applied(self) -> Optional[int]:
        """The serializer (metadata.SERIALIZER) the last completed pass
        built its desired states with; None before any pass stamped one,
        and for a stamp of a build that recorded the features alone."""
        stamp = self._applied()
        number = (stamp or {}).get("serializer")
        if isinstance(number, int) and not isinstance(number, bool):
            return number
        return None

    def _applied(self) -> Optional[dict[str, Any]]:
        with Database() as db:
            self._prepare(db.cursor)
            row = db.cursor.execute(
                "SELECT features FROM api_features WHERE namespace=?",
                (self.namespace,),
            ).fetchone()
        if row is None:
            return None
        try:
            stamp = json.loads(row[0])
        except ValueError:
            return None
        if isinstance(stamp, list):
            # A build before the serializer was stamped wrote the list.
            return {"features": stamp}
        return stamp if isinstance(stamp, dict) else None

    def remember_features(self, features: Iterable[str], serializer: int) -> None:
        with Database() as db:
            self._prepare(db.cursor)
            db.cursor.execute(
                "INSERT OR REPLACE INTO api_features VALUES (?,?)",
                (
                    self.namespace,
                    json.dumps(
                        {"features": sorted(features), "serializer": serializer}
                    ),
                ),
            )

    # -- the scanner format a library's rows were filed under ----------------

    def scanner_format(self, library: str) -> int:
        """1 for a library with no record: its rows were filed before the
        record existed (metadata.SCANNER_FORMAT)."""
        with Database() as db:
            self._prepare(db.cursor)
            row = db.cursor.execute(
                "SELECT scanner FROM api_library WHERE namespace=? AND library=?",
                (self.namespace, library),
            ).fetchone()
        return int(row[0]) if row else 1

    def set_scanner_format(self, library: str, value: int) -> None:
        with Database() as db:
            self._prepare(db.cursor)
            db.cursor.execute(
                "INSERT OR REPLACE INTO api_library VALUES (?,?,?)",
                (self.namespace, library, int(value)),
            )

    def rebuilding(self) -> list[str]:
        """The libraries recorded as being rebuilt (REBUILDING): their rows
        are being removed so that the listing after imports them again."""
        with Database() as db:
            self._prepare(db.cursor)
            rows = db.cursor.execute(
                "SELECT library FROM api_library WHERE namespace=? AND scanner=?",
                (self.namespace, REBUILDING),
            ).fetchall()
        return [row[0] for row in rows]

    # -- what the status dialog counts -----------------------------------------

    def summary(self) -> dict[tuple[str, str], tuple[int, int, int]]:
        """(library, kind) -> (items in the catalogue, of them in Kodi, of
        them settled without a row: what Kodi's scanner cannot file)."""
        with Database() as db:
            self._prepare(db.cursor)
            rows = db.cursor.execute(
                """SELECT e.library, e.kind, COUNT(*),
                SUM(CASE WHEN n.kodi_id IS NOT NULL THEN 1 ELSE 0 END),
                SUM(CASE WHEN n.item_id IS NOT NULL AND n.kodi_id IS NULL
                    AND i.status='applied' THEN 1 ELSE 0 END)
                FROM api_entry e
                JOIN api_item i ON i.namespace=e.namespace AND i.item_id=e.item_id
                LEFT JOIN api_native n
                ON n.namespace=e.namespace AND n.item_id=e.item_id
                WHERE e.namespace=? AND e.removed IS NULL
                GROUP BY e.library, e.kind""",
                (self.namespace,),
            ).fetchall()
        return {
            (row[0], row[1]): (int(row[2]), int(row[3] or 0), int(row[4] or 0))
            for row in rows
        }

    def unfiled(
        self, pairs: Iterable[tuple[str, str]]
    ) -> list[tuple[str, str, dict[str, Any]]]:
        """(library, kind, payload) of the items of these ``(library, kind)``
        pairs that ``summary`` counts as settled without a row. The caller
        names the kinds it shows: a music library settles a guest artist
        or an album this way by the hundred, and their payloads stay put."""
        wanted = sorted(set(pairs))
        if not wanted:
            return []
        with Database() as db:
            self._prepare(db.cursor)
            rows = db.cursor.execute(
                """SELECT e.library, e.kind, i.payload
                FROM api_entry e
                JOIN api_item i ON i.namespace=e.namespace AND i.item_id=e.item_id
                JOIN api_native n ON n.namespace=e.namespace AND n.item_id=e.item_id
                WHERE e.namespace=? AND e.removed IS NULL
                AND n.kodi_id IS NULL AND i.status='applied' AND (%s)"""
                % " OR ".join("(e.library=? AND e.kind=?)" for _ in wanted),
                [self.namespace] + [value for pair in wanted for value in pair],
            ).fetchall()
        return [(row[0], row[1], json.loads(row[2])) for row in rows]

    def leaving(self) -> set[str]:
        """The libraries with a removal still pending."""
        return {entry.library for entry in self.tombstones().values() if entry.library}

    def outstanding(self) -> tuple[int, int, str]:
        """(items pending, of them failed at their last try, one failure)."""
        with Database() as db:
            self._prepare(db.cursor)
            pending, failed = db.cursor.execute(
                """SELECT COUNT(*), SUM(CASE WHEN error<>'' THEN 1 ELSE 0 END)
                FROM api_item WHERE namespace=? AND status='pending'""",
                (self.namespace,),
            ).fetchone()
            row = db.cursor.execute(
                """SELECT error FROM api_item
                WHERE namespace=? AND status='pending' AND error<>'' LIMIT 1""",
                (self.namespace,),
            ).fetchone()
        return int(pending or 0), int(failed or 0), row[0] if row else ""

    def has_rows(self, library: str) -> bool:
        """Whether any live item of the library has a native row."""
        with Database() as db:
            self._prepare(db.cursor)
            return bool(
                db.cursor.execute(
                    """SELECT 1 FROM api_native n JOIN api_entry e
                    ON e.namespace=n.namespace AND e.item_id=n.item_id
                    WHERE n.namespace=? AND n.kodi_id IS NOT NULL
                    AND e.removed IS NULL AND e.library=? LIMIT 1""",
                    (self.namespace, library),
                ).fetchone()
            )

    def removing(self, libraries: Iterable[str]) -> bool:
        """Whether a removal is still pending for an item last placed in
        one of these libraries."""
        libraries = list(libraries)
        if not libraries:
            return False
        with Database() as db:
            self._prepare(db.cursor)
            return bool(
                db.cursor.execute(
                    """SELECT 1 FROM api_item i JOIN api_entry e
                    ON e.namespace=i.namespace AND e.item_id=i.item_id
                    WHERE i.namespace=? AND i.operation='remove'
                    AND i.status='pending' AND e.library IN (%s)
                    AND e.added=(SELECT MAX(added) FROM api_entry x
                        WHERE x.namespace=e.namespace AND x.item_id=e.item_id)
                    LIMIT 1""" % ",".join("?" * len(libraries)),
                    [self.namespace] + libraries,
                ).fetchone()
            )

    # -- Kodi settings a scan owes back --------------------------------------

    def hold_setting(self, setting: str, value: Any) -> None:
        """Record the value a Kodi setting had before a scan changed it. The
        first record wins: a hold a stopped Kodi left behind is the user's
        value, and the one read after it is the pass's own."""
        with Database() as db:
            self._prepare(db.cursor)
            db.cursor.execute(
                "INSERT OR IGNORE INTO api_held VALUES (?,?)",
                (setting, json.dumps(value)),
            )

    def held_settings(self) -> dict[str, Any]:
        with Database() as db:
            self._prepare(db.cursor)
            return {
                setting: json.loads(value)
                for setting, value in db.cursor.execute(
                    "SELECT setting, value FROM api_held"
                ).fetchall()
            }

    def release_setting(self, setting: str) -> None:
        with Database() as db:
            self._prepare(db.cursor)
            db.cursor.execute("DELETE FROM api_held WHERE setting=?", (setting,))

    # -- video sources a removal owes a scan ---------------------------------

    def owe_scans(self, sources: Iterable[str]) -> None:
        """Record the video sources whose rows a removal is about to delete
        with ours: Kodi forgets their folders' hashes as it deletes, and only
        a scan of the source files them again. Recorded before the delete,
        the scan is owed whatever stops the pass after it."""
        rows = [(source,) for source in sources]
        if not rows:
            return
        with Database() as db:
            self._prepare(db.cursor)
            db.cursor.executemany("INSERT OR IGNORE INTO api_rescan VALUES (?)", rows)

    def owed_scans(self) -> list[str]:
        with Database() as db:
            self._prepare(db.cursor)
            rows = db.cursor.execute(
                "SELECT source FROM api_rescan ORDER BY source"
            ).fetchall()
        return [row[0] for row in rows]

    def settle_scan(self, source: str) -> None:
        with Database() as db:
            self._prepare(db.cursor)
            db.cursor.execute("DELETE FROM api_rescan WHERE source=?", (source,))

    # -- lifecycle -----------------------------------------------------------

    def initialize(self, server: str) -> None:
        with Database() as db:
            self._prepare(db.cursor)
            db.cursor.execute(
                "INSERT OR IGNORE INTO api_root(namespace,server) VALUES (?,?)",
                (self.namespace, server),
            )
            db.cursor.execute(
                "UPDATE api_root SET server=? WHERE namespace=?",
                (server, self.namespace),
            )
        self._enable_incremental_vacuum()

    def _enable_incremental_vacuum(self) -> None:
        """Reclaim freed pages as they go; needs one VACUUM to take effect."""
        with Database() as db:
            mode = db.conn.execute("PRAGMA auto_vacuum").fetchone()[0]
            if mode == 2:
                return
            db.conn.commit()
            db.conn.execute("PRAGMA auto_vacuum=INCREMENTAL")
            db.conn.execute("VACUUM")

    @classmethod
    def owner(cls) -> Optional[str]:
        """The namespace the setup row names, whoever asks."""
        with Database() as db:
            cls._prepare(db.cursor)
            row = db.cursor.execute(
                "SELECT namespace FROM api_setup WHERE id=1"
            ).fetchone()
        return str(row[0]) if row else None

    def prepared(self) -> Optional[str]:
        with Database() as db:
            self._prepare(db.cursor)
            row = db.cursor.execute(
                "SELECT namespace FROM api_setup WHERE id=1"
            ).fetchone()
        found: Optional[str] = row[0] if row else None
        return found

    def prepare_empty(self) -> None:
        with Database() as db:
            self._prepare(db.cursor)
            db.cursor.execute("INSERT INTO api_setup VALUES (1,?)", (self.namespace,))

    # -- publication ---------------------------------------------------------

    def publish(
        self,
        items: Iterable[dict[str, Any]],
        membership: Union[dict[str, str], str, None] = None,
        library: Optional[str] = None,
        removed: Iterable[str] = (),
        complete_libraries: Optional[Collection[str]] = None,
        complete_boxsets: bool = False,
    ) -> int:
        """A validated listing, or a batch of explicit item changes.

        The caller must finish fetching and validating first: one transaction
        commits the desired payloads, their membership and every tombstone.
        ``library`` says the items are that library's complete listing;
        ``complete_libraries`` says the same for a union; ``complete_boxsets``
        says every collection is present. Nothing else implies deletion.
        """
        media = [MediaItem.from_dto(item) for item in items]
        parents = {}
        for medium in media:
            if medium.kind not in NAMES or not medium.payload.get("Name"):
                raise ValueError("complete %s metadata required" % medium.kind)
            parents[medium.item_id] = parent_of(medium.kind, medium.payload)
        if len({m.item_id for m in media}) != len(media):
            raise ValueError("duplicate identities")
        with Database() as db:
            cursor = db.cursor
            self._prepare(cursor)
            # executescript in _prepare commits implicitly; start only after DDL.
            cursor.execute("BEGIN IMMEDIATE")
            row = cursor.execute(
                "SELECT current, pinned FROM api_root WHERE namespace=?",
                (self.namespace,),
            ).fetchone()
            if not row:
                raise ValueError("directory not initialized")
            current: int = row[0]
            pinned: Optional[int] = row[1]
            following = current + 1
            incoming = {m.item_id for m in media}
            if library is None and not complete_libraries and not complete_boxsets:
                # Only a complete listing deletes by absence; a batch of
                # changes needs no placement but its own.
                live = self._live_entries(cursor, incoming | set(removed))
            else:
                live = {
                    e.item_id: e for e in self._entries(cursor, "removed IS NULL", ())
                }
            deleting = {i for i in removed if i in live}
            for item_id, entry in live.items():
                if item_id in incoming:
                    continue
                if library is not None and entry.library == library:
                    deleting.add(item_id)
                elif complete_libraries and entry.library in complete_libraries:
                    deleting.add(item_id)
                elif complete_boxsets and entry.kind == "BoxSet":
                    deleting.add(item_id)
            changed = False
            for medium in media:
                old = live.get(medium.item_id)
                item_library: Optional[str]
                if medium.kind == "BoxSet":
                    item_library = ""
                else:
                    item_library = (
                        membership.get(medium.item_id)
                        if isinstance(membership, dict)
                        else membership
                    )
                    if item_library is None and library is not None:
                        item_library = library
                    if item_library is None and old is not None:
                        item_library = old.library
                    if not item_library:
                        raise ValueError(
                            "new %s %s requires a selected library"
                            % (medium.kind, medium.item_id)
                        )
                parent = parents[medium.item_id]
                before = cursor.execute(
                    "SELECT desired FROM api_item WHERE namespace=? AND item_id=?",
                    (self.namespace, medium.item_id),
                ).fetchone()
                generation = self.stage_in(cursor, medium)
                if before is None or before[0] != generation:
                    changed = True
                entry = Entry(medium.item_id, medium.kind, item_library, parent)
                if old != entry:
                    changed = True
                    if old is not None:
                        cursor.execute(
                            "UPDATE api_entry SET removed=? WHERE namespace=? AND item_id=? AND removed IS NULL",
                            (following, self.namespace, medium.item_id),
                        )
                    cursor.execute(
                        "INSERT INTO api_entry VALUES (?,?,?,NULL,?,?,?)",
                        (
                            self.namespace,
                            medium.item_id,
                            following,
                            medium.kind,
                            item_library,
                            parent,
                        ),
                    )
                    if (
                        old is not None
                        and before is not None
                        and before[0] == generation
                    ):
                        # A move between libraries changes the native tags
                        # without touching the payload: it must still be work.
                        generation += 1
                        cursor.execute(
                            "UPDATE api_item SET desired=?,status='pending' WHERE namespace=? AND item_id=?",
                            (generation, self.namespace, medium.item_id),
                        )
                deleting.discard(medium.item_id)
            for item_id in sorted(deleting):
                entry = live[item_id]
                changed = True
                stored = cursor.execute(
                    "SELECT payload FROM api_item WHERE namespace=? AND item_id=?",
                    (self.namespace, item_id),
                ).fetchone()
                payload = (
                    json.loads(stored[0]) if stored else tombstone(entry.kind, item_id)
                )
                self.stage_in(cursor, MediaItem.from_dto(payload, entry.kind), "remove")
                cursor.execute(
                    "UPDATE api_entry SET removed=? WHERE namespace=? AND item_id=? AND removed IS NULL",
                    (following, self.namespace, item_id),
                )
            if not changed:
                return current
            cursor.execute(
                "UPDATE api_root SET current=? WHERE namespace=?",
                (following, self.namespace),
            )
            # A closed interval is reachable only through a retained
            # generation; the pin and the current one are the only two. A
            # pending removal keeps its last placement until it is applied.
            self._collect(cursor, pinned if pinned is not None else following)
            return following

    def _collect(
        self, cursor: sqlite3.Cursor, floor: int, item_id: Optional[str] = None
    ) -> None:
        query = (
            "DELETE FROM api_entry WHERE namespace=? AND removed IS NOT NULL AND removed<=?"
            " AND item_id NOT IN (SELECT item_id FROM api_item WHERE namespace=?"
            " AND operation='remove' AND status='pending')"
        )
        params: list[Any] = [self.namespace, floor, self.namespace]
        if item_id is not None:
            query += " AND item_id=?"
            params.append(item_id)
        cursor.execute(query, params)

    def _entries(
        self, cursor: sqlite3.Cursor, where: str, params: Sequence[Any]
    ) -> list[Entry]:
        rows = cursor.execute(
            "SELECT item_id, kind, library, parent_id FROM api_entry WHERE namespace=? AND "
            + where,
            (self.namespace,) + tuple(params),
        ).fetchall()
        return [Entry(*row) for row in rows]

    def _live_entries(
        self, cursor: sqlite3.Cursor, item_ids: Iterable[str]
    ) -> dict[str, Entry]:
        ids = sorted(item_ids)
        found: dict[str, Entry] = {}
        for start in range(0, len(ids), 500):
            chunk = ids[start : start + 500]
            for entry in self._entries(
                cursor,
                "removed IS NULL AND item_id IN (%s)" % ",".join("?" * len(chunk)),
                chunk,
            ):
                found[entry.item_id] = entry
        return found

    def _generation(self, cursor: sqlite3.Cursor, pinned: bool) -> int:
        row = cursor.execute(
            "SELECT current, pinned FROM api_root WHERE namespace=?",
            (self.namespace,),
        ).fetchone()
        if not row:
            raise ValueError("no committed directory")
        current: int = row[0]
        pin: Optional[int] = row[1]
        return pin if pinned and pin is not None else current

    def entries(
        self, pinned: bool = True, kind: Optional[str] = None
    ) -> dict[str, Entry]:
        """Membership at the pinned generation (or the current one), of one
        kind when asked."""
        with Database() as db:
            self._prepare(db.cursor)
            generation = self._generation(db.cursor, pinned)
            where = "added<=? AND (removed IS NULL OR removed>?)"
            params: tuple = (generation, generation)
            if kind is not None:
                where += " AND kind=?"
                params += (kind,)
            return {e.item_id: e for e in self._entries(db.cursor, where, params)}

    def placements(self, item_ids: Iterable[str] = ()) -> "Placements":
        """Membership at the pinned generation, read by the item: ``item_ids``
        now, the rest as it is asked for (``Placements``)."""
        with Database() as db:
            self._prepare(db.cursor)
            generation = self._generation(db.cursor, True)
        return Placements(self, generation, item_ids)

    def entries_of(self, item_ids: Iterable[str], generation: int) -> dict[str, Entry]:
        """The placements of ``item_ids`` at ``generation``, a few hundred to
        a query."""
        ids = sorted(set(item_ids))
        found: dict[str, Entry] = {}
        with Database() as db:
            self._prepare(db.cursor)
            for start in range(0, len(ids), 500):
                chunk = ids[start : start + 500]
                for entry in self._entries(
                    db.cursor,
                    "added<=? AND (removed IS NULL OR removed>?) AND item_id IN (%s)"
                    % ",".join("?" * len(chunk)),
                    [generation, generation] + chunk,
                ):
                    found[entry.item_id] = entry
        return found

    def entries_at(self, generation: int) -> dict[str, Entry]:
        with Database() as db:
            self._prepare(db.cursor)
            return {
                e.item_id: e
                for e in self._entries(
                    db.cursor,
                    "added<=? AND (removed IS NULL OR removed>?)",
                    (generation, generation),
                )
            }

    def has_survivor(
        self, library: str, generation: int, exclude_kinds: Collection[str]
    ) -> bool:
        """Whether ``library`` has a member at ``generation``, not of
        ``exclude_kinds``, with no removal pending. One row answers, on the
        same generation predicate as ``entries_at``."""
        excluded = list(exclude_kinds)
        kind_sql = ""
        if excluded:
            kind_sql = " AND e.kind NOT IN (%s)" % ",".join("?" * len(excluded))
        with Database() as db:
            self._prepare(db.cursor)
            row = db.cursor.execute(
                """SELECT 1 FROM api_entry e
                WHERE e.namespace=? AND e.added<=?
                AND (e.removed IS NULL OR e.removed>?) AND e.library=?"""
                + kind_sql
                + """ AND NOT EXISTS (SELECT 1 FROM api_item i
                    WHERE i.namespace=e.namespace AND i.item_id=e.item_id
                    AND i.status='pending' AND i.operation='remove')
                LIMIT 1""",
                [self.namespace, generation, generation, library] + excluded,
            ).fetchone()
        return row is not None

    def filed_under(self, kind: str, parent_id: str) -> list[str]:
        """The ids of one kind filed under a parent, live and not leaving."""
        with Database() as db:
            self._prepare(db.cursor)
            rows = db.cursor.execute(
                "SELECT e.item_id FROM api_entry e"
                " JOIN api_item i ON i.namespace = e.namespace AND i.item_id = e.item_id"
                " WHERE e.namespace=? AND e.kind=? AND e.parent_id=?"
                " AND e.removed IS NULL AND i.operation='upsert'",
                (self.namespace, kind, parent_id),
            ).fetchall()
        return [row[0] for row in rows]

    def entry(self, item_id: str) -> Optional[Entry]:
        """The current placement of one item, tombstoned items excluded."""
        with Database() as db:
            self._prepare(db.cursor)
            rows = self._entries(db.cursor, "item_id=? AND removed IS NULL", (item_id,))
        return rows[0] if rows else None

    def known(self, item_ids: Iterable[str]) -> set[str]:
        """Which of ``item_ids`` the catalogue places now, as ``entry`` reads
        one: an item whose removal is pending is not one of them."""
        ids = list(item_ids)
        found: set[str] = set()
        with Database() as db:
            self._prepare(db.cursor)
            for start in range(0, len(ids), 500):
                chunk = ids[start : start + 500]
                found.update(
                    row[0]
                    for row in db.cursor.execute(
                        "SELECT item_id FROM api_entry WHERE namespace=?"
                        " AND removed IS NULL AND item_id IN (%s)"
                        % ",".join("?" * len(chunk)),
                        [self.namespace] + chunk,
                    )
                )
        return found

    def states(self, item_ids: Iterable[str]) -> dict[str, ItemState]:
        """``state`` for many items, a few hundred to a query; an item the
        catalogue has no row of is left out."""
        ids = list(item_ids)
        result: dict[str, ItemState] = {}
        with Database() as db:
            self._prepare(db.cursor)
            for start in range(0, len(ids), 500):
                chunk = ids[start : start + 500]
                for row in db.cursor.execute(
                    "SELECT item_id, desired, applied, operation, status, error"
                    " FROM api_item WHERE namespace=? AND item_id IN (%s)"
                    % ",".join("?" * len(chunk)),
                    [self.namespace] + chunk,
                ):
                    result[row[0]] = ItemState(*row[1:])
        return result

    def tombstones(self) -> dict[str, Entry]:
        """The last known placement of every item with a pending removal."""
        with Database() as db:
            self._prepare(db.cursor)
            # From the pending removals (api_item_status): joined the other
            # way, SQLite walks every placement with a subquery each.
            rows = db.cursor.execute(
                """SELECT e.item_id, e.kind, e.library, e.parent_id FROM api_entry e
                WHERE e.namespace=? AND e.item_id IN (SELECT item_id FROM api_item
                    WHERE namespace=? AND status='pending' AND operation='remove')
                AND e.added=(SELECT MAX(added) FROM api_entry x
                    WHERE x.namespace=e.namespace AND x.item_id=e.item_id)""",
                (self.namespace, self.namespace),
            ).fetchall()
            return {row[0]: Entry(*row) for row in rows}

    def payload(self, item_id: str) -> dict[str, Any]:
        """One item's desired payload."""
        with Database() as db:
            self._prepare(db.cursor)
            row = db.cursor.execute(
                "SELECT payload FROM api_item WHERE namespace=? AND item_id=?",
                (self.namespace, item_id),
            ).fetchone()
        return json.loads(row[0]) if row else {}

    def payloads(self, item_ids: Iterable[str]) -> dict[str, dict[str, Any]]:
        """The desired payloads of ``item_ids``, a few hundred to a query."""
        ids = list(item_ids)
        result: dict[str, dict[str, Any]] = {}
        if not ids:
            return result
        with Database() as db:
            self._prepare(db.cursor)
            for start in range(0, len(ids), 500):
                chunk = ids[start : start + 500]
                rows = db.cursor.execute(
                    "SELECT item_id, payload FROM api_item WHERE namespace=? AND item_id IN (%s)"
                    % ",".join("?" * len(chunk)),
                    [self.namespace] + chunk,
                ).fetchall()
                for item_id, payload in rows:
                    result[item_id] = json.loads(payload)
        return result

    def pending_work(self) -> list[tuple[str, int, str, dict[str, Any]]]:
        """Every pending item with its generation and operation, in id order.

        A removal carries its tombstone (it names what it removes); an
        upsert carries ``{}``, its payload read on demand through a
        ``PayloadWindow``, so a first import or a repair never holds the
        catalogue in memory.
        """
        with Database() as db:
            self._prepare(db.cursor)
            rows = db.cursor.execute(
                """SELECT item_id, desired, operation,
                CASE WHEN operation='remove' THEN payload END
                FROM api_item WHERE namespace=? AND status='pending' ORDER BY item_id""",
                (self.namespace,),
            ).fetchall()
        return [
            (item_id, generation, operation, json.loads(payload) if payload else {})
            for item_id, generation, operation, payload in rows
        ]

    def records(
        self,
        kind: Union[str, Iterable[str], None] = None,
        library: Optional[str] = None,
        parent_id: Optional[str] = None,
        item_ids: Optional[Iterable[str]] = None,
        pinned: bool = True,
        payloads: bool = True,
    ) -> dict[str, Record]:
        """Payloads of the members a scanner callback or a repair pass needs.

        With ``payloads=False`` the records come without their payloads and
        read them on first use, one at a time.
        """
        where = ["e.added<=?", "(e.removed IS NULL OR e.removed>?)"]
        t0 = time.monotonic()
        with Database() as db:
            t1 = time.monotonic()
            self._prepare(db.cursor)
            t2 = time.monotonic()
            generation = self._generation(db.cursor, pinned)
            t3 = time.monotonic()
            params: list[Any] = [generation, generation]
            if kind is not None:
                kinds = (kind,) if isinstance(kind, str) else tuple(kind)
                where.append("e.kind IN (%s)" % ",".join("?" * len(kinds)))
                params.extend(kinds)
            if library is not None:
                where.append("e.library=?")
                params.append(library)
            if parent_id is not None:
                where.append("e.parent_id=?")
                params.append(parent_id)
            if item_ids is not None:
                ids = list(item_ids)
                if not ids:
                    return {}
                where.append("e.item_id IN (%s)" % ",".join("?" * len(ids)))
                params.extend(ids)
            rows = db.cursor.execute(
                """SELECT e.item_id, e.kind, e.library, e.parent_id, %s, i.desired
                FROM api_entry e JOIN api_item i ON i.namespace=e.namespace AND i.item_id=e.item_id
                WHERE e.namespace=? AND """ % ("i.payload" if payloads else "NULL")
                + " AND ".join(where),
                [self.namespace] + params,
            ).fetchall()
        t4 = time.monotonic()
        if t4 - t0 > 1.0:
            LOG.debug(
                "slow records(%s): open %.2f prepare %.2f generation %.2f query %.2f s",
                kind,
                t1 - t0,
                t2 - t1,
                t3 - t2,
                t4 - t3,
            )
        return {
            row[0]: Record(
                row[0],
                row[1],
                row[2],
                row[3],
                json.loads(row[4]) if row[4] is not None else None,
                row[5],
                loader=None if row[4] is not None else self.payload,
            )
            for row in rows
        }

    def episode_rows(
        self,
        library: str,
        reduce: Callable[[dict[str, Any]], Optional[EpisodeRow]],
        row_format: int,
        pinned: bool = True,
    ) -> dict[str, list[EpisodeRow]]:
        """What ``reduce`` makes of each episode of ``library``, by show,
        without the episodes it answers None for.

        A row is kept beside the generation of the payload it was reduced
        from and ``row_format``, the caller's number for what ``reduce``
        reads of a payload. Only an episode whose payload has moved since,
        one kept under another format and one never reduced have their
        payload read,
        so a library nothing changed in is answered without a payload. A
        payload staged between the two reads is kept under the generation
        before it, which the next read finds moved.
        """
        with Database() as db:
            self._prepare(db.cursor)
            generation = self._generation(db.cursor, pinned)
            found = db.cursor.execute(
                """SELECT e.item_id, e.parent_id, i.desired,
                    r.generation, r.format, r.season, r.episode
                FROM api_entry e
                JOIN api_item i ON i.namespace=e.namespace AND i.item_id=e.item_id
                LEFT JOIN api_episode_row r
                    ON r.namespace=e.namespace AND r.item_id=e.item_id
                WHERE e.namespace=? AND e.added<=?
                    AND (e.removed IS NULL OR e.removed>?)
                    AND e.kind='Episode' AND e.library=?""",
                (self.namespace, generation, generation, library),
            ).fetchall()
        rows: dict[str, list[EpisodeRow]] = {}
        moved: dict[str, tuple[str, int]] = {}
        for item_id, parent, desired, kept, kept_format, season, episode in found:
            if kept != desired or kept_format != row_format:
                moved[item_id] = (parent, desired)
            elif season is not None:
                rows.setdefault(parent, []).append((item_id, season, episode))
        reduced = []
        ids = sorted(moved)
        for start in range(0, len(ids), PayloadWindow.CHUNK):
            for item_id, payload in self.payloads(
                ids[start : start + PayloadWindow.CHUNK]
            ).items():
                parent, desired = moved[item_id]
                row = reduce(payload)
                reduced.append(
                    (
                        self.namespace,
                        item_id,
                        desired,
                        row_format,
                        row[1] if row else None,
                        row[2] if row else None,
                    )
                )
                if row is not None:
                    rows.setdefault(parent, []).append(row)
        if reduced:
            try:
                with Database() as db:
                    self._prepare(db.cursor)
                    db.cursor.executemany(
                        "INSERT OR REPLACE INTO api_episode_row VALUES (?,?,?,?,?,?)",
                        reduced,
                    )
            except sqlite3.Error as error:
                # The rows are the answer either way; unkept, they are
                # reduced again by the next read.
                LOG.debug("episode rows not kept: %s", error)
        return rows

    def folders(self, kind: str, library: str, pinned: bool = True) -> list[str]:
        """The directory keys live items of ``kind`` file under, without
        loading a payload."""
        with Database() as db:
            self._prepare(db.cursor)
            generation = self._generation(db.cursor, pinned)
            rows = db.cursor.execute(
                """SELECT DISTINCT parent_id FROM api_entry WHERE namespace=? AND kind=?
                AND library=? AND added<=? AND (removed IS NULL OR removed>?)""",
                (self.namespace, kind, library, generation, generation),
            ).fetchall()
        return [row[0] for row in rows if row[0]]

    def all_libraries(self) -> list[str]:
        """Every library with a live item, whatever its kind."""
        with Database() as db:
            self._prepare(db.cursor)
            rows = db.cursor.execute(
                "SELECT DISTINCT library FROM api_entry WHERE namespace=? AND removed IS NULL",
                (self.namespace,),
            ).fetchall()
        return sorted(row[0] for row in rows if row[0])

    def unfinished_removals(self) -> int:
        """Tombstones no pass has confirmed yet."""
        with Database() as db:
            self._prepare(db.cursor)
            row = db.cursor.execute(
                "SELECT COUNT(*) FROM api_item WHERE namespace=? AND operation='remove' AND status='pending'",
                (self.namespace,),
            ).fetchone()
        return int(row[0]) if row else 0

    def adopt(self, owner: str) -> None:
        """Take the catalogue over from ``owner``: its rows go from every
        namespaced table and the setup row names this namespace. Only for
        an owner whose rows have left Kodi (Native.retire)."""
        with Database() as db:
            self._prepare(db.cursor)
            tables = [
                row[0]
                for row in db.cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' "
                    "AND name LIKE 'api\\_%' ESCAPE '\\'"
                ).fetchall()
            ]
            for table in tables:
                columns = [
                    row[1]
                    for row in db.cursor.execute(
                        'PRAGMA table_info("%s")' % table
                    ).fetchall()
                ]
                if "namespace" in columns and table != "api_setup":
                    db.cursor.execute(
                        'DELETE FROM "%s" WHERE namespace=?' % table, (owner,)
                    )
            db.cursor.execute(
                "UPDATE api_setup SET namespace=? WHERE id=1", (self.namespace,)
            )

    def libraries(self, kind: str) -> list[str]:
        """The libraries with a live item of ``kind``."""
        with Database() as db:
            self._prepare(db.cursor)
            rows = db.cursor.execute(
                "SELECT DISTINCT library FROM api_entry WHERE namespace=? AND kind=? AND removed IS NULL",
                (self.namespace, kind),
            ).fetchall()
        return sorted(row[0] for row in rows if row[0])

    def item(self, item_id: str) -> Optional[dict[str, Any]]:
        with Database() as db:
            self._prepare(db.cursor)
            row = db.cursor.execute(
                "SELECT payload FROM api_item WHERE namespace=? AND item_id=? AND operation='upsert'",
                (self.namespace, item_id),
            ).fetchone()
        payload: Optional[dict[str, Any]] = json.loads(row[0]) if row else None
        return payload

    def server(self) -> str:
        with Database() as db:
            self._prepare(db.cursor)
            row = db.cursor.execute(
                "SELECT server FROM api_root WHERE namespace=?", (self.namespace,)
            ).fetchone()
        server: str = row[0] if row else ""
        return server

    def generation(self) -> int:
        with Database() as db:
            self._prepare(db.cursor)
            row = db.cursor.execute(
                "SELECT current FROM api_root WHERE namespace=?", (self.namespace,)
            ).fetchone()
        current: int = row[0] if row else 0
        return current

    def pin(self) -> int:
        with Database() as db:
            self._prepare(db.cursor)
            db.cursor.execute(
                "UPDATE api_root SET pinned=COALESCE(pinned,current) WHERE namespace=? AND current>0",
                (self.namespace,),
            )
            return self._generation(db.cursor, True)

    def unpin(self) -> None:
        with Database() as db:
            self._prepare(db.cursor)
            db.cursor.execute(
                "UPDATE api_root SET pinned=NULL WHERE namespace=?", (self.namespace,)
            )

    # -- native identities ---------------------------------------------------

    def populated(self, kind: Optional[str] = None) -> bool:
        """Whether any owned item of ``kind`` (or any kind) has a native row."""
        with Database() as db:
            self._prepare(db.cursor)
            query = "SELECT 1 FROM api_native WHERE namespace=? AND kodi_id IS NOT NULL"
            params: tuple[Any, ...] = (self.namespace,)
            if kind is not None:
                query += " AND kind=?"
                params += (kind,)
            return bool(db.cursor.execute(query + " LIMIT 1", params).fetchone())

    def mapping(self, item_id: str) -> Optional[Mapping]:
        with Database() as db:
            self._prepare(db.cursor)
            row = db.cursor.execute(
                "SELECT kodi_id, applied, kind FROM api_native WHERE namespace=? AND item_id=?",
                (self.namespace, item_id),
            ).fetchone()
        if not row:
            return None
        return Mapping(row[0], json.loads(row[1] or "{}"), row[2])

    def mappings(
        self, kind: Optional[str] = None, library: Optional[str] = None
    ) -> dict[str, Mapping]:
        where = ["n.namespace=?"]
        params: list[Any] = [self.namespace]
        if kind is not None:
            where.append("n.kind=?")
            params.append(kind)
        if library is not None:
            where.append(
                "EXISTS (SELECT 1 FROM api_entry e WHERE e.namespace=n.namespace"
                " AND e.item_id=n.item_id AND e.removed IS NULL AND e.library=?)"
            )
            params.append(library)
        with Database() as db:
            self._prepare(db.cursor)
            rows = db.cursor.execute(
                "SELECT n.item_id, n.kodi_id, n.applied, n.kind FROM api_native n WHERE "
                + " AND ".join(where),
                params,
            ).fetchall()
        return {
            row[0]: Mapping(row[1], json.loads(row[2] or "{}"), row[3]) for row in rows
        }

    def placed_in(
        self, kind: str, library: str, parent_ids: Iterable[str]
    ) -> list[str]:
        """The items of ``kind`` the catalogue places now under ``parent_ids``
        of ``library``, a few hundred parents to a query (api_entry_parent)."""
        parents = sorted(set(parent_ids))
        found: list[str] = []
        with Database() as db:
            self._prepare(db.cursor)
            for start in range(0, len(parents), 500):
                chunk = parents[start : start + 500]
                found.extend(
                    row[0]
                    for row in db.cursor.execute(
                        "SELECT item_id FROM api_entry WHERE namespace=? AND kind=?"
                        " AND parent_id IN (%s) AND library=? AND removed IS NULL"
                        % ",".join("?" * len(chunk)),
                        [self.namespace, kind] + chunk + [library],
                    )
                )
        return found

    def mappings_of(self, item_ids: Iterable[str]) -> dict[str, Mapping]:
        """The mappings of ``item_ids``, a few hundred to a query; an item
        with no mapping is left out."""
        ids = list(item_ids)
        found: dict[str, Mapping] = {}
        with Database() as db:
            self._prepare(db.cursor)
            for start in range(0, len(ids), 500):
                chunk = ids[start : start + 500]
                for row in db.cursor.execute(
                    "SELECT item_id, kodi_id, applied, kind FROM api_native"
                    " WHERE namespace=? AND item_id IN (%s)"
                    % ",".join("?" * len(chunk)),
                    [self.namespace] + chunk,
                ):
                    found[row[0]] = Mapping(row[1], json.loads(row[2] or "{}"), row[3])
        return found

    def refile(self, removed: Iterable[tuple[str, int]]) -> list[str]:
        """The items filed on the Kodi rows ``removed`` names ((kind, Kodi
        id)), with the seasons and episodes of a show among them, put back to
        pending with their acknowledgement emptied: the pass looks for each
        as if it had never compared it, scans what it cannot find, and
        compares what it finds. A tombstone is left alone. The mapping keeps
        its Kodi id, so a row Kodi lists under another source's file is still
        looked for (Readback.show, Readback.movie)."""
        by_kind: dict[str, list[int]] = {}
        for kind, kodi_id in removed:
            by_kind.setdefault(kind, []).append(kodi_id)
        found: dict[str, str] = {}
        with Database() as db:
            self._prepare(db.cursor)
            db.cursor.execute("BEGIN IMMEDIATE")
            for kind, kodi_ids in sorted(by_kind.items()):
                for start in range(0, len(kodi_ids), 500):
                    ids = kodi_ids[start : start + 500]
                    found.update(
                        db.cursor.execute(
                            "SELECT n.item_id, n.kind FROM api_native n JOIN api_item i"
                            " ON i.namespace=n.namespace AND i.item_id=n.item_id"
                            " WHERE n.namespace=? AND n.kind=? AND i.operation='upsert'"
                            " AND n.kodi_id IN (%s)" % ",".join("?" * len(ids)),
                            [self.namespace, kind, *ids],
                        ).fetchall()
                    )
            shows = sorted(
                item_id for item_id, kind in found.items() if kind == "Series"
            )
            for start in range(0, len(shows), 500):
                chunk = shows[start : start + 500]
                found.update(
                    db.cursor.execute(
                        "SELECT e.item_id, e.kind FROM api_entry e JOIN api_native n"
                        " ON n.namespace=e.namespace AND n.item_id=e.item_id"
                        " WHERE e.namespace=? AND e.removed IS NULL"
                        " AND e.kind IN ('Season','Episode') AND e.parent_id IN (%s)"
                        % ",".join("?" * len(chunk)),
                        [self.namespace, *chunk],
                    ).fetchall()
                )
            items = sorted(found)
            for start in range(0, len(items), 500):
                chunk = items[start : start + 500]
                marks = ",".join("?" * len(chunk))
                db.cursor.execute(
                    "UPDATE api_native SET applied='{}' WHERE namespace=? AND item_id IN (%s)"
                    % marks,
                    [self.namespace, *chunk],
                )
                db.cursor.execute(
                    "UPDATE api_item SET status='pending' WHERE namespace=?"
                    " AND operation='upsert' AND item_id IN (%s)" % marks,
                    [self.namespace, *chunk],
                )
        return items

    def mapped_to(self, kind: str, kodi_id: int) -> list[str]:
        """The items of ``kind`` acknowledged against Kodi's row ``kodi_id``."""
        with Database() as db:
            self._prepare(db.cursor)
            rows = db.cursor.execute(
                "SELECT item_id FROM api_native WHERE namespace=? AND kind=? AND kodi_id=?",
                (self.namespace, kind, kodi_id),
            ).fetchall()
        return sorted(row[0] for row in rows)

    def movies_with_extras(
        self, has_extras: Callable[[dict[str, Any]], bool]
    ) -> tuple[dict[str, Entry], set[str]]:
        """The movies at the pinned generation, as ``entries`` reads them,
        and which of them an acknowledgement lists extras for
        (metadata.asset_files), in one read (Native.bind_movie_folders).

        An acknowledgement older than the file list carries the assets token
        alone, which cannot tell extras from versions, and a movie whose
        token never moved is never planned again to gain the list. Such a
        movie is asked of its payload (``has_extras``), a chunk at a time, so
        the read holds no library's payloads."""
        with Database() as db:
            self._prepare(db.cursor)
            generation = self._generation(db.cursor, True)
            entries = {
                e.item_id: e
                for e in self._entries(
                    db.cursor,
                    "added<=? AND (removed IS NULL OR removed>?) AND kind=?",
                    (generation, generation, "Movie"),
                )
            }
            rows = db.cursor.execute(
                "SELECT item_id, applied FROM api_native"
                " WHERE namespace=? AND kind='Movie'",
                (self.namespace,),
            ).fetchall()
            extras = set()
            older = []
            for item_id, applied in rows:
                acknowledged = json.loads(applied or "{}")
                if "asset_files" in acknowledged:
                    if (acknowledged["asset_files"] or {}).get("extras"):
                        extras.add(item_id)
                elif acknowledged.get("assets") and item_id in entries:
                    older.append(item_id)
            for start in range(0, len(older), 500):
                chunk = older[start : start + 500]
                payloads = db.cursor.execute(
                    "SELECT item_id, payload FROM api_item WHERE namespace=? AND item_id IN (%s)"
                    % ",".join("?" * len(chunk)),
                    [self.namespace] + chunk,
                ).fetchall()
                for item_id, payload in payloads:
                    if has_extras(json.loads(payload)):
                        extras.add(item_id)
        return entries, extras

    def remember(
        self,
        item_id: str,
        generation: int,
        kodi_id: Optional[int],
        applied: dict[str, Any],
        kind: Optional[str] = None,
    ) -> bool:
        """Acknowledge readback of exactly the desired generation."""
        return self.remember_many([(item_id, generation, kodi_id, applied, kind)]) == 1

    def remember_many(self, rows: Iterable[Acknowledgement]) -> int:
        """One transaction for a batch of acknowledgements; returns how many
        matched their desired generation. A pass over a real catalogue is
        thousands of these, and one commit each cost more than the pass."""
        count = 0
        with Database() as db:
            self._prepare(db.cursor)
            db.cursor.execute("BEGIN IMMEDIATE")
            for item_id, generation, kodi_id, applied, kind in rows:
                db.cursor.execute(
                    """UPDATE api_item SET applied=desired,status='applied',error=''
                    WHERE namespace=? AND item_id=? AND desired=? AND operation='upsert'""",
                    (self.namespace, item_id, generation),
                )
                if not db.cursor.rowcount:
                    continue
                count += 1
                if kind is None:
                    kind = db.cursor.execute(
                        "SELECT kind FROM api_item WHERE namespace=? AND item_id=?",
                        (self.namespace, item_id),
                    ).fetchone()[0]
                db.cursor.execute(
                    """INSERT INTO api_native(namespace,item_id,kind,kodi_id,applied) VALUES (?,?,?,?,?)
                    ON CONFLICT(namespace,item_id) DO UPDATE SET kind=excluded.kind,
                    kodi_id=excluded.kodi_id, applied=excluded.applied""",
                    (self.namespace, item_id, kind, kodi_id, encode(applied or {})),
                )
        return count

    def forget(self, item_id: str, generation: int) -> bool:
        """Acknowledge a removal: the native identity goes, the payload shrinks."""
        return self.forget_many([(item_id, generation)]) == 1

    def forget_many(self, rows: Iterable[tuple[str, int]]) -> int:
        """One transaction for a batch of removal acknowledgements; returns
        how many matched their desired generation. An empty batch opens no
        transaction: a removal that settled nothing still calls this."""
        rows = list(rows)
        if not rows:
            return 0
        count = 0
        with Database() as db:
            self._prepare(db.cursor)
            db.cursor.execute("BEGIN IMMEDIATE")
            root = db.cursor.execute(
                "SELECT current, pinned FROM api_root WHERE namespace=?",
                (self.namespace,),
            ).fetchone()
            for item_id, generation in rows:
                row = db.cursor.execute(
                    "SELECT kind FROM api_item WHERE namespace=? AND item_id=? AND desired=? AND operation='remove'",
                    (self.namespace, item_id, generation),
                ).fetchone()
                if not row:
                    continue
                count += 1
                db.cursor.execute(
                    """UPDATE api_item SET applied=desired,status='applied',error='',payload=?
                    WHERE namespace=? AND item_id=?""",
                    (encode(tombstone(row[0], item_id)), self.namespace, item_id),
                )
                db.cursor.execute(
                    "DELETE FROM api_native WHERE namespace=? AND item_id=?",
                    (self.namespace, item_id),
                )
                db.cursor.execute(
                    "DELETE FROM api_expected WHERE namespace=? AND item_id=?",
                    (self.namespace, item_id),
                )
                db.cursor.execute(
                    "DELETE FROM api_episode_row WHERE namespace=? AND item_id=?",
                    (self.namespace, item_id),
                )
            if count and root:
                # One collection for the batch: the query's "still pending"
                # subquery scans the item table.
                self._collect(db.cursor, root[1] if root[1] is not None else root[0])
        return count

    def invalidate(self, item_ids: Iterable[str]) -> None:
        """Put applied upserts back to pending; their desired state is unchanged."""
        ids = list(item_ids)
        if not ids:
            return
        with Database() as db:
            self._prepare(db.cursor)
            for start in range(0, len(ids), 500):
                chunk = ids[start : start + 500]
                db.cursor.execute(
                    "UPDATE api_item SET status='pending' WHERE namespace=? AND operation='upsert'"
                    " AND item_id IN (%s)" % ",".join("?" * len(chunk)),
                    [self.namespace] + chunk,
                )

    # -- scanner bindings, watermarks --------------------------------------------

    def bindings(self) -> dict[str, str]:
        with Database() as db:
            self._prepare(db.cursor)
            return dict(
                db.cursor.execute(
                    "SELECT path, content FROM api_binding WHERE namespace=?",
                    (self.namespace,),
                ).fetchall()
            )

    def bind(self, path: str, content: str) -> None:
        with Database() as db:
            self._prepare(db.cursor)
            db.cursor.execute(
                "INSERT OR REPLACE INTO api_binding VALUES (?,?,?)",
                (self.namespace, path, content),
            )

    def salt(self, folder: str) -> int:
        """How many times a music directory's listing has been salted: a
        directory whose scan left its songs missing is one Kodi
        skips "due to no change" (its hash was stored by a scan stopped
        before the songs were written); salting the dates moves the hash."""
        with Database() as db:
            self._prepare(db.cursor)
            row = db.cursor.execute(
                "SELECT salt FROM api_salt WHERE namespace=? AND folder=?",
                (self.namespace, folder),
            ).fetchone()
        return int(row[0]) if row else 0

    def salts(self) -> dict[str, int]:
        """Every salted directory with its salt, in one read."""
        with Database() as db:
            self._prepare(db.cursor)
            rows = db.cursor.execute(
                "SELECT folder, salt FROM api_salt WHERE namespace=?",
                (self.namespace,),
            ).fetchall()
        return {folder: int(salt) for folder, salt in rows}

    def plan_walk(self, library: str, rows: Iterable[tuple[str, str]]) -> None:
        """The album directories a scan of the library is to visit, in order,
        each with the label it is listed under. The pass writes the plan
        before the scan and the provider lists it a part at a time
        (``walk_part``), reading no payload. A new plan has had none of its
        directories listed (``listed``)."""
        with Database() as db:
            self._prepare(db.cursor)
            db.cursor.execute("BEGIN IMMEDIATE")
            db.cursor.execute(
                "DELETE FROM api_walk WHERE namespace=? AND library=?",
                (self.namespace, library),
            )
            db.cursor.execute(
                "DELETE FROM api_listed WHERE namespace=? AND library=?",
                (self.namespace, library),
            )
            db.cursor.executemany(
                "INSERT INTO api_walk VALUES (?,?,?,?,?)",
                [
                    (self.namespace, library, position, folder, label)
                    for position, (folder, label) in enumerate(rows)
                ],
            )

    def walk_part(self, library: str, index: int, size: int) -> list[tuple[str, str]]:
        """(folder, label) of the directories in one part of the plan."""
        with Database() as db:
            self._prepare(db.cursor)
            rows = db.cursor.execute(
                """SELECT folder, label FROM api_walk WHERE namespace=? AND library=?
                AND position>=? AND position<? ORDER BY position""",
                (self.namespace, library, index * size, (index + 1) * size),
            ).fetchall()
        return [(folder, label) for folder, label in rows]

    def walk_size(self, library: str) -> int:
        """How many directories the library's plan names."""
        with Database() as db:
            self._prepare(db.cursor)
            row = db.cursor.execute(
                "SELECT COUNT(*) FROM api_walk WHERE namespace=? AND library=?",
                (self.namespace, library),
            ).fetchone()
        return int(row[0]) if row else 0

    def note_listed(self, library: str, folder: str) -> None:
        """Record that Kodi is handed the catalogue's listing of a directory
        the library's plan names (the provider, before the handover). A
        directory outside the plan, or one already recorded, writes
        nothing."""
        with Database() as db:
            self._prepare(db.cursor)
            owed = db.cursor.execute(
                """SELECT 1 FROM api_walk w WHERE w.namespace=? AND w.library=?
                AND w.folder=? AND NOT EXISTS (SELECT 1 FROM api_listed l
                    WHERE l.namespace=w.namespace AND l.library=w.library
                    AND l.folder=w.folder)""",
                (self.namespace, library, folder),
            ).fetchone()
            if owed:
                db.cursor.execute(
                    "INSERT OR IGNORE INTO api_listed VALUES (?,?,?)",
                    (self.namespace, library, folder),
                )

    def listed(self, library: str) -> set[str]:
        """The directories of the library's plan whose listing Kodi has been
        handed since the plan was written."""
        with Database() as db:
            self._prepare(db.cursor)
            rows = db.cursor.execute(
                "SELECT folder FROM api_listed WHERE namespace=? AND library=?",
                (self.namespace, library),
            ).fetchall()
        return {row[0] for row in rows}

    def bump_salt(self, folder: str) -> int:
        with Database() as db:
            self._prepare(db.cursor)
            db.cursor.execute(
                """INSERT INTO api_salt VALUES (?,?,1)
                ON CONFLICT(namespace, folder) DO UPDATE SET salt=salt+1""",
                (self.namespace, folder),
            )
        return self.salt(folder)

    def bind_many(self, pairs: Iterable[tuple[str, str]]) -> None:
        """``bind`` for a batch of (path, content), one transaction."""
        pairs = list(pairs)
        if not pairs:
            return
        with Database() as db:
            self._prepare(db.cursor)
            db.cursor.executemany(
                "INSERT OR REPLACE INTO api_binding VALUES (?,?,?)",
                [(self.namespace, path, content) for path, content in pairs],
            )

    def unbind(self, prefix: str) -> None:
        with Database() as db:
            self._prepare(db.cursor)
            db.cursor.execute(
                "DELETE FROM api_binding WHERE namespace=? AND SUBSTR(path,1,?)=?",
                (self.namespace, len(prefix), prefix),
            )

    def watermark(self) -> tuple[str, float]:
        with Database() as db:
            self._prepare(db.cursor)
            row = db.cursor.execute(
                "SELECT watermark, enumerated FROM api_root WHERE namespace=?",
                (self.namespace,),
            ).fetchone()
        return (row[0], row[1]) if row else ("", 0.0)

    def set_watermark(
        self, watermark: Optional[str] = None, enumerated: Optional[float] = None
    ) -> None:
        with Database() as db:
            self._prepare(db.cursor)
            if watermark is not None:
                db.cursor.execute(
                    "UPDATE api_root SET watermark=? WHERE namespace=?",
                    (watermark, self.namespace),
                )
            if enumerated is not None:
                db.cursor.execute(
                    "UPDATE api_root SET enumerated=? WHERE namespace=?",
                    (enumerated, self.namespace),
                )

    def listings(self) -> dict[str, str]:
        """library -> what its last published listing asked the server for
        (library.LISTING); a library with none is missing."""
        with Database() as db:
            self._prepare(db.cursor)
            rows = db.cursor.execute(
                "SELECT library, fields FROM api_listing WHERE namespace=?",
                (self.namespace,),
            ).fetchall()
        return {row[0]: row[1] for row in rows}

    def remember_listing(self, libraries: Iterable[str], fields: str) -> None:
        with Database() as db:
            self._prepare(db.cursor)
            db.cursor.executemany(
                "INSERT OR REPLACE INTO api_listing VALUES (?,?,?)",
                [(self.namespace, library, fields) for library in libraries],
            )

    # -- userdata echoes and the local outbox --------------------------------

    def expect(self, item_id: str, generation: int, userdata: dict[str, Any]) -> None:
        self.expect_many([(item_id, generation, userdata)])

    def expect_many(
        self, expectations: Iterable[tuple[str, int, dict[str, Any]]]
    ) -> None:
        with Database() as db:
            self._prepare(db.cursor)
            db.cursor.executemany(
                "INSERT OR REPLACE INTO api_expected VALUES (?,?,?,?,?)",
                [
                    (
                        self.namespace,
                        item_id,
                        generation,
                        time.time() + 120,
                        encode(userdata),
                    )
                    for item_id, generation, userdata in expectations
                ],
            )

    def is_echo(self, item_id: str, field: str, value: Any) -> bool:
        with Database() as db:
            self._prepare(db.cursor)
            row = db.cursor.execute(
                """SELECT e.payload FROM api_expected e JOIN api_item i USING(namespace,item_id)
                WHERE e.namespace=? AND e.item_id=? AND e.expires>?
                AND e.generation=i.desired""",
                (self.namespace, item_id, time.time()),
            ).fetchone()
        if not row:
            return False
        expected = json.loads(row[0]).get(field)
        if field == "resume":
            # Match native readback's precision; runtime is not a local edit.
            return bool(
                expected is not None
                and abs(expected.get("position", 0) - value["position"]) < 1
            )
        return bool(expected == value)

    def local(self, item_id: str, values: dict[str, Any]) -> None:
        with Database() as db:
            self._prepare(db.cursor)
            db.cursor.execute("BEGIN IMMEDIATE")
            row = db.cursor.execute(
                "SELECT payload FROM api_local_userdata WHERE namespace=? AND item_id=?",
                (self.namespace, item_id),
            ).fetchone()
            payload = json.loads(row[0]) if row else {}
            payload.update(values)
            db.cursor.execute(
                "INSERT OR REPLACE INTO api_local_userdata VALUES (?,?,?)",
                (self.namespace, item_id, encode(payload)),
            )

    def local_pending(self) -> list[tuple[str, dict[str, Any]]]:
        with Database() as db:
            self._prepare(db.cursor)
            return [
                (item_id, json.loads(payload))
                for item_id, payload in db.cursor.execute(
                    "SELECT item_id,payload FROM api_local_userdata WHERE namespace=?",
                    (self.namespace,),
                ).fetchall()
            ]

    def local_done(self, item_id: str, values: dict[str, Any]) -> None:
        with Database() as db:
            self._prepare(db.cursor)
            db.cursor.execute(
                "DELETE FROM api_local_userdata WHERE namespace=? AND item_id=? AND payload=?",
                (self.namespace, item_id, encode(values)),
            )
