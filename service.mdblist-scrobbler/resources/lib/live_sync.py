import xbmc
import xbmcaddon

from resources.lib import ratings_sync, sync_orchestrator, watched_sync
from resources.lib.mdblist_api import MDBListApiError
from resources.lib.utils import fix_unique_ids, jsonrpc_request


def _bool_setting(setting_id, default=False):
    try:
        return xbmcaddon.Addon().getSettings().getBool(setting_id)
    except Exception:
        return default


def _movie_record(dbid):
    details = jsonrpc_request(
        "VideoLibrary.GetMovieDetails",
        {"movieid": dbid, "properties": ["uniqueid", "playcount", "lastplayed", "userrating"]},
    ).get("moviedetails")
    if not details:
        return None

    ids = fix_unique_ids(details.get("uniqueid", {}), "movie")
    if not ids:
        return None

    return {
        "dbtype": "movie", "ids": ids,
        "playcount": details.get("playcount") or 0,
        "lastplayed": details.get("lastplayed") or None,
        "userrating": details.get("userrating") or 0,
    }


def _episode_record(dbid):
    details = jsonrpc_request(
        "VideoLibrary.GetEpisodeDetails",
        {"episodeid": dbid, "properties": ["season", "episode", "tvshowid", "playcount", "lastplayed", "userrating"]},
    ).get("episodedetails")
    if not details or not details.get("tvshowid"):
        return None

    show = jsonrpc_request(
        "VideoLibrary.GetTVShowDetails",
        {"tvshowid": details["tvshowid"], "properties": ["uniqueid"]},
    ).get("tvshowdetails") or {}
    show_ids = fix_unique_ids(show.get("uniqueid", {}), "show")
    if not show_ids:
        return None

    return {
        "dbtype": "episode", "show_ids": show_ids,
        "season": details.get("season"), "episode": details.get("episode"),
        "playcount": details.get("playcount") or 0,
        "lastplayed": details.get("lastplayed") or None,
        "userrating": details.get("userrating") or 0,
    }


def handle_library_update(dbtype, dbid):
    """Called from MainMonitor.onNotification for VideoLibrary.OnUpdate --
    fires for any change to a library item's playcount/lastplayed/userrating,
    regardless of what caused it (our own scrobble/rating-prompt flow, Kodi's
    native "mark as watched"/rate dialog, another addon). Pushes just that one
    item instead of waiting for the next full sync run."""
    watched_enabled = _bool_setting("sync.watched.enabled")
    ratings_enabled = _bool_setting("sync.ratings.enabled")
    if not (watched_enabled or ratings_enabled):
        return

    with sync_orchestrator.try_lock() as acquired:
        if not acquired:
            # A run()/check_activity()/check_ratings_local() is in progress --
            # very likely applying remote state to this same item, so skip
            # rather than echo it straight back. Held for this whole block,
            # not just checked once, so a sync that starts mid-operation is
            # caught too, not just one already running at entry.
            return

        record = _movie_record(dbid) if dbtype == "movie" else _episode_record(dbid)
        if not record:
            return

        try:
            if watched_enabled:
                watched_sync.push_single(record)
            if ratings_enabled:
                ratings_sync.push_single(record)
        except MDBListApiError as exception:
            xbmc.log("MDBList Sync: live push failed - {}".format(exception), level=xbmc.LOGDEBUG)
