"""The kofin.db ``download`` table: what is downloaded, wanted, or failed.

One row per item, keyed by jellyfin id; a row leaves the table when its
download is removed or cancelled, or its file is found missing. The DDL lives
in :func:`kofin.sync.private.kofin_tables` so the table exists wherever
kofin.db exists.

State machine: queued -> active -> done | failed; failed -> queued on a
re-request (keeping ``bytes_done``, so an original resumes with a Range).
``active`` rows found at manager start are a crash's leftovers and go back
to queued (:func:`recover_interrupted`).
"""

import json
import time
from dataclasses import dataclass, fields as dataclass_fields
from typing import Any, Optional
from collections.abc import Sequence

from kofin.core.log import Logger
from kofin.sync.private import Database

LOG = Logger(__name__)

QUEUED = "queued"
ACTIVE = "active"
DONE = "done"
FAILED = "failed"

ORIGIN_USER = "user"
# Automatic downloads carry "auto:<context>" — the retention sweep matches
# the prefix, never the user origin.
ORIGIN_AUTO_PREFIX = "auto"


def is_auto_origin(origin: str) -> bool:
    return str(origin or "").startswith(ORIGIN_AUTO_PREFIX)


QUALITY_ORIGINAL = "original"
# Decided at transfer time (downloads/quality.py), recorded so retry and
# recovery know the .part is not byte-stable: a transcode restarts clean
# where an original resumes with a Range.
QUALITY_TRANSCODE = "transcode"

# The two video kinds every per-type policy branches on. "" (unknown) is
# deliberately not here — each consumer decides what unknown means.
VIDEO_MEDIA_TYPES = ("movie", "episode")


@dataclass
class Download:
    jellyfin_id: str
    media_type: str = ""
    series_id: str = ""
    state: str = QUEUED
    origin: str = ORIGIN_USER
    rel_path: str = ""
    container: str = ""
    size_expected: int = 0
    size_actual: int = 0
    quality: str = QUALITY_ORIGINAL
    bytes_done: int = 0
    userdata_json: str = ""
    queued_at: int = 0
    done_at: int = 0
    error: str = ""
    # The raw /MediaSegments body taken at download completion: parsed at
    # claim time, where the parser lives. Empty means never fetched (the
    # online claim path falls back to its own fetch); a stored
    # '{"Items": []}' is known-empty, so nobody asks again.
    segments_json: str = ""
    # What the user asked to download: its Jellyfin id and name. Distinct
    # from ``series_id``, which is the *item's* parent — a
    # playlist's twelve tracks have twelve different albums and one request.
    # The name is stored so the final toast survives a service restart;
    # both are empty for anything queued automatically.
    request_id: str = ""
    request_name: str = ""
    # The server's validator (a strong ETag, else Last-Modified) for the file
    # whose bytes the original's ``.part`` holds, sent as If-Range on a
    # resume. Written whenever a ``.part`` starts again from byte zero.
    validator: str = ""

    @property
    def userdata(self) -> dict[str, Any]:
        """The server UserData snapshot taken at queue time, {} when none."""
        if not self.userdata_json:
            return {}
        try:
            parsed = json.loads(self.userdata_json)
        except ValueError:
            return {}
        return parsed if isinstance(parsed, dict) else {}


_COLUMNS = tuple(field.name for field in dataclass_fields(Download))


def _row_to_download(row: Any) -> Download:
    values = {name: value for name, value in zip(_COLUMNS, row) if value is not None}
    return Download(**values)


_SELECT = "SELECT %s FROM download" % ", ".join(_COLUMNS)


def queue(download: Download) -> bool:
    """Add a download request; True when it was actually (re)queued.

    An absent row is inserted queued. A failed row is re-queued in place,
    keeping ``bytes_done`` so an original resumes where it died. A row that
    is queued, active or done is left alone — the menu should not have
    offered Download, and a double-tap must not double-fetch.
    """
    now = download.queued_at or int(time.time())
    with Database("kofin") as opened:
        opened.cursor.execute(
            "SELECT state FROM download WHERE jellyfin_id = ?",
            (download.jellyfin_id,),
        )
        existing = opened.cursor.fetchone()
        if existing is None:
            values = {name: getattr(download, name) for name in _COLUMNS}
            values.update(state=QUEUED, queued_at=now, error="")
            opened.cursor.execute(
                "INSERT INTO download (%s) VALUES (%s)"
                % (", ".join(_COLUMNS), ", ".join("?" for _ in _COLUMNS)),
                tuple(values[name] for name in _COLUMNS),
            )
            return True
        if existing[0] == FAILED:
            # A failed transcode's frozen target is worthless — nothing
            # resumes into a re-encode — and can itself be the failure (a
            # name the attempt could not put on disk), so it re-freezes
            # fresh. Originals keep theirs: that is the Range resume. The
            # CASE reads the pre-update row, as SQLite guarantees.
            opened.cursor.execute(
                "UPDATE download SET state = ?, queued_at = ?, error = '', "
                "rel_path = CASE WHEN quality = ? THEN '' ELSE rel_path END, "
                "bytes_done = CASE WHEN quality = ? THEN 0 ELSE bytes_done END, "
                "quality = ?, origin = ?, request_id = ?, request_name = ? "
                "WHERE jellyfin_id = ?",
                (
                    QUEUED,
                    now,
                    QUALITY_TRANSCODE,
                    QUALITY_TRANSCODE,
                    download.quality,
                    download.origin,
                    download.request_id,
                    download.request_name,
                    download.jellyfin_id,
                ),
            )
            return True
    return False


