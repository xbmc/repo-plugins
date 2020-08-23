from future import standard_library
standard_library.install_aliases()  # noqa: E402

from resources.lib.f1.api import Api
from resources.lib.kodi.items import Items
from resources.lib.kodi.settings import Settings
from resources.routes import *
import sys
import urllib.parse
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo("id")
addon_base = "plugin://" + addon_id
settings = Settings(addon)
api = Api(settings)
listItems = Items(addon, addon_base)


def run():
    url = urllib.parse.urlparse(sys.argv[0])
    path = url.path
    handle = int(sys.argv[1])
    args = urllib.parse.parse_qs(sys.argv[2][1:])
    xbmcplugin.setContent(handle, "videos")

    if path == PATH_ROOT:
        action = args.get("action", None)
        if action is None:
            items = listItems.root()
            xbmcplugin.addDirectoryItems(handle, items, len(items))
            xbmcplugin.endOfDirectory(handle)
        elif "call" in action:
            collection = listItems.from_collection(api.call(args.get("call")[0]))
            xbmcplugin.addDirectoryItems(handle, collection, len(collection))
            xbmcplugin.endOfDirectory(handle)
        elif "editorial" in action:
            collection = listItems.from_collection(api.video_editorial())
            xbmcplugin.addDirectoryItems(handle, collection, len(collection))
            xbmcplugin.endOfDirectory(handle)
        elif "settings" in action:
            addon.openSettings()
        else:
            xbmc.log("Invalid root action", xbmc.LOGERROR)

    elif path == PATH_VIDEOS:
        collection = listItems.from_collection(api.video_editorial())
        xbmcplugin.addDirectoryItems(handle, collection, len(collection))
        xbmcplugin.endOfDirectory(handle)

    elif path == PATH_STANDINGS:
        action = args.get("action", None)
        if action is None:
            items = listItems.standings()
            xbmcplugin.addDirectoryItems(handle, items, len(items))
            xbmcplugin.endOfDirectory(handle)
        elif "drivers" in action:
            items = listItems.from_collection(api.standings(Api.api_path_drivers))
            xbmcplugin.addDirectoryItems(handle, items, len(items))
            xbmcplugin.endOfDirectory(handle)
        elif "constructors" in action:
            items = listItems.from_collection(api.standings(Api.api_path_constructors))
            xbmcplugin.addDirectoryItems(handle, items, len(items))
            xbmcplugin.endOfDirectory(handle)
        elif "results" in action:
            items = listItems.from_collection(api.standings(Api.api_path_results))
            xbmcplugin.addDirectoryItems(handle, items, len(items))
            xbmcplugin.endOfDirectory(handle)
        else:
            xbmc.log("Invalid standings action", xbmc.LOGERROR)

    elif path == PATH_RACING:
        items = listItems.from_collection(api.standings(Api.api_path_events))
        xbmcplugin.addDirectoryItems(handle, items, len(items))
        xbmcplugin.endOfDirectory(handle)

    elif path == PATH_PLAY:
        embed_code = args.get("embed_code", [None])[0]
        if embed_code:
            resolved_url = api.resolve_embed_code(embed_code)
            item = xbmcgui.ListItem(path=resolved_url)
            xbmcplugin.setResolvedUrl(handle, succeeded=True, listitem=item)
        else:
            xbmc.log("Invalid play param", xbmc.LOGERROR)

    else:
        xbmc.log("Path not found", xbmc.LOGERROR)
