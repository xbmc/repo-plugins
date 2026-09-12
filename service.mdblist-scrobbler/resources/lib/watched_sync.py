import datetime

import xbmc

from resources.lib import library_snapshot, mdblist_api, sync_payload, sync_state
from resources.lib.utils import jsonrpc_request, local_time_to_utc_iso, utc_iso_to_local_time

CATEGORY = "watched"


def _now_iso():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _to_api_datetime(value):
    # Kodi's lastplayed is naive local time; MDBList expects UTC.
    return local_time_to_utc_iso(value)


def _remote_ts_normalized(value):
    if not value:
        return None
    return value.replace(" ", "T")[:19]


# --- push: Kodi -> MDBList -----------------------------------------------

def _movie_item(movie):
    return {"type": "movie", "ids": movie["ids"], "watched_at": _to_api_datetime(movie["lastplayed"])}


def _episode_item(episode):
    return {
        "type": "episode", "show_ids": episode["show_ids"],
        "season": episode["season"], "episode": episode["episode"],
        "watched_at": _to_api_datetime(episode["lastplayed"]),
    }


def _canonical_key(record):
    if record["dbtype"] == "movie":
        return library_snapshot.canonical_movie_key(record["ids"])
    return library_snapshot.canonical_episode_key(record["show_ids"], record["season"], record["episode"])


def _current_watched_items(snapshot):
    items = {}
    for movie in library_snapshot.iter_movies(snapshot):
        if movie["playcount"] > 0:
            key = library_snapshot.canonical_movie_key(movie["ids"])
            if key:
                items[key] = _movie_item(movie)
    for episode in library_snapshot.iter_episodes(snapshot):
        if episode["playcount"] > 0:
            key = library_snapshot.canonical_episode_key(episode["show_ids"], episode["season"], episode["episode"])
            if key:
                items[key] = _episode_item(episode)
    return items


def _push_add(items):
    sync_payload.push_items(CATEGORY, "/sync/watched", "watched_at", items)


def _push_remove(items):
    sync_payload.push_items_remove(CATEGORY, "/sync/watched/remove", items)


def _watched_at_changed(known_item, item):
    return known_item.get("watched_at") != item.get("watched_at")


def push(snapshot, allow_remove=False):
    """Membership diff, plus a value-changed check on watched_at so a rewatch
    that only updates lastplayed (membership unchanged) is still re-pushed by
    the full diff, not just by the live push from /scrobble/stop.

    allow_remove: see sync_payload.diff_and_reconcile."""
    current = _current_watched_items(snapshot)
    return sync_payload.diff_and_reconcile(
        CATEGORY, current, _push_add, _push_remove, value_changed=_watched_at_changed, allow_remove=allow_remove,
    )


def push_single(record):
    """Immediate push for one item, triggered by a live VideoLibrary.OnUpdate
    notification (Kodi's native "mark as watched"/"mark as unwatched", not
    just our own scrobble flow). _push_add/_push_remove persist sync_state
    for this one item as part of pushing it -- see
    sync_payload.push_items/push_items_remove.

    Returns False only when the item genuinely couldn't be pushed (no id this
    addon can map to a provider). Returns {} for "nothing to do, already in
    sync" and a populated dict when something was actually pushed -- see
    ratings_sync.push_single, same contract, fixed for the same reason."""
    key = _canonical_key(record)
    if not key:
        return False

    known_item = sync_state.get_known_items(CATEGORY).get(key)
    is_watched = record["playcount"] > 0

    if is_watched:
        item = _movie_item(record) if record["dbtype"] == "movie" else _episode_item(record)
        if known_item and known_item.get("watched_at") == item.get("watched_at"):
            return {}
        _push_add([item])
        return {"pushed_add": 1}

    if not known_item:
        return {}
    _push_remove([known_item])
    return {"pushed_remove": 1}


# --- pull: MDBList -> Kodi -------------------------------------------------

