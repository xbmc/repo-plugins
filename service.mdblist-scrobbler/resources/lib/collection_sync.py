from resources.lib import library_snapshot, sync_payload
from resources.lib.utils import local_time_to_utc_iso

CATEGORY = "collection"

# Kodi -> MDBList only: this reflects what's actually in the local library so
# MDBList's collected status is accurate. There is deliberately no pull
# direction -- Kodi can't materialize a file just because MDBList thinks it's
# collected, so a remote-only "collected" flag has nothing local to apply.


def _to_api_datetime(value):
    # Kodi's dateadded is naive local time; MDBList expects UTC.
    return local_time_to_utc_iso(value)


def _current_collected_items(snapshot):
    items = {}
    for movie in library_snapshot.iter_movies(snapshot):
        if movie["file"]:
            key = library_snapshot.canonical_movie_key(movie["ids"])
            if key:
                items[key] = {
                    "type": "movie", "ids": movie["ids"],
                    "collected_at": _to_api_datetime(movie["dateadded"]),
                }
    for episode in library_snapshot.iter_episodes(snapshot):
        if episode["file"]:
            key = library_snapshot.canonical_episode_key(episode["show_ids"], episode["season"], episode["episode"])
            if key:
                items[key] = {
                    "type": "episode", "show_ids": episode["show_ids"],
                    "season": episode["season"], "episode": episode["episode"],
                    "collected_at": _to_api_datetime(episode["dateadded"]),
                }
    return items


def _push_add(items):
    sync_payload.push_items(CATEGORY, "/sync/collection", "collected_at", items)


def _push_remove(items):
    sync_payload.push_items_remove(CATEGORY, "/sync/collection/remove", items)


def push(snapshot, allow_remove=False):
    """Push + reconcile: anything newly present in the Kodi library is added,
    anything that dropped out (file removed/library item deleted) since the
    last run is removed from MDBList's collection -- the "clean collection"
    step, mirroring script.trakt's collection sync.

    allow_remove: see sync_payload.diff_and_reconcile. Collection sync has no
    pull direction (see the module note above), so a wrongly-pushed removal
    here has no remote-to-local self-healing path at all."""
    current = _current_collected_items(snapshot)
    return sync_payload.diff_and_reconcile(CATEGORY, current, _push_add, _push_remove, allow_remove=allow_remove)