def get(jellyfin_id: str) -> Optional[Download]:
    with Database("kofin") as opened:
        return get_on(opened.cursor, jellyfin_id)


def get_on(cursor: Any, jellyfin_id: str) -> Optional[Download]:
    """`get` on a caller-held cursor."""
    cursor.execute(_SELECT + " WHERE jellyfin_id = ?", (jellyfin_id,))
    row = cursor.fetchone()
    return _row_to_download(row) if row is not None else None


def container_states(container_id: str) -> dict[str, str]:
    """``{jellyfin_id: state}`` for every download under a container.

    ``series_id`` is written as ``SeriesId or AlbumId`` (manager._transfer),
    which answers a Series and a MusicAlbum; a Season is answered through the
    catalogue (``_season_states``), and a playlist or a music library by the
    request or the origin that names it. No server: the context menu that
    asks this has to answer offline too.
    """
    if not container_id:
        return {}
    states: dict[str, str] = {}
    with Database("kofin") as opened:
        opened.cursor.execute(
            "SELECT jellyfin_id, state FROM download WHERE series_id = ?",
            (container_id,),
        )
        states.update(opened.cursor.fetchall())
        opened.cursor.execute(
            "SELECT jellyfin_id, state FROM download WHERE request_id = ? "
            "OR origin IN (?, ?)",
            (
                container_id,
                "auto:playlist:%s" % container_id,
                "auto:musiclibrary:%s" % container_id,
            ),
        )
        states.update(opened.cursor.fetchall())
    states.update(_season_states(container_id))
    return states


def _season_states(season_id: str) -> dict[str, str]:
    """A season's downloads, through the catalogue: it files an episode under
    its series (store.parent_of), so the season's downloads are the rows of
    the series' live episodes whose payload names the season. A row is found
    by its id, never by ``series_id``, which a queued row carries only once a
    worker has started it. The downloads under one series are few, and their
    payloads are read for that one key. The catalogue is namespaced per
    server and user and the download table is not, so the active namespace
    alone is asked; with none, nothing is filed to find."""
    from kofin.sync.backends.api.identity import current_store

    try:
        catalogue = current_store()
        season = catalogue.entry(season_id)
    except Exception:
        return {}
    if season is None or season.kind != "Season":
        return {}
    episodes = catalogue.filed_under("Episode", season.parent_id)
    rows: dict[str, str] = {}
    with Database("kofin") as opened:
        for start in range(0, len(episodes), 500):
            chunk = episodes[start : start + 500]
            opened.cursor.execute(
                "SELECT jellyfin_id, state FROM download WHERE jellyfin_id IN (%s)"
                % ",".join("?" * len(chunk)),
                chunk,
            )
            rows.update(opened.cursor.fetchall())
    found: dict[str, str] = {}
    for jellyfin_id, item in catalogue.payloads(rows).items():
        if str(item.get("SeasonId") or item.get("ParentId") or "") == season_id:
            found[jellyfin_id] = rows[jellyfin_id]
    return found


def request_counts(request_id: str) -> dict[str, int]:
    """Counts for one queue request, including failures."""
    if not request_id:
        return {"total": 0, "pending": 0, "failed": 0}
    with Database("kofin") as opened:
        opened.cursor.execute(
            "SELECT state FROM download WHERE request_id = ?", (request_id,)
        )
        states = [row[0] for row in opened.cursor.fetchall()]
    return {
        "total": len(states),
        "pending": sum(1 for state in states if state in (QUEUED, ACTIVE)),
        "failed": sum(1 for state in states if state == FAILED),
    }


