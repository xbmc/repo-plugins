from resources.lib.soundcloud.api_v2 import ApiV2
from resources.lib.kodi.cache import Cache
from resources.lib.kodi.items import Items
from resources.lib.kodi.search_history import SearchHistory
from resources.lib.kodi.settings import Settings
from resources.lib.kodi.vfs import VFS
from resources.routes import *
import os
import sys
import urllib.parse
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo("id")
addon_base = "plugin://" + addon_id
addon_profile_path = xbmcvfs.translatePath(addon.getAddonInfo("profile"))
vfs = VFS(addon_profile_path)
vfs_cache = VFS(os.path.join(addon_profile_path, "cache"))
settings = Settings(addon)
cache = Cache(settings, vfs_cache)
api = ApiV2(settings, xbmc.getLanguage(xbmc.ISO_639_1), cache)
search_history = SearchHistory(settings, vfs)
listItems = Items(addon, addon_base, search_history)


def run():
    url = urllib.parse.urlparse(sys.argv[0])
    path = url.path
    handle = int(sys.argv[1])
    args = urllib.parse.parse_qs(sys.argv[2][1:])
    xbmcplugin.setContent(handle, "songs")

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
        elif "settings" in action:
            addon.openSettings()
        else:
            xbmc.log(addon_id + ": Invalid root action", xbmc.LOGERROR)

    elif path == PATH_CHARTS:
        action = args.get("action", [None])[0]
        genre = args.get("genre", ["soundcloud:genres:all-music"])[0]
        if action is None:
            items = listItems.charts()
            xbmcplugin.addDirectoryItems(handle, items, len(items))
            xbmcplugin.endOfDirectory(handle)
        else:
            api_result = api.charts({"kind": action, "genre": genre, "limit": 50})
            collection = listItems.from_collection(api_result)
            xbmcplugin.addDirectoryItems(handle, collection, len(collection))
            xbmcplugin.endOfDirectory(handle)

    elif path == PATH_DISCOVER:
        selection = args.get("selection", [None])[0]
        collection = listItems.from_collection(api.discover(selection))
        xbmcplugin.addDirectoryItems(handle, collection, len(collection))
        xbmcplugin.endOfDirectory(handle)

    elif path == PATH_PLAY:
        # Public params
        track_id = args.get("track_id", [None])[0]
        playlist_id = args.get("playlist_id", [None])[0]
        url = args.get("url", [None])[0]

        # Public legacy params (@deprecated)
        audio_id_legacy = args.get("audio_id", [None])[0]
        track_id = audio_id_legacy if audio_id_legacy else track_id

        # Private params
        media_url = args.get("media_url", [None])[0]

        if media_url:
            resolved_url = api.resolve_media_url(media_url)
            item = xbmcgui.ListItem(path=resolved_url)
            xbmcplugin.setResolvedUrl(handle, succeeded=True, listitem=item)
        elif track_id:
            collection = listItems.from_collection(api.resolve_id(track_id))
            playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
            resolve_list_item(handle, collection[0][1])
            playlist.add(url=collection[0][0], listitem=collection[0][1])
        elif playlist_id:
            call = "/playlists/{id}".format(id=playlist_id)
            collection = listItems.from_collection(api.call(call))
            playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
            for item in collection:
                resolve_list_item(handle, item[1])
                playlist.add(url=item[0], listitem=item[1])
        elif url:
            collection = listItems.from_collection(api.resolve_url(url))
            playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
            for item in collection:
                resolve_list_item(handle, item[1])
                playlist.add(url=item[0], listitem=item[1])
        else:
            xbmc.log(addon_id + ": Invalid play param", xbmc.LOGERROR)

    elif path == PATH_SEARCH:
        action = args.get("action", None)
        query = args.get("query", [""])[0]

        if action and "remove" in action:
            search_history.remove(query)
            xbmc.executebuiltin("Container.Refresh")
        elif action and "clear" in action:
            search_history.clear()
            xbmc.executebuiltin("Container.Refresh")

        if query:
            if action is None:
                search(handle, query)
            elif "people" in action:
                xbmcplugin.setContent(handle, "artists")
                collection = listItems.from_collection(api.search(query, "users"))
                xbmcplugin.addDirectoryItems(handle, collection, len(collection))
                xbmcplugin.endOfDirectory(handle)
            elif "albums" in action:
                xbmcplugin.setContent(handle, "albums")
                collection = listItems.from_collection(api.search(query, "albums"))
                xbmcplugin.addDirectoryItems(handle, collection, len(collection))
                xbmcplugin.endOfDirectory(handle)
            elif "playlists" in action:
                xbmcplugin.setContent(handle, "albums")
                collection = listItems.from_collection(
                    api.search(query, "playlists_without_albums")
                )
                xbmcplugin.addDirectoryItems(handle, collection, len(collection))
                xbmcplugin.endOfDirectory(handle)
            else:
                xbmc.log(addon_id + ": Invalid search action", xbmc.LOGERROR)
        else:
            if action is None:
                items = listItems.search()
                xbmcplugin.addDirectoryItems(handle, items, len(items))
                xbmcplugin.endOfDirectory(handle)
            elif "new" in action:
                query = xbmcgui.Dialog().input(addon.getLocalizedString(30101))
                search_history.add(query)
                search(handle, query)
            else:
                xbmc.log(addon_id + ": Invalid search action", xbmc.LOGERROR)

    # Legacy search query used by Chorus2 (@deprecated)
    elif path == PATH_SEARCH_LEGACY:
        query = args.get("q", [""])[0]
        collection = listItems.from_collection(api.search(query))
        xbmcplugin.addDirectoryItems(handle, collection, len(collection))
        xbmcplugin.endOfDirectory(handle)

    elif path == PATH_USER:
        user_id = args.get("id")[0]
        default_action = args.get("call")[0]
        if user_id:
            items = listItems.user(user_id)
            collection = listItems.from_collection(api.call(default_action))
            xbmcplugin.addDirectoryItems(handle, items, len(items))
            xbmcplugin.addDirectoryItems(handle, collection, len(collection))
            xbmcplugin.endOfDirectory(handle)
        else:
            xbmc.log(addon_id + ": Invalid user action", xbmc.LOGERROR)

    elif path == PATH_SETTINGS_CACHE_CLEAR:
        vfs_cache.destroy()
        dialog = xbmcgui.Dialog()
        dialog.ok("SoundCloud", addon.getLocalizedString(30501))

    else:
        xbmc.log(addon_id + ": Path not found", xbmc.LOGERROR)


def resolve_list_item(handle, list_item):
    resolved_url = api.resolve_media_url(list_item.getProperty("mediaUrl"))
    list_item.setPath(resolved_url)
    xbmcplugin.setResolvedUrl(handle, succeeded=True, listitem=list_item)


def search(handle, query):
    search_options = listItems.search_sub(query)
    collection = listItems.from_collection(api.search(query))
    xbmcplugin.addDirectoryItems(handle, search_options, len(collection))
    xbmcplugin.addDirectoryItems(handle, collection, len(collection))
    xbmcplugin.endOfDirectory(handle)
