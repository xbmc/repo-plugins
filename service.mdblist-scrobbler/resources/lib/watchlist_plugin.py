import json
import sys
import urllib.parse

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

from resources.lib.mdblist_api import MDBListApiError, fetch_watchlist, modify_watchlist
from resources.lib.utils import fix_unique_ids, jsonrpc_request


def addon():
    return xbmcaddon.Addon()


def bool_setting(setting_id):
    try:
        return addon().getSettings().getBool(setting_id)
    except Exception:
        return addon().getSetting(setting_id).lower() == "true"


def notify(message, error=False):
    icon = xbmcgui.NOTIFICATION_ERROR if error else xbmcgui.NOTIFICATION_INFO
    xbmcgui.Dialog().notification("MDBList Watchlist", message, icon, 3500)


def plugin_url(params):
    return "{}?{}".format(sys.argv[0], urllib.parse.urlencode(params))


def parse_query():
    if len(sys.argv) < 3 or not sys.argv[2]:
        return {}
    return dict(urllib.parse.parse_qsl(sys.argv[2].lstrip("?")))


def watchlist_item_ids(item):
    ids = item.get("ids")
    if isinstance(ids, dict) and ids:
        return {key: value for key, value in ids.items() if value not in (None, "")}

    ids = {
        "mdblist": item.get("mdblist_id") or item.get("public_id"),
        "imdb": item.get("imdb_id") or item.get("imdbid"),
        "tmdb": item.get("tmdb_id") or item.get("tmdbid"),
        "tvdb": item.get("tvdb_id") or item.get("tvdbid"),
        "trakt": item.get("trakt_id") or item.get("traktid"),
    }
    return {key: value for key, value in ids.items() if value not in (None, "")}


def build_library_index(mediatype):
    if mediatype == "movie":
        result = jsonrpc_request(
            "VideoLibrary.GetMovies",
            {"properties": ["title", "year", "uniqueid", "thumbnail", "fanart", "file"]},
        )
        items = result.get("movies", [])
        id_key = "movieid"
    else:
        result = jsonrpc_request(
            "VideoLibrary.GetTVShows",
            {"properties": ["title", "year", "uniqueid", "thumbnail", "fanart"]},
        )
        items = result.get("tvshows", [])
        id_key = "tvshowid"

    index = {}
    for item in items or []:
        ids = fix_unique_ids(item.get("uniqueid", {}), mediatype)
        for key, value in ids.items():
            index["{}:{}".format(key, str(value))] = {
                "id": item.get(id_key),
                "title": item.get("title"),
                "year": item.get("year"),
                "thumbnail": item.get("thumbnail"),
                "fanart": item.get("fanart"),
                "file": item.get("file"),
            }
    return index


def find_library_match(item, library_index):
    ids = watchlist_item_ids(item)
    for key in ("mdblist", "imdb", "tmdb", "tvdb", "trakt"):
        value = ids.get(key)
        if value in (None, ""):
            continue
        match = library_index.get("{}:{}".format(key, str(value)))
        if match:
            return match
    return None


def item_art(item, match):
    art = {}
    poster = item.get("poster") or item.get("poster_path")
    if poster:
        art["poster"] = poster
        art["thumb"] = poster
        art["icon"] = poster
    if match:
        if match.get("thumbnail"):
            art.setdefault("thumb", match["thumbnail"])
            art.setdefault("icon", match["thumbnail"])
        if match.get("fanart"):
            art["fanart"] = match["fanart"]
    return art


def library_url(mediatype, match):
    if not match:
        return plugin_url({"action": "metadata"})
    if mediatype == "movie":
        return match.get("file") or "videodb://movies/titles/{}/".format(match["id"])
    return "videodb://tvshows/titles/{}/".format(match["id"])


def make_video_item(item, mediatype, match):
    title = item.get("title") or "Untitled"
    year = item.get("release_year") or item.get("year")
    label = "{} ({})".format(title, year) if year else title
    if not match:
        label = "{} [Not in library]".format(label)

    list_item = xbmcgui.ListItem(label=label)
    list_item.setArt(item_art(item, match))
    list_item.setProperty("IsPlayable", "true" if mediatype == "movie" and match else "false")

    info = {
        "title": title,
        "year": int(year) if str(year).isdigit() else 0,
        "mediatype": "movie" if mediatype == "movie" else "tvshow",
    }
    list_item.setInfo("video", info)

    ids = watchlist_item_ids(item)
    context_url = plugin_url({
        "action": "remove",
        "mediatype": mediatype,
        "ids": json.dumps(ids),
    })
    list_item.addContextMenuItems([
        ("Remove from MDBList Watchlist", "RunPlugin({})".format(context_url)),
    ])

    return library_url(mediatype, match), list_item, mediatype == "show" and bool(match)


def add_directory(label, params):
    list_item = xbmcgui.ListItem(label=label)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), plugin_url(params), list_item, isFolder=True)


def show_root():
    if not bool_setting("watchlist.enabled"):
        item = xbmcgui.ListItem(label="MDBList watchlist is disabled")
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), plugin_url({"action": "metadata"}), item, isFolder=False)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        return

    add_directory("Movies", {"action": "list", "mediatype": "movie"})
    add_directory("Shows", {"action": "list", "mediatype": "show"})
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def show_watchlist(mediatype):
    xbmcplugin.setContent(int(sys.argv[1]), "movies" if mediatype == "movie" else "tvshows")

    data = fetch_watchlist(mediatype)
    items = data.get("movies" if mediatype == "movie" else "shows") or []
    library_index = build_library_index(mediatype)

    for item in items:
        match = find_library_match(item, library_index)
        url, list_item, is_folder = make_video_item(item, mediatype, match)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, list_item, isFolder=is_folder)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def remove_item(query):
    try:
        ids = json.loads(query.get("ids", "{}"))
    except ValueError:
        ids = {}

    if not ids:
        notify("No supported IDs found", error=True)
        return

    modify_watchlist("remove", query.get("mediatype"), ids)
    notify("Removed from MDBList watchlist")
    xbmc.executebuiltin("Container.Refresh")


def run():
    query = parse_query()
    action = query.get("action", "root")

    try:
        if action == "root":
            show_root()
        elif action == "list":
            show_watchlist(query.get("mediatype"))
        elif action == "remove":
            remove_item(query)
        elif action == "metadata":
            notify("This item is not in your Kodi library")
        else:
            show_root()
    except MDBListApiError as exception:
        xbmc.log("MDBList Watchlist: {}".format(exception), level=xbmc.LOGERROR)
        notify(str(exception)[:80], error=True)
        xbmcplugin.endOfDirectory(int(sys.argv[1]), succeeded=False)
    except Exception as exception:
        xbmc.log("MDBList Watchlist: unexpected error - {}".format(exception), level=xbmc.LOGERROR)
        notify("Watchlist error: {}".format(str(exception)[:60]), error=True)
        xbmcplugin.endOfDirectory(int(sys.argv[1]), succeeded=False)
