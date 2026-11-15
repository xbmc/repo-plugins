"""Continue watching as listed: the account's positions, and those gone from it while still on catch-up."""

import os
import time

from resources.lib import kodiutil
from resources.lib.data import guidedata
from resources.lib.util import atomicfile
from resources.lib.util import isotime

# The rows listed before, kept until their programme leaves catch-up: {position id: {"mark", "removed"}}.
# The provider's list drops a position once watched to its end (its apps cannot remove one), and this
# add-on's reset deletes it there: kept here, such a row stays, greyed out (see rows).
KEPT = os.path.join(kodiutil.PROFILE, "continue.json")
# The longest a programme stays on catch-up after it ended: how long a greyed row is kept at most.
# Not when a row's programme leaves catch-up: that varies by channel (Mozi+ HD: under four days, seen
# 2026-11-02) and the provider says it nowhere but in the programme's airings (see on_catchup).
CATCHUP_SECONDS = 7 * 86400
# How long a programme stays on catch-up after it ended, as measured: Mozi+ HD, 2026-11-15 (one that
# ended 11:25Z on 11-12 played at 11:18Z on 11-15 and was refused at 11:55Z). Other channels fit it
# but were not measured this close: the rows' order and their "N days left" are estimates by it.
EXPECTED_CATCHUP_SECONDS = 72 * 3600
# What a row is: being watched (resumable), watched to its end, or its position reset here.
ACTIVE, WATCHED, REMOVED = "active", "watched", "removed"


def available_until(mark):
    """Return the latest a position's programme can leave catch-up (a timestamp); None if its id has no times."""
    ended = _ended(mark)
    return None if ended is None else ended + CATCHUP_SECONDS


def expected_until(mark):
    """Return when a position's programme is expected to leave catch-up (see EXPECTED_CATCHUP_SECONDS); None if unknown."""
    ended = _ended(mark)
    return None if ended is None else ended + EXPECTED_CATCHUP_SECONDS


def seconds_left(mark, now=None):
    """Return the seconds until a position's programme is expected to leave catch-up (below 0: past it); None if unknown."""
    until = expected_until(mark)
    return None if until is None else until - (time.time() if now is None else now)


def catchup(marks):
    """Return the catch-up positions of the account's (see client.bookmarks): those with an id of times."""
    return [m for m in marks if m.get("bookmark_type", "Catchup") == "Catchup" and guidedata.from_bookmark_id(m.get("id"))]


def rows(marks, now=None):
    """Return the rows to list as [(mark, state)]: the account's positions first, in its order, then the greyed ones.

    A position in the account's list is ACTIVE, however far it got; one gone from it is WATCHED unless
    reset here (REMOVED). Rows whose programme left catch-up are dropped, here and from KEPT.
    The active ones first, then the greyed ones, each the soonest to leave catch-up first (see expected_until).

    :param marks: the account's catch-up positions (see catchup)
    """
    now = time.time() if now is None else now
    kept = _load()
    listed = {mark["id"]: mark for mark in marks if (available_until(mark) or 0) > now}
    out = [(mark, ACTIVE) for mark in listed.values()]
    fresh = {mark_id: {"mark": mark, "removed": False} for mark_id, mark in listed.items()}
    for mark_id, entry in kept.items():
        if mark_id not in listed and (available_until(entry["mark"]) or 0) > now:
            fresh[mark_id] = entry
            out.append((entry["mark"], REMOVED if entry.get("removed") else WATCHED))
    if fresh != kept:
        _save(fresh)
    # The active ones first, then the greyed ones; each the soonest to leave catch-up first (stable for equal ones).
    return sorted(out, key=lambda row: (row[1] != ACTIVE, expected_until(row[0]) or 0))


def on_catchup(mark, airings):
    """Return whether a position's airing is among its programme's catch-up airings (see client.airings).

    :param airings: the programme's catch-up airings, each with station_id and start_utc
    """
    station, start, _ = guidedata.from_bookmark_id(mark.get("id")) or (None, None, None)
    return any(str(a.get("station_id")) == station and a.get("start_utc") == start for a in airings)


def find(station, start, marks):
    """Return the row of an airing (its station, its start "...Z"): the account's position or a greyed row; None if none.

    :param marks: the account's catch-up positions (see client.bookmarks)
    """
    kept = [entry["mark"] for entry in _load().values()]
    return next((m for m in list(marks) + kept if (guidedata.from_bookmark_id(m.get("id")) or ())[:2] == (station, start)), None)


def drop(mark_id):
    """Forget a row kept here: listed no more once the account has no position for it either."""
    kept = _load()
    if kept.pop(mark_id, None) is not None:
        _save(kept)


def set_removed(mark):
    """Keep a position reset here (deleted from the account's list) as REMOVED."""
    kept = _load()
    kept[mark["id"]] = {"mark": (kept.get(mark["id"]) or {}).get("mark") or mark, "removed": True}
    _save(kept)


def _ended(mark):
    """Return when a position's programme ended (a timestamp); None if its id has no times."""
    marked = guidedata.from_bookmark_id(mark.get("id"))
    if not marked:
        return None
    try:
        return isotime.stamp(marked[2])
    except ValueError:
        return None


def _load():
    return atomicfile.read_json(KEPT, {})


def _save(kept):
    atomicfile.write_json(KEPT, kept)
