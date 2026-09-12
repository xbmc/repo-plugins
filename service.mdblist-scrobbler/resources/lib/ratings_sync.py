import datetime

import xbmc

from resources.lib import library_snapshot, mdblist_api, sync_payload, sync_state
from resources.lib.utils import jsonrpc_request

CATEGORY = "ratings"
JOURNAL_CATEGORY = "rated"


def _now_iso():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


# --- push: Kodi -> MDBList -----------------------------------------------

def _movie_item(movie):
    return {"type": "movie", "ids": movie["ids"], "rating": movie["userrating"]}


def _episode_item(episode):
    return {
        "type": "episode", "show_ids": episode["show_ids"],
        "season": episode["season"], "episode": episode["episode"],
        "rating": episode["userrating"],
    }


def _canonical_key(record):
    if record["dbtype"] == "movie":
        return library_snapshot.canonical_movie_key(record["ids"])
    return library_snapshot.canonical_episode_key(record["show_ids"], record["season"], record["episode"])


def _current_rated_items(snapshot):
    items = {}
    for movie in library_snapshot.iter_movies(snapshot):
        if movie["userrating"] > 0:
            key = library_snapshot.canonical_movie_key(movie["ids"])
            if key:
                items[key] = _movie_item(movie)
    for episode in library_snapshot.iter_episodes(snapshot):
        if episode["userrating"] > 0:
            key = library_snapshot.canonical_episode_key(episode["show_ids"], episode["season"], episode["episode"])
            if key:
                items[key] = _episode_item(episode)
    return items


def _push_add(items):
    sync_payload.push_items(CATEGORY, "/sync/ratings", "rating", items)


def _push_remove(items):
    sync_payload.push_items_remove(CATEGORY, "/sync/ratings/remove", items)


def _rating_changed(known_item, item):
    return known_item.get("rating") != item.get("rating")


def push(snapshot, allow_remove=False):
    """allow_remove: see sync_payload.diff_and_reconcile."""
    current = _current_rated_items(snapshot)
    return sync_payload.diff_and_reconcile(
        CATEGORY, current, _push_add, _push_remove, value_changed=_rating_changed, allow_remove=allow_remove,
    )


def push_single(record):
    """Immediate push for one item -- see watched_sync.push_single. Used both
    by the live VideoLibrary.OnUpdate listener (Kodi's native rate dialog) and
    by player_monitor's own rating-prompt flow, so the two don't duplicate
    payload-building logic or double-push the same rating.

    Returns False only when the item genuinely couldn't be pushed (no id this
    addon can map to a provider -- e.g. an anime movie with only a kitsu id).
    Returns {} for "nothing to do, already in sync" and a populated dict when
    something was actually pushed -- callers must not treat every non-False
    result as "pushed" (confirmed bug: player_monitor.save_mdblist_rating
    used to report success even when this returned None for the unmapped-id
    case, with no distinction from the harmless already-in-sync no-op)."""
    key = _canonical_key(record)
    if not key:
        return False

    known_item = sync_state.get_known_items(CATEGORY).get(key)
    rating = record["userrating"]

    if rating > 0:
        item = _movie_item(record) if record["dbtype"] == "movie" else _episode_item(record)
        if known_item and known_item.get("rating") == rating:
            return {}
        _push_add([item])
        return {"pushed_add": 1}

    if not known_item:
        return {}
    _push_remove([known_item])
    return {"pushed_remove": 1}


# --- pull: MDBList -> Kodi ---------------------------------------------------
# No local "rated at" timestamp exists in Kodi, so unlike watched status this
# is not true last-write-wins: push() always runs first (see sync_orchestrator),
# so on the first sync any conflicting item is already resolved local-wins by
# the time pull happens. After that, pull only ever applies items that changed
# remotely since our own last sync watermark, which keeps the collision window
# to "rated locally and remotely in between two sync runs" -- acceptable given
# Kodi has nothing to compare against.