def _set_watched(record, playcount, lastplayed=None):
    # Only send lastplayed when we have a real value -- e.g. on removal this
    # leaves it untouched, matching Kodi's own "mark unwatched" behavior
    # rather than forcing an empty/invalid date onto the library row.
    params = {"playcount": playcount}
    if lastplayed:
        params["lastplayed"] = lastplayed
    if record["dbtype"] == "movie":
        jsonrpc_request("VideoLibrary.SetMovieDetails", dict(params, movieid=record["dbid"]))
    else:
        jsonrpc_request("VideoLibrary.SetEpisodeDetails", dict(params, episodeid=record["dbid"]))


def _apply_watched(record, status, remote_at):
    """Last-write-wins using Kodi's lastplayed vs the remote timestamp -- the
    one sync category where Kodi actually tracks a comparable local
    timestamp, so real conflict resolution (not just remote-wins) applies.
    Both sides are normalized to UTC before comparing -- Kodi's lastplayed is
    naive local time, MDBList's timestamps are UTC, so comparing the raw
    strings would be off by the device's UTC offset.

    An exact tie (same second on both sides) is resolved the same way in
    both branches below -- remote wins -- for one consistent tie-break rule
    rather than local winning on removal but losing on activation."""
    local_ts = local_time_to_utc_iso(record.get("lastplayed"))
    remote_ts = _remote_ts_normalized(remote_at)

    if status == "removed":
        if record["playcount"] <= 0:
            return False
        if local_ts and remote_ts and local_ts > remote_ts:
            return False
        _set_watched(record, playcount=0)
        return True

    if record["playcount"] > 0 and local_ts and remote_ts and local_ts > remote_ts:
        return False

    new_lastplayed = utc_iso_to_local_time(remote_at) or record.get("lastplayed")
    _set_watched(record, playcount=max(record["playcount"], 1), lastplayed=new_lastplayed)
    return True


def _apply_movie_entry(snapshot, ids, status, remote_at):
    """Returns (applied, canonical_key) -- the key (None if no local match)
    lets _pull_full track which locally-watched items the remote list
    actually mentioned, to reconcile removals for the rest."""
    match = library_snapshot.find_movie_match(snapshot, ids)
    if not match:
        return False, None
    return _apply_watched(match, status, remote_at), library_snapshot.canonical_movie_key(match["ids"])


def _apply_episode_entry(snapshot, show_ids, season, episode, status, remote_at, episode_ids=None):
    match = library_snapshot.find_episode_match(snapshot, show_ids, season, episode, episode_ids)
    if not match:
        xbmc.log(
            "MDBList Sync: watched pull found no local match for show tmdb={} imdb={} tvdb={} S{}E{} "
            "episodeTmdb={} episodeTvdb={}".format(
                show_ids.get("tmdb"), show_ids.get("imdb"), show_ids.get("tvdb"), season, episode,
                (episode_ids or {}).get("tmdb"), (episode_ids or {}).get("tvdb"),
            ),
            level=xbmc.LOGDEBUG,
        )
        return False, None
    key = library_snapshot.canonical_episode_key(match["show_ids"], match["season"], match["episode"])
    return _apply_watched(match, status, remote_at), key


