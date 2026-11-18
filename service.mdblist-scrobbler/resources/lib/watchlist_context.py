import os
import sys

import xbmc
import xbmcaddon
import xbmcgui

_addon_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _addon_root not in sys.path:
    sys.path.insert(0, _addon_root)

from resources.lib.mdblist_api import MDBListApiError, modify_watchlist
from resources.lib.utils import fix_unique_ids, jsonrpc_request


def notify(message, error=False):
    icon = xbmcgui.NOTIFICATION_ERROR if error else xbmcgui.NOTIFICATION_INFO
    xbmcgui.Dialog().notification("MDBList Watchlist", message, icon, 3500)


def bool_setting(setting_id):
    addon = xbmcaddon.Addon()
    try:
        return addon.getSettings().getBool(setting_id)
    except Exception:
        return addon.getSetting(setting_id).lower() == "true"


def selected_dbtype():
    dbtype = xbmc.getInfoLabel("ListItem.DBTYPE") or xbmc.getInfoLabel("ListItem.DBType")
    return dbtype.lower()


def selected_dbid():
    try:
        return int(xbmc.getInfoLabel("ListItem.DBID"))
    except (TypeError, ValueError):
        return None


def selected_title(dbtype):
    if dbtype == "episode":
        return (
            xbmc.getInfoLabel("ListItem.TVShowTitle")
            or xbmc.getInfoLabel("ListItem.ShowTitle")
            or xbmc.getInfoLabel("ListItem.Title")
        )
    return xbmc.getInfoLabel("ListItem.Title")


def selected_infolabel_ids(media_type):
    unique_ids = {}
    for key, labels in (
        ("imdbnumber", ("ListItem.IMDBNumber",)),
        ("tmdb_id", ("ListItem.Property(tmdb_id)", "ListItem.Property(TmdbId)")),
        ("tvdb_id", ("ListItem.Property(tvdb_id)", "ListItem.Property(TvdbId)")),
    ):
        for label in labels:
            value = xbmc.getInfoLabel(label)
            if value:
                unique_ids[key] = value
                break

    return fix_unique_ids(unique_ids, media_type)


def selected_item_ids():
    dbtype = selected_dbtype()
    dbid = selected_dbid()

    if dbtype == "movie" and dbid:
        details = jsonrpc_request(
            "VideoLibrary.GetMovieDetails",
            {"movieid": dbid, "properties": ["title", "uniqueid"]},
        ).get("moviedetails", {})
        return "movie", details.get("title"), fix_unique_ids(details.get("uniqueid", {}), "movie")

    if dbtype == "tvshow" and dbid:
        details = jsonrpc_request(
            "VideoLibrary.GetTVShowDetails",
            {"tvshowid": dbid, "properties": ["title", "uniqueid"]},
        ).get("tvshowdetails", {})
        return "show", details.get("title"), fix_unique_ids(details.get("uniqueid", {}), "show")

    if dbtype == "episode" and dbid:
        episode = jsonrpc_request(
            "VideoLibrary.GetEpisodeDetails",
            {"episodeid": dbid, "properties": ["showtitle", "tvshowid"]},
        ).get("episodedetails", {})
        tvshowid = episode.get("tvshowid")
        if tvshowid:
            show = jsonrpc_request(
                "VideoLibrary.GetTVShowDetails",
                {"tvshowid": tvshowid, "properties": ["title", "uniqueid"]},
            ).get("tvshowdetails", {})
            return "show", show.get("title") or episode.get("showtitle"), fix_unique_ids(show.get("uniqueid", {}), "show")

    if dbtype in ("movie", "tvshow", "episode"):
        mediatype = "movie" if dbtype == "movie" else "show"
        ids = selected_infolabel_ids(mediatype)
        if ids:
            return mediatype, selected_title(dbtype), ids

    return None, None, {}


def run():
    action = "add"
    for arg in sys.argv[1:]:
        if arg in ("add", "remove"):
            action = arg

    if not bool_setting("watchlist.enabled"):
        notify("MDBList watchlist is disabled")
        return

    try:
        mediatype, title, ids = selected_item_ids()
        if not mediatype or not ids:
            notify("No supported IDs found for this item", error=True)
            return

        modify_watchlist(action, mediatype, ids)
    except MDBListApiError as exception:
        notify(str(exception)[:80], error=True)
        return
    except Exception as exception:
        # Broad fallback matches watchlist_plugin.py's pattern, covering
        # jsonrpc_request's JSONRPCError among other things -- keeps a Kodi
        # query failure a graceful notification rather than an uncaught
        # exception with no user-facing message.
        xbmc.log("MDBList Watchlist: unexpected error - {}".format(exception), level=xbmc.LOGERROR)
        notify("Watchlist error: {}".format(str(exception)[:60]), error=True)
        return

    verb = "Added to" if action == "add" else "Removed from"
    notify("{} MDBList watchlist: {}".format(verb, title or "item"))


if __name__ == "__main__":
    run()