def _set_rating(record, rating):
    params = {"userrating": rating}
    if record["dbtype"] == "movie":
        jsonrpc_request("VideoLibrary.SetMovieDetails", dict(params, movieid=record["dbid"]))
    else:
        jsonrpc_request("VideoLibrary.SetEpisodeDetails", dict(params, episodeid=record["dbid"]))


def _apply_movie_rating(snapshot, ids, rating):
    match = library_snapshot.find_movie_match(snapshot, ids)
    if not match or match["userrating"] == rating:
        return False
    _set_rating(match, rating)
    return True


def _apply_episode_rating(snapshot, show_ids, season, episode, rating, episode_ids=None):
    match = library_snapshot.find_episode_match(snapshot, show_ids, season, episode, episode_ids)
    if not match or match["userrating"] == rating:
        return False
    _set_rating(match, rating)
    return True


def _pull_full(snapshot, server_time):
    # extended=None (full, not ids_only) -- MDBList's ids_only ratings response
    # only carries the episode's own tmdb id, not season/episode/show, so it
    # can't be matched against the Kodi library the way ids_only works for /sync/watched.
    data = mdblist_api.fetch_sync_items("/sync/ratings", extended=None)
    xbmc.log(
        "MDBList Sync: ratings full pull fetched {} movies, {} episodes from MDBList".format(
            len(data.get("movies", [])), len(data.get("episodes", []))
        ),
        level=xbmc.LOGDEBUG,
    )

    applied = 0

    for entry in data.get("movies", []):
        ids = (entry.get("movie") or {}).get("ids") or {}
        if ids and _apply_movie_rating(snapshot, ids, entry.get("rating") or 0):
            applied += 1

    for entry in data.get("episodes", []):
        episode = entry.get("episode") or {}
        show_ids = (episode.get("show") or {}).get("ids") or {}
        if show_ids and _apply_episode_rating(
            snapshot, show_ids, episode.get("season"), episode.get("number"), entry.get("rating") or 0,
            episode.get("ids"),
        ):
            applied += 1

    sync_state.set_synced_at(CATEGORY, server_time or _now_iso())
    return {"pulled_applied": applied, "mode": "full"}


def _pull_incremental(snapshot, entries, server_time):
    applied = 0
    skipped_type = 0
    for entry in entries:
        if entry.get("category") != JOURNAL_CATEGORY:
            continue

        ids = entry.get("ids") or {}
        rating = entry.get("rating") or 0 if entry.get("status") != "removed" else 0

        if entry.get("item_type") == "movie":
            if _apply_movie_rating(snapshot, ids, rating):
                applied += 1
        elif entry.get("item_type") == "episode":
            episode_ids = library_snapshot.journal_episode_ids(entry)
            if _apply_episode_rating(snapshot, ids, entry.get("season"), entry.get("episode"), rating, episode_ids):
                applied += 1
        else:
            skipped_type += 1

    if skipped_type:
        xbmc.log(
            "MDBList Sync: ratings incremental pull skipped {} journal entries with unhandled item type".format(
                skipped_type
            ),
            level=xbmc.LOGDEBUG,
        )

    sync_state.set_synced_at(CATEGORY, server_time or _now_iso())
    return {"pulled_applied": applied, "mode": "incremental"}


def pull(snapshot, server_time):
    """server_time: see watched_sync.pull -- a server-provided watermark,
    not the client's own clock."""
    since = sync_state.get_synced_at(CATEGORY)
    if not since:
        xbmc.log("MDBList Sync: ratings pull has no cursor - running full pull", level=xbmc.LOGDEBUG)
        return _pull_full(snapshot, server_time)

    journal = mdblist_api.fetch_journal(since=since)
    if journal.get("requires_full_sync"):
        xbmc.log(
            "MDBList Sync: ratings pull cursor {} is outside journal retention - running full pull".format(since),
            level=xbmc.LOGDEBUG,
        )
        return _pull_full(snapshot, server_time)

    entries = journal.get("entries", [])
    xbmc.log(
        "MDBList Sync: ratings pull cursor {} - running incremental pull ({} journal entries)".format(
            since, len(entries)
        ),
        level=xbmc.LOGDEBUG,
    )
    return _pull_incremental(snapshot, entries, server_time)
