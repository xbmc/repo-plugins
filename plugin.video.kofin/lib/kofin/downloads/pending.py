"""Userdata that could not reach the server, and its replay.

Userdata a failed push would lose is parked and replayed on the next
connect.

One row per item, not per event: a later event overwrites only the fields
it carries (:func:`enqueue`), so a replay cannot resurrect a stale position.

NULL means "unchanged": a row can carry a position without touching the
played flag, and vice versa.
"""

import json
import time
from dataclasses import dataclass
from typing import Any, Optional

from kofin.core.log import Logger
from kofin.sync.private import Database

LOG = Logger(__name__)

# How many times a row is replayed before it is dropped. A row that fails
# this often is not a connection problem — it is an item the server will not
# accept (deleted, or a permission change) — and keeping it forever would
# retry it on every single connect for the life of the install.
MAX_ATTEMPTS = 5


@dataclass
class Pending:
    jellyfin_id: str
    media_type: str = ""
    played: Optional[int] = None
    position_ticks: Optional[int] = None
    event_at: int = 0
    attempts: int = 0
    server_snapshot: str = ""

    @property
    def snapshot(self) -> dict[str, Any]:
        if not self.server_snapshot:
            return {}
        try:
            parsed = json.loads(self.server_snapshot)
        except ValueError:
            return {}
        return parsed if isinstance(parsed, dict) else {}


def enqueue(
    jellyfin_id: str,
    media_type: str = "",
    played: Optional[bool] = None,
    position_ticks: Optional[int] = None,
    snapshot: Optional[dict[str, Any]] = None,
) -> None:
    """Park a userdata change for the next connect.

    Coalesces onto any existing row for the item: the fields this call
    carries win, the others keep what they had, and the timestamp moves so
    the replay order follows the newest evidence. The snapshot is only
    written the first time — it records what the server looked like *before*
    we went away, which is what the conflict rule compares against.
    """
    if not jellyfin_id:
        return
    now = int(time.time())
    with Database("kofin") as opened:
        opened.cursor.execute(
            "SELECT jellyfin_id FROM pending_userdata WHERE jellyfin_id = ?",
            (jellyfin_id,),
        )
        exists = opened.cursor.fetchone() is not None
        if not exists:
            opened.cursor.execute(
                "INSERT INTO pending_userdata (jellyfin_id, media_type, played, "
                "position_ticks, event_at, attempts, server_snapshot) "
                "VALUES (?, ?, ?, ?, ?, 0, ?)",
                (
                    jellyfin_id,
                    media_type,
                    None if played is None else int(played),
                    position_ticks,
                    now,
                    json.dumps(snapshot or {}),
                ),
            )
            LOG.debug("userdata parked for %s (played=%s)", jellyfin_id, played)
            return
        sets = ["event_at = ?", "attempts = 0"]
        args: list[Any] = [now]
        if media_type:
            sets.append("media_type = ?")
            args.append(media_type)
        if played is not None:
            sets.append("played = ?")
            args.append(int(played))
        if position_ticks is not None:
            sets.append("position_ticks = ?")
            args.append(int(position_ticks))
        args.append(jellyfin_id)
        opened.cursor.execute(
            "UPDATE pending_userdata SET %s WHERE jellyfin_id = ?" % ", ".join(sets),
            tuple(args),
        )
        LOG.debug("userdata coalesced for %s (played=%s)", jellyfin_id, played)


def rows() -> list[Pending]:
    with Database("kofin") as opened:
        opened.cursor.execute(
            "SELECT jellyfin_id, media_type, played, position_ticks, event_at, "
            "attempts, server_snapshot FROM pending_userdata ORDER BY event_at, "
            "jellyfin_id"
        )
        fetched = opened.cursor.fetchall()
    return [
        Pending(
            jellyfin_id=row[0],
            media_type=row[1] or "",
            played=row[2],
            position_ticks=row[3],
            event_at=int(row[4] or 0),
            attempts=int(row[5] or 0),
            server_snapshot=row[6] or "",
        )
        for row in fetched
    ]


def remove(jellyfin_id: str) -> None:
    with Database("kofin") as opened:
        opened.cursor.execute(
            "DELETE FROM pending_userdata WHERE jellyfin_id = ?", (jellyfin_id,)
        )


def record_attempt(jellyfin_id: str) -> int:
    """Count a failed replay; returns the new count. At MAX_ATTEMPTS the row
    is dropped — see the constant."""
    with Database("kofin") as opened:
        opened.cursor.execute(
            "UPDATE pending_userdata SET attempts = attempts + 1 WHERE jellyfin_id = ?",
            (jellyfin_id,),
        )
        opened.cursor.execute(
            "SELECT attempts FROM pending_userdata WHERE jellyfin_id = ?",
            (jellyfin_id,),
        )
        row = opened.cursor.fetchone()
    attempts = int(row[0]) if row else MAX_ATTEMPTS
    if attempts >= MAX_ATTEMPTS:
        LOG.warning(
            "dropping parked userdata for %s after %d attempts",
            jellyfin_id,
            attempts,
        )
        remove(jellyfin_id)
    return attempts


def resolve(row: Pending, server: dict[str, Any]) -> dict[str, Any]:
    """What to send, given the server's *current* userdata for the item.

    - The server has not moved since the snapshot: replay verbatim.
    - The server *has* moved: keep the further position — a viewer who got
      to 40 minutes elsewhere should not be dragged back to 20 — and keep a
      played flag only if it is still being set, never cleared, because
      un-watching something on the strength of stale local state is the one
      irreversible mistake here.

    Returns {} when there is nothing left worth sending.
    """
    snapshot = row.snapshot
    moved = str(server.get("LastPlayedDate") or "") != str(
        snapshot.get("LastPlayedDate") or ""
    )
    payload: dict[str, Any] = {}
    if row.played is not None:
        if not moved or row.played:
            payload["Played"] = bool(row.played)
    if row.position_ticks is not None:
        position = int(row.position_ticks)
        if moved:
            position = max(position, int(server.get("PlaybackPositionTicks") or 0))
        payload["PlaybackPositionTicks"] = position
    # A finished item has no meaningful resume point, and sending one is how
    # a watched episode reappears in Continue Watching (Findroid #406).
    if payload.get("Played"):
        payload["PlaybackPositionTicks"] = 0
    return payload