def _pull_full(snapshot, server_time, trusted=False):
    # extended=None (full, not ids_only): ids_only only exposes a movie's
    # tmdb id (and an episode's parent show's tmdb id). A local item
    # identified only by imdb/tvdb/trakt/mdblist couldn't be matched or ruled
    # out below with that alone, and the removal-reconciliation loop needs to
    # tell "not remotely watched" apart from "couldn't check" -- full mode
    # gives every provider id.
    data = mdblist_api.fetch_sync_items("/sync/watched", extended=None)
    xbmc.log(
        "MDBList Sync: watched full pull fetched {} movies, {} episodes from MDBList".format(
            len(data.get("movies", [])), len(data.get("episodes", []))
        ),
        level=xbmc.LOGDEBUG,
    )

    applied = 0
    matched_keys = set()

    for entry in data.get("movies", []):
        ids = (entry.get("movie") or {}).get("ids") or {}
        if not ids:
            continue
        applied_ok, key = _apply_movie_entry(snapshot, ids, "active", entry.get("last_watched_at"))
        if key:
            matched_keys.add(key)
        if applied_ok:
            applied += 1

    for entry in data.get("episodes", []):
        episode = entry.get("episode") or {}
        show_ids = (episode.get("show") or {}).get("ids") or {}
        if not show_ids:
            continue
        applied_ok, key = _apply_episode_entry(
            snapshot, show_ids, episode.get("season"), episode.get("number"),
            "active", entry.get("last_watched_at"), episode.get("ids"),
        )
        if key:
            matched_keys.add(key)
        if applied_ok:
            applied += 1

    # The full list above is authoritative: anything locally watched but not
    # in it was unwatched remotely -- this is the fallback for when the
    # journal's 30-day retention window has lapsed, so there's no incremental
    # removal feed to rely on instead.
    #
    # This is the same "known minus current-read = remove" shape
    # diff_and_reconcile guards against on push, just mirrored to the
    # opposite direction: a successful-but-degraded /sync/watched response
    # would otherwise read as "everything was unwatched remotely" and wipe
    # local state. Same three guards (trust, empty-vs-threshold, magnitude),
    # same constants -- see removal_safety_pattern.md.
    locally_watched = []
    for movie in library_snapshot.iter_movies(snapshot):
        if movie["playcount"] > 0:
            key = library_snapshot.canonical_movie_key(movie["ids"])
            if key:
                locally_watched.append((movie, key))
    for episode in library_snapshot.iter_episodes(snapshot):
        if episode["playcount"] > 0:
            key = library_snapshot.canonical_episode_key(episode["show_ids"], episode["season"], episode["episode"])
            if key:
                locally_watched.append((episode, key))

    candidate_removals = [(record, key) for record, key in locally_watched if key not in matched_keys]
    remote_count = len(data.get("movies", [])) + len(data.get("episodes", []))
    hold_removals = bool(candidate_removals) and _should_hold_pull_removals(
        remote_count, len(candidate_removals), len(locally_watched), trusted
    )

    if candidate_removals and not hold_removals:
        # The removal timestamp is the server-provided watermark, not "now":
        # if the item was genuinely rewatched between when the server
        # generated this snapshot and now, its local timestamp needs to be
        # newer than server_time (not a later client-side "now") to
        # correctly win the conflict-resolution check in _apply_watched.
        removal_at = server_time or _now_iso()
        for record, _key in candidate_removals:
            if _apply_watched(record, "removed", removal_at):
                applied += 1

    if hold_removals:
        # Held, not dropped -- don't advance the watermark either, so the
        # next pull retries a full reconcile from scratch (and, per pull(),
        # keeps landing back here) instead of downgrading to the incremental
        # journal path and never revisiting these items.
        return {"pulled_applied": applied, "mode": "full", "skipped_remove": len(candidate_removals)}

    sync_state.set_synced_at(CATEGORY, server_time or _now_iso())
    return {"pulled_applied": applied, "mode": "full"}


def _should_hold_pull_removals(remote_count, candidate_count, known_count, trusted):
    """Same shape as sync_payload.diff_and_reconcile's removal guard, applied
    to the pull-direction full reconcile: held when the trigger isn't trusted
    for removals, when a totally-empty remote read sits next to a known-watched
    baseline bigger than the threshold, or when the removal batch itself is
    larger than max(REMOVAL_MIN_BATCH, known_count * REMOVAL_MAX_FRACTION).
    The empty-read check is tied to the threshold rather than an absolute
    veto, same reasoning as diff_and_reconcile -- a user whose whole watched
    library is smaller than the threshold must still be able to clear it
    completely on a trusted run."""
    threshold = max(sync_payload.REMOVAL_MIN_BATCH, int(known_count * sync_payload.REMOVAL_MAX_FRACTION))

    if not trusted:
        xbmc.log(
            "MDBList Sync: watched pull removal held ({} items) - this trigger doesn't allow removals".format(
                candidate_count
            ),
            level=xbmc.LOGDEBUG,
        )
        return True

    if remote_count == 0 and known_count > threshold:
        xbmc.log(
            "MDBList Sync: watched pull removal held - remote full list came back empty while {} items are "
            "locally watched (threshold {}); treating as an unreliable read rather than a real removal".format(
                known_count, threshold
            ),
            level=xbmc.LOGWARNING,
        )
        return True

    if candidate_count > threshold:
        xbmc.log(
            "MDBList Sync: watched pull removal held - {} of {} locally watched items would be unwatched "
            "(threshold {}); remote read may be incomplete".format(candidate_count, known_count, threshold),
            level=xbmc.LOGWARNING,
        )
        return True

    return False


