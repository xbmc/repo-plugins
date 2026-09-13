from collections import OrderedDict

import xbmc

from resources.lib import library_snapshot, mdblist_api, sync_state

BATCH_SIZE = 100

# Magnitude circuit-breaker on removals -- see diff_and_reconcile. Fixed, not
# user-configurable: there's a single correct answer here, not a per-user
# preference.
REMOVAL_MAX_FRACTION = 0.30
REMOVAL_MIN_BATCH = 15  # trip threshold = max(this, known_count * REMOVAL_MAX_FRACTION)


def build_shows_payload(episode_entries):
    """Group flat (show_ids, season, episode, extra_fields) tuples into the
    nested {"ids", "seasons": [{"number", "episodes": [{"number", **extra}]}]}
    shape every /sync/* endpoint (watched, ratings, collection) expects for
    episodes -- confirmed against api.mdblist's resolve_show_payload, which
    every one of those POST handlers routes through."""
    shows_by_key = OrderedDict()

    for show_ids, season, episode, extra in episode_entries:
        key = tuple(sorted(show_ids.items()))
        show = shows_by_key.setdefault(key, {"ids": show_ids, "seasons": OrderedDict()})
        entries = show["seasons"].setdefault(season, [])
        entry = {"number": episode}
        entry.update(extra)
        entries.append(entry)

    return [
        {
            "ids": show["ids"],
            "seasons": [
                {"number": season_number, "episodes": episodes}
                for season_number, episodes in show["seasons"].items()
            ],
        }
        for show in shows_by_key.values()
    ]


def chunked(items, size=100):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def _canonical_key_of(item):
    if item.get("type") == "movie":
        return library_snapshot.canonical_movie_key(item.get("ids") or {})
    return library_snapshot.canonical_episode_key(item.get("show_ids") or {}, item.get("season"), item.get("episode"))


def _persist_pushed_chunk(category, chunk):
    upserts = {}
    for item in chunk:
        key = _canonical_key_of(item)
        if key:
            upserts[key] = item
    if upserts:
        sync_state.merge_known_items(category, upserts)


def _persist_removed_chunk(category, chunk):
    removed_keys = [key for key in (_canonical_key_of(item) for item in chunk) if key]
    if removed_keys:
        sync_state.merge_known_items(category, {}, removed_keys)


def push_items(category, endpoint, field_name, items):
    """Shared push body for watched_sync/ratings_sync/collection_sync's
    _push_add: split by type, set `field_name` (watched_at/rating/
    collected_at) on each, chunk, POST to `endpoint`. The three call sites
    were previously identical modulo that field name and endpoint string.
    Persists each chunk's known-items state immediately after it pushes
    successfully, so a later chunk's failure (e.g. hitting the write rate
    limit) doesn't undo already-pushed progress."""
    movie_items = [item for item in items if item["type"] == "movie"]
    for batch in chunked(movie_items, BATCH_SIZE):
        payload = [{"ids": item["ids"], field_name: item[field_name]} for item in batch]
        mdblist_api.push_sync_items(endpoint, {"movies": payload})
        _persist_pushed_chunk(category, batch)

    episode_items = [item for item in items if item["type"] == "episode"]
    for batch in chunked(episode_items, BATCH_SIZE):
        entries = [(item["show_ids"], item["season"], item["episode"], {field_name: item[field_name]}) for item in batch]
        mdblist_api.push_sync_items(endpoint, {"shows": build_shows_payload(entries)})
        _persist_pushed_chunk(category, batch)


def push_items_remove(category, endpoint, items):
    """Shared push body for the three modules' _push_remove -- identity only,
    no value field. Persists each chunk's removal immediately after it
    pushes successfully -- see push_items."""
    movie_items = [item for item in items if item["type"] == "movie"]
    for batch in chunked(movie_items, BATCH_SIZE):
        payload = [{"ids": item["ids"]} for item in batch]
        mdblist_api.push_sync_items(endpoint, {"movies": payload})
        _persist_removed_chunk(category, batch)

    episode_items = [item for item in items if item["type"] == "episode"]
    for batch in chunked(episode_items, BATCH_SIZE):
        entries = [(item["show_ids"], item["season"], item["episode"], {}) for item in batch]
        mdblist_api.push_sync_items(endpoint, {"shows": build_shows_payload(entries)})
        _persist_removed_chunk(category, batch)