def container_counts(container_id: str) -> dict[str, int]:
    """How many downloads under a container are finished, and how many are
    still coming. What a container's context menu offers is decided from
    these two numbers — a failed row counts as neither, because the menu's
    answer to it is Download, same as for an item nobody ever asked for."""
    states = container_states(container_id)
    return {
        "done": sum(1 for state in states.values() if state == DONE),
        "pending": sum(1 for state in states.values() if state in (QUEUED, ACTIVE)),
    }


def container_done_ids(container_id: str) -> list[str]:
    """The finished downloads under a container — what "Remove download" on
    a show or an album actually removes."""
    return sorted(
        item_id
        for item_id, state in container_states(container_id).items()
        if state == DONE
    )


def container_pending_ids(container_id: str) -> list[str]:
    """The unfinished downloads under a container — what "Cancel download"
    on a show or an album actually cancels."""
    return sorted(
        item_id
        for item_id, state in container_states(container_id).items()
        if state in (QUEUED, ACTIVE)
    )


def has_subscription_claim(item_id: str) -> bool:
    """Whether any standing music order still needs this local song."""
    with Database("kofin") as opened:
        opened.cursor.execute(
            "SELECT 1 FROM download_subscription WHERE jellyfin_id = ? LIMIT 1",
            (item_id,),
        )
        return opened.cursor.fetchone() is not None


def playlist_unclaimed_states(playlist_id: str) -> dict[str, str]:
    """Downloads requested from this playlist that no subscription still claims."""
    return music_container_unclaimed_states(playlist_id, "playlist")


def music_container_unclaimed_states(container_id: str, kind: str) -> dict[str, str]:
    """Music request's downloads that remain safe to remove or cancel."""
    with Database("kofin") as opened:
        opened.cursor.execute(
            "SELECT d.jellyfin_id, d.state FROM download d "
            "WHERE (d.request_id = ? OR d.origin = ?) "
            "AND NOT EXISTS (SELECT 1 FROM download_subscription s "
            "WHERE s.jellyfin_id = d.jellyfin_id)",
            (container_id, "auto:%s:%s" % (kind, container_id)),
        )
        return dict(opened.cursor.fetchall())


def claim(media_types: Optional[Sequence[str]] = None) -> Optional[Download]:
    """Move the oldest queued row to active and return it; None when idle.

    Race-safe across worker threads without RETURNING (the deployed SQLite
    floor is not ours to raise): each candidate is taken with a guarded
    UPDATE, and a loser's zero rowcount just moves it to the next candidate.

    ``media_types`` scopes a worker pool to its own kind. An empty
    ``media_type`` matches only a caller that names "" among its kinds.
    """
    kinds = list(media_types) if media_types is not None else None
    if kinds is not None and not kinds:
        return None
    where = " WHERE state = ?"
    params: list[Any] = [QUEUED]
    if kinds is not None:
        clause = "media_type IN (%s)" % ", ".join("?" for _ in kinds)
        params.extend(kinds)
        if "" in kinds:
            # NULL is unknown too, and `IN` never matches it.
            clause = "(%s OR media_type IS NULL)" % clause
        where += " AND " + clause
    while True:
        with Database("kofin") as opened:
            opened.cursor.execute(
                _SELECT + where + " ORDER BY queued_at, jellyfin_id LIMIT 1",
                tuple(params),
            )
            row = opened.cursor.fetchone()
            if row is None:
                return None
            candidate = _row_to_download(row)
            opened.cursor.execute(
                "UPDATE download SET state = ? WHERE jellyfin_id = ? AND state = ?",
                (ACTIVE, candidate.jellyfin_id, QUEUED),
            )
            if opened.cursor.rowcount == 1:
                candidate.state = ACTIVE
                return candidate
        # Another worker claimed it between the SELECT and the UPDATE.


def record_progress(jellyfin_id: str, bytes_done: int) -> None:
    with Database("kofin") as opened:
        opened.cursor.execute(
            "UPDATE download SET bytes_done = ? WHERE jellyfin_id = ?",
            (int(bytes_done), jellyfin_id),
        )


def finish(
    jellyfin_id: str,
    rel_path: str,
    container: str,
    size_actual: int,
    done_at: int = 0,
) -> None:
    with Database("kofin") as opened:
        opened.cursor.execute(
            "UPDATE download SET state = ?, rel_path = ?, container = ?, "
            "size_actual = ?, bytes_done = ?, done_at = ?, error = '' "
            "WHERE jellyfin_id = ?",
            (
                DONE,
                rel_path,
                container,
                int(size_actual),
                int(size_actual),
                done_at or int(time.time()),
                jellyfin_id,
            ),
        )