def _pull_incremental(snapshot, entries, server_time):
    applied = 0
    skipped_type = 0
    for entry in entries:
        if entry.get("category") != "watched":
            continue

        ids = entry.get("ids") or {}
        status = entry.get("status")
        # value_at is the actual watched timestamp and is what conflict
        # resolution must compare against -- but it's only ever set on
        # add/active rows; a removal row has no "value" to speak of and
        # only carries action_at (confirmed against api.mdblist's
        # _remove_movies/_remove_shows/etc., which write the journal row
        # with action_at but no value_at at all). Falling back to action_at
        # there keeps last-write-wins working for removals instead of
        # silently skipping the conflict check.
        remote_at = entry.get("value_at") or entry.get("action_at")

        if entry.get("item_type") == "movie":
            applied_ok, _key = _apply_movie_entry(snapshot, ids, status, remote_at)
            if applied_ok:
                applied += 1
        elif entry.get("item_type") == "episode":
            episode_ids = library_snapshot.journal_episode_ids(entry)
            applied_ok, _key = _apply_episode_entry(
                snapshot, ids, entry.get("season"), entry.get("episode"), status, remote_at, episode_ids,
            )
            if applied_ok:
                applied += 1
        else:
            # show/season-level rows have no directly writable Kodi field; skipped
            skipped_type += 1

    if skipped_type:
        xbmc.log(
            "MDBList Sync: watched incremental pull skipped {} journal entries with unhandled item type".format(
                skipped_type
            ),
            level=xbmc.LOGDEBUG,
        )

    sync_state.set_synced_at(CATEGORY, server_time or _now_iso())
    return {"pulled_applied": applied, "mode": "incremental"}


def pull(snapshot, server_time, trusted=False):
    """server_time: /sync/last_activities' own server_time -- a
    safety-margined timestamp meant to be persisted as the next watermark,
    rather than the device's own clock, which can drift and under-cover the
    next incremental window.

    trusted: forwarded to _pull_full's removal reconcile -- see
    _should_hold_pull_removals and removal_safety_pattern.md's Trusted Runs
    section. Defaults to False so a call site that forgets to think about it
    stays safe; only run()'s allow_remove (24h backstop, manual "Sync now")
    should pass True. _pull_incremental doesn't need this: it applies
    explicit per-item journal events, not a "known minus current-read"
    diff, so it isn't the failure mode this pattern guards against."""
    since = sync_state.get_synced_at(CATEGORY)
    if not since:
        xbmc.log("MDBList Sync: watched pull has no cursor - running full pull", level=xbmc.LOGDEBUG)
        return _pull_full(snapshot, server_time, trusted)

    journal = mdblist_api.fetch_journal(since=since)
    if journal.get("requires_full_sync"):
        xbmc.log(
            "MDBList Sync: watched pull cursor {} is outside journal retention - running full pull".format(since),
            level=xbmc.LOGDEBUG,
        )
        return _pull_full(snapshot, server_time, trusted)

    entries = journal.get("entries", [])
    xbmc.log(
        "MDBList Sync: watched pull cursor {} - running incremental pull ({} journal entries)".format(
            since, len(entries)
        ),
        level=xbmc.LOGDEBUG,
    )
    return _pull_incremental(snapshot, entries, server_time)