def diff_and_reconcile(category, current_items, push_add, push_remove, value_changed=None, allow_remove=False):
    """Shared push+reconcile skeleton used by watched_sync/ratings_sync/
    collection_sync's push(): diff `current_items` (key -> item) against
    sync_state's known_items for `category`, call push_add(items)/
    push_remove(items) for the deltas, and return a summary dict.

    `value_changed(known_item, item)` -- optional -- adds an item to to_add
    even when its key is already known, if the value differs. Only
    ratings_sync needs this: a rating can change without membership changing,
    unlike watched/collection, which are membership-only (a rewatch/re-add
    with the same value doesn't need a fresh push).

    `allow_remove` gates whether this call may push removals at all --
    defaults to False so a call site that forgets to think about it stays
    safe; only the deliberate periodic timer and manual "Sync now" pass True
    (see main_monitor.py). Even when True, a removal batch larger than
    max(REMOVAL_MIN_BATCH, known_count * REMOVAL_MAX_FRACTION) is skipped
    and logged rather than pushed -- and, ahead of that check, a totally-empty
    current_items next to a known baseline bigger than that same threshold is
    always skipped regardless of batch size. Tied to the threshold rather
    than an absolute veto so a user with a small category can still clear it
    completely on a trusted run -- see removal_safety_pattern.md's "Core
    Rule". This exists because a diff-based "clean" reconcile with no floor
    once wiped a real user's entire remote collection when their local Kodi
    library briefly (and wrongly) read back near-empty. A skipped batch isn't
    persisted anywhere -- it's simply re-diffed from scratch next run, so
    once the local library reads back correctly the very next qualifying run
    pushes it normally.

    push_add/push_remove are expected to persist each pushed chunk's
    known-items state as they go (see push_items/push_items_remove above),
    not just report success at the end -- so a chunk that fails partway
    through only leaves the unpushed remainder to retry next time."""
    known = sync_state.get_known_items(category)

    if value_changed:
        to_add = [item for key, item in current_items.items() if key not in known or value_changed(known[key], item)]
    else:
        to_add = [item for key, item in current_items.items() if key not in known]
    to_remove = [item for key, item in known.items() if key not in current_items]

    if to_add:
        push_add(to_add)

    pushed_remove = 0
    skipped_remove = 0
    if to_remove:
        threshold = max(REMOVAL_MIN_BATCH, int(len(known) * REMOVAL_MAX_FRACTION))
        if not allow_remove:
            # Routine, not suspicious -- this call site's trigger (scan/clean
            # finished, service start) simply never removes, by policy.
            skipped_remove = len(to_remove)
            xbmc.log(
                "MDBList Sync: {} removal skipped ({} items) - this trigger doesn't allow removals".format(
                    category, len(to_remove)
                ),
                level=xbmc.LOGDEBUG,
            )
        elif not current_items and len(known) > threshold:
            # Extra guard ahead of the magnitude check below, tied to the
            # same threshold rather than an absolute veto: a totally-empty
            # current read next to a known baseline bigger than the
            # threshold is never a real mass unwatch/unrate/uncollect, but a
            # user whose whole category is smaller than the threshold must
            # still be able to clear it completely on a trusted run -- see
            # removal_safety_pattern.md. Same handling as an RPC failure:
            # hold every known item and re-diff fresh next run.
            skipped_remove = len(to_remove)
            xbmc.log(
                "MDBList Sync: {} removal skipped - current_items read is empty while {} known items are on "
                "file (threshold {}); treating as an unreliable read rather than a real removal".format(
                    category, len(known), threshold
                ),
                level=xbmc.LOGWARNING,
            )
        elif len(to_remove) > threshold:
            # The circuit breaker actually tripped -- this is the
            # notable case, worth a louder log level.
            skipped_remove = len(to_remove)
            xbmc.log(
                "MDBList Sync: {} removal skipped - {} of {} known items would be removed (threshold {}); "
                "local Kodi library may be incomplete".format(category, len(to_remove), len(known), threshold),
                level=xbmc.LOGWARNING,
            )
        else:
            push_remove(to_remove)
            pushed_remove = len(to_remove)

    return {"pushed_add": len(to_add), "pushed_remove": pushed_remove, "skipped_remove": skipped_remove}