def record_target(jellyfin_id: str, rel_path: str, container: str) -> None:
    """Freeze the target path the moment it is first known, so a retry or a
    restart resumes the same ``.part`` instead of re-deciding the name."""
    with Database("kofin") as opened:
        opened.cursor.execute(
            "UPDATE download SET rel_path = ?, container = ? WHERE jellyfin_id = ?",
            (rel_path, container, jellyfin_id),
        )


def record_validator(jellyfin_id: str, validator: str) -> None:
    with Database("kofin") as opened:
        opened.cursor.execute(
            "UPDATE download SET validator = ? WHERE jellyfin_id = ?",
            (validator, jellyfin_id),
        )


def record_details(
    jellyfin_id: str,
    media_type: str,
    series_id: str,
    size_expected: int,
    userdata_json: str,
    quality: str = QUALITY_ORIGINAL,
) -> None:
    """Fill what only the item DTO knows, at download time: the queue path
    carries bare ids across the IPC bus, and the worker holds the DTO (and
    the quality decision, made against the same fetch)."""
    with Database("kofin") as opened:
        opened.cursor.execute(
            "UPDATE download SET media_type = ?, series_id = ?, "
            "size_expected = ?, userdata_json = ?, quality = ? "
            "WHERE jellyfin_id = ?",
            (
                media_type,
                series_id,
                int(size_expected),
                userdata_json,
                quality,
                jellyfin_id,
            ),
        )


def set_segments(jellyfin_id: str, raw_json: str) -> None:
    with Database("kofin") as opened:
        opened.cursor.execute(
            "UPDATE download SET segments_json = ? WHERE jellyfin_id = ?",
            (raw_json, jellyfin_id),
        )


def release(jellyfin_id: str) -> None:
    """Put an active row back to queued without spending an attempt;
    ``queued_at`` stays, so the row heads the queue for the reconnect."""
    with Database("kofin") as opened:
        opened.cursor.execute(
            "UPDATE download SET state = ? WHERE jellyfin_id = ? AND state = ?",
            (QUEUED, jellyfin_id, ACTIVE),
        )


def fail(jellyfin_id: str, error: str) -> None:
    with Database("kofin") as opened:
        opened.cursor.execute(
            "UPDATE download SET state = ?, error = ? WHERE jellyfin_id = ?",
            (FAILED, str(error)[:500], jellyfin_id),
        )


def remove(jellyfin_id: str) -> None:
    with Database("kofin") as opened:
        opened.cursor.execute(
            "DELETE FROM download WHERE jellyfin_id = ?", (jellyfin_id,)
        )


def rows(state: Optional[str] = None) -> list[Download]:
    with Database("kofin") as opened:
        if state is None:
            opened.cursor.execute(_SELECT + " ORDER BY queued_at, jellyfin_id")
        else:
            opened.cursor.execute(
                _SELECT + " WHERE state = ? ORDER BY queued_at, jellyfin_id",
                (state,),
            )
        fetched = opened.cursor.fetchall()
    return [_row_to_download(row) for row in fetched]


def targets_under(directory: str) -> list[tuple[str, str]]:
    """``(jellyfin_id, rel_path)`` of every row whose target is somewhere
    under ``directory``. LIKE matches ASCII letters in either case."""
    escaped = directory.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    with Database("kofin") as opened:
        opened.cursor.execute(
            "SELECT jellyfin_id, rel_path FROM download "
            "WHERE rel_path LIKE ? ESCAPE '\\'",
            (escaped + "/%",),
        )
        return [(str(found[0]), str(found[1])) for found in opened.cursor.fetchall()]


def is_done(jellyfin_id: str) -> bool:
    row = get(jellyfin_id)
    return row is not None and row.state == DONE


def pending_count() -> int:
    """Queued + active rows — what the progress bar calls the remainder."""
    with Database("kofin") as opened:
        opened.cursor.execute(
            "SELECT COUNT(*) FROM download WHERE state IN (?, ?)",
            (QUEUED, ACTIVE),
        )
        return int(opened.cursor.fetchone()[0])


def recover_interrupted() -> int:
    """Re-queue rows a crash left active; returns how many. Manager start.

    ``bytes_done`` survives, so a recovered original resumes with a Range
    rather than starting over; the manager deletes stale ``.part`` files for
    transcodes itself (they are not byte-stable across attempts).
    """
    with Database("kofin") as opened:
        opened.cursor.execute(
            "UPDATE download SET state = ? WHERE state = ?", (QUEUED, ACTIVE)
        )
        moved = opened.cursor.rowcount
    if moved:
        LOG.debug("re-queued %d interrupted download(s)", moved)
    return int(moved)
