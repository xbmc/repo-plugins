"""Kofin-owned SQLite and sync state, independent of Kodi's native databases.

Test overrides and the per-path schema guard are restart-safe: their keys are
complete private paths, and reset_overrides clears both.
"""

import datetime
import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from typing import Any, Optional
from collections.abc import Iterator

import xbmcvfs

from kofin.core.log import Logger

LOG = Logger(__name__)
ADDON_DATA = "special://profile/addon_data/plugin.video.kofin/"
_path_overrides: dict[str, str] = {}
_tables_ensured: set = set()

# Connections kept open for the plugin process, per path and thread. Module
# state, deliberately: it lives in a plugin interpreter Kodi recycles, never
# in the service (``pool_connections`` is called from the provider and the
# play route only), so a reused interpreter reuses its connection and pays a
# fresh connection's first statement once.
_pooling = False
_pool: dict[tuple[str, int], "sqlite3.Connection"] = {}


def pool_connections(enabled: bool) -> None:
    """Keep this process's private-database connections open between uses."""
    global _pooling
    _pooling = enabled
    if not enabled:
        for conn in _pool.values():
            try:
                conn.close()
            except Exception:
                pass
        _pool.clear()


# The connections a service thread holds for the length of a ``with
# hold_connections()``. Thread state, and none of it outlives the block that
# made it: the block closes every connection on its way out, so a service
# restart, which ends the thread, finds nothing left behind.
_held = threading.local()


@contextmanager
def hold_connections() -> Iterator[None]:
    """Keep this thread's private-database connection open across every
    ``Database`` block inside the ``with``.

    In WAL mode with nobody else connected, every open and close creates and
    tears down the WAL and its index; holding the connection turns a block
    into a statement.
    """
    depth = getattr(_held, "depth", 0)
    if depth == 0:
        _held.connections = {}
    _held.depth = depth + 1
    try:
        yield
    finally:
        _held.depth -= 1
        if _held.depth == 0:
            connections, _held.connections = _held.connections, {}
            for conn in connections.values():
                try:
                    conn.close()
                except Exception as error:
                    LOG.debug("held connection not closed: %s", error)


def set_path_override(kind: str, path: str) -> None:
    if kind != "kofin":
        raise ValueError("only Kofin-owned storage is supported")
    _path_overrides[kind] = path


def reset_overrides() -> None:
    """Forget every override and pooled connection: the tests' clean slate."""
    _path_overrides.clear()
    _tables_ensured.clear()
    pool_connections(False)


def addon_data_path() -> str:
    return xbmcvfs.translatePath(ADDON_DATA)


def resolve_path(db_file: str = "kofin") -> str:
    if db_file != "kofin":
        raise ValueError("only Kofin-owned storage is supported")
    if db_file in _path_overrides:
        return _path_overrides[db_file]
    directory = addon_data_path()
    if not xbmcvfs.exists(ADDON_DATA):
        xbmcvfs.mkdirs(ADDON_DATA)
    return os.path.join(directory, "kofin.db")


class Database:
    """This should be called like a context.
    i.e. with Database('kofin') as db:
        db.cursor
        db.conn.commit()
    """

    timeout = 120

    def __init__(self, db_file: Optional[str] = None, commit_close: bool = True):
        """Open Kofin's own database; native kinds and literal paths are refused."""
        self.db_file = db_file or "kofin"
        self.commit_close = commit_close

    def __enter__(self) -> "Database":
        self.path = self._resolve_path()
        key = (self.path, threading.get_ident())
        held = _held.connections if getattr(_held, "depth", 0) else None
        self._pooled = _pooling or held is not None
        pooled = _pool.get(key) if _pooling else None
        if pooled is None and held is not None:
            pooled = held.get(self.path)
        if pooled is not None:
            self.conn = pooled
            self.cursor = self.conn.cursor()
            self._changes_at_enter = self.conn.total_changes
            return self
        self.conn = sqlite3.connect(self.path, timeout=self.timeout)
        try:
            self.cursor = self.conn.cursor()

            self._prepare()
        except BaseException:
            # __exit__ never runs when __enter__ raises, so the handle would
            # leak with the WAL lock held for the rest of the process.
            self.conn.close()
            raise
        if _pooling:
            _pool[key] = self.conn
        elif held is not None:
            held[self.path] = self.conn
        self._changes_at_enter = self.conn.total_changes

        return self

    def _resolve_path(self) -> str:
        return resolve_path(self.db_file)

    def _prepare(self) -> None:
        # WAL is configured only for Kofin's own file here.
        self.conn.execute("PRAGMA journal_mode=WAL")
        if self.path not in _tables_ensured:
            kofin_tables(self.cursor)
            self.conn.commit()
            _tables_ensured.add(self.path)

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Close the connection and cursor.

        The exception path rolls back to the last commit rather than
        committing.

        A block leaves the connection idle whether or not it changed a row.
        ``total_changes`` counts since the connection opened, so on a
        pooled connection it is read as a delta from ``__enter__``; and a
        block that began a transaction without changing a row still ends
        it, or the next block on this interpreter would run inside it and a
        failure there would roll both back while the write lock stayed held.
        """
        try:
            changes = self.conn.total_changes - getattr(self, "_changes_at_enter", 0)

            if exc_type is not None:
                LOG.error("type: %s value: %s", exc_type, exc_val)
                self.conn.rollback()
            elif self.commit_close and (changes or self.conn.in_transaction):

                LOG.debug("[%s] %s rows updated.", self.db_file, changes)
                self.conn.commit()
        finally:
            LOG.debug("---<[ database: %s ] %s", self.db_file, id(self.conn))
            self.cursor.close()
            if not getattr(self, "_pooled", False):
                self.conn.close()


def kofin_tables(cursor: "sqlite3.Cursor") -> None:
    """Create every kofin.db table."""
    cursor.execute("""CREATE TABLE IF NOT EXISTS view(
        view_id TEXT UNIQUE, view_name TEXT, media_type TEXT)""")
    # Jellyfin playlists are Kodi files, not MyVideos/MyMusic rows. checksum
    # is the server Etag; filename is the basename under the managed folder.
    cursor.execute("""CREATE TABLE IF NOT EXISTS playlist_state(
        jellyfin_id TEXT PRIMARY KEY, media_type TEXT NOT NULL,
        filename TEXT NOT NULL, checksum TEXT NOT NULL)""")
    # Tables an earlier build kept and nothing reads; a profile it filed
    # still holds them.
    for table in ("playlist_item", "boxset_state", "version"):
        cursor.execute("DROP TABLE IF EXISTS %s" % table)
    cursor.execute("""CREATE TABLE IF NOT EXISTS download_subscription(
        owner TEXT NOT NULL, jellyfin_id TEXT NOT NULL,
        PRIMARY KEY(owner, jellyfin_id))""")
    cursor.execute("""CREATE INDEX IF NOT EXISTS download_subscription_item
        ON download_subscription(jellyfin_id)""")
    # Offline downloads. Rows leave only on remove; ``state`` walks
    # queued|active|done|failed. ``rel_path`` is relative to the downloads
    # root, which is a setting and may move; ``quality`` records the request
    # that produced the file and ``userdata_json`` the server's UserData, both
    # at queue time.
    cursor.execute("""CREATE TABLE IF NOT EXISTS download(
        jellyfin_id TEXT PRIMARY KEY, media_type TEXT, series_id TEXT,
        state TEXT, origin TEXT, rel_path TEXT, container TEXT,
        size_expected INTEGER, size_actual INTEGER, quality TEXT,
        bytes_done INTEGER, userdata_json TEXT,
        queued_at INTEGER, done_at INTEGER, error TEXT,
        segments_json TEXT,
        request_id TEXT, request_name TEXT, validator TEXT)""")
    # CREATE IF NOT EXISTS never revisits an existing table: a new column goes
    # in the CREATE above *and* here.
    _ensure_columns(
        cursor,
        "download",
        {
            "segments_json": "TEXT",
            "request_id": "TEXT",
            "request_name": "TEXT",
            "validator": "TEXT",
        },
    )

    # Userdata a playback produced while the server was unreachable, replayed
    # on the next connect. One row per item — a later event coalesces onto
    # it — and NULL means "unchanged".
    cursor.execute("""CREATE TABLE IF NOT EXISTS pending_userdata(
        jellyfin_id TEXT PRIMARY KEY, media_type TEXT, played INTEGER,
        position_ticks INTEGER, event_at INTEGER, attempts INTEGER,
        server_snapshot TEXT)""")

    cursor.execute("""CREATE INDEX IF NOT EXISTS idx_download_series
        ON download(series_id, state)""")
    cursor.execute("""CREATE INDEX IF NOT EXISTS idx_download_state
        ON download(state, queued_at)""")
    # Every completed song asks "is the rest of my request still coming"
    # (store.request_counts), which on a hundred-track playlist is a hundred
    # scans of the table without this.
    cursor.execute("""CREATE INDEX IF NOT EXISTS idx_download_request
        ON download(request_id)""")


def _ensure_columns(
    cursor: "sqlite3.Cursor", table: str, columns: dict[str, str]
) -> None:
    """ALTER TABLE ADD COLUMN for any listed column the table lacks."""
    cursor.execute("PRAGMA table_info(%s)" % table)
    present = {row[1] for row in cursor.fetchall()}
    for name, declaration in columns.items():
        if name in present:
            continue
        try:
            cursor.execute(
                "ALTER TABLE %s ADD COLUMN %s %s" % (table, name, declaration)
            )
        except sqlite3.OperationalError as error:
            # Two connections race this at service start (the main thread
            # and a download worker both open kofin.db): each reads the
            # PRAGMA before the other's ALTER commits, and the loser's
            # "duplicate column name" is the winner's success.
            if "duplicate column" not in str(error).lower():
                raise


class SyncStateCorrupt(Exception):
    """sync.json exists but cannot be parsed.

    Raised rather than defaulted: a bad read would otherwise answer an empty
    whitelist.
    """


def get_sync() -> dict[str, Any]:
    """The sync state record (pending libraries, restore points, whitelist).

    A missing or empty file answers defaults — a fresh install, or the
    truncate-then-crash a pre-atomic ``save_sync`` could leave behind.
    Content that exists but does not parse as a JSON object raises
    :class:`SyncStateCorrupt` (see its docstring for why defaulting is the
    dangerous answer).
    """
    if not xbmcvfs.exists(ADDON_DATA):
        xbmcvfs.mkdirs(ADDON_DATA)

    path = os.path.join(addon_data_path(), "sync.json")
    try:
        with open(path, "rb") as infile:
            raw = infile.read()
    except FileNotFoundError:
        raw = b""
    except OSError as error:
        raise SyncStateCorrupt("sync.json unreadable: %s" % error) from error

    sync: dict[str, Any] = {}
    if raw.strip():
        try:
            loaded = json.loads(raw)
        except ValueError as error:
            raise SyncStateCorrupt("sync.json corrupt: %s" % error) from error
        if not isinstance(loaded, dict):
            raise SyncStateCorrupt(
                "sync.json corrupt: expected an object, found %s" % type(loaded)
            )
        sync = loaded

    sync["Libraries"] = sync.get("Libraries", [])
    sync["RestorePoints"] = sync.get("RestorePoints", {})
    sync["Whitelist"] = list(set(sync.get("Whitelist", [])))
    sync["SortedViews"] = sync.get("SortedViews", [])

    return sync


def save_sync(sync: dict[str, Any]) -> None:
    """Write the record atomically: temp file, fsync, ``os.replace``.

    A reader sees the old record or the new one, never a mixture, and the
    fsync keeps a power loss from replacing the record with an empty file on
    filesystems that defer allocation.
    """
    if not xbmcvfs.exists(ADDON_DATA):
        xbmcvfs.mkdirs(ADDON_DATA)

    sync["Date"] = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    path = os.path.join(addon_data_path(), "sync.json")
    temp_path = path + ".tmp"
    data = json.dumps(sync, sort_keys=True, indent=4, ensure_ascii=False)
    with open(temp_path, "wb") as outfile:
        outfile.write(data.encode("utf-8"))
        outfile.flush()
        os.fsync(outfile.fileno())
    os.replace(temp_path, path)
