import os
import sys
import urllib.parse
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

from resources.lib.api import Api, PasswordRequiredException, WrongPasswordException
from resources.lib.kodi.cache import Cache
from resources.lib.kodi.items import Items
from resources.lib.kodi.search_history import SearchHistory
from resources.lib.kodi.settings import Settings
from resources.lib.kodi.utils import format_bold
from resources.lib.kodi.vfs import VFS
from resources.routes import *

addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo("id")
addon_base = "plugin://" + addon_id
addon_profile_path = xbmcvfs.translatePath(addon.getAddonInfo("profile"))

vfs = VFS(addon_profile_path)
vfs_cache = VFS(os.path.join(addon_profile_path, "cache/"))
settings = Settings(addon)
cache = Cache(settings, vfs_cache)
api = Api(settings, xbmc.getLanguage(xbmc.ISO_639_1), (vfs, vfs_cache), cache)
search_history = SearchHistory(settings, vfs)
listItems = Items(addon, addon_base, settings, search_history, vfs)


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
        elif "settings" in action:
            addon.openSettings()
        else:
            xbmc.log(addon_id + ": Invalid root action", xbmc.LOGERROR)

    elif path == PATH_CATEGORIES:
        collection = listItems.from_collection(api.categories())
        xbmcplugin.addDirectoryItems(handle, collection, len(collection))
        xbmcplugin.endOfDirectory(handle)

    elif path == PATH_TRENDING:
        collection = listItems.from_collection(api.trending())
        xbmcplugin.addDirectoryItems(handle, collection, len(collection))
        xbmcplugin.endOfDirectory(handle)

    elif path == PATH_FEATURED:
        action = args.get("action", None)
        if action is None:
            items = listItems.featured()
            xbmcplugin.addDirectoryItems(handle, items, len(items))
            xbmcplugin.endOfDirectory(handle)
        elif "channel" in action:
            channel_id = args.get("id", [""])[0]
            collection = listItems.from_collection(api.channel(channel_id))
            xbmcplugin.addDirectoryItems(handle, collection, len(collection))
            xbmcplugin.endOfDirectory(handle)
        else:
            xbmc.log(addon_id + ": Invalid featured action", xbmc.LOGERROR)

    elif path == PATH_PLAY:
        # Public params
        video_id = args.get("video_id", [None])[0]

        # Private params
        media_url = args.get("uri", [None])[0]
        texttracks = args.get("texttracks", [False])[0]

        # Settings
        fetch_subtitles = True if settings.get("video.subtitles") == "true" else False

        if media_url:
            resolved_url = api.resolve_media_url(media_url)
            item = xbmcgui.ListItem(path=resolved_url)
            if fetch_subtitles and texttracks:
                item = add_subtitles(item, texttracks)
            xbmcplugin.setResolvedUrl(handle, succeeded=True, listitem=item)
        elif video_id:
            try:
                password = None
                collection = listItems.from_collection(api.resolve_id(video_id, password))
            except PasswordRequiredException:
                try:
                    password = xbmcgui.Dialog().input(addon.getLocalizedString(30904))
                    collection = listItems.from_collection(api.resolve_id(video_id, password))
                except WrongPasswordException:
                    return xbmcgui.Dialog().notification(
                        addon.getLocalizedString(30905),
                        addon.getLocalizedString(30906),
                        xbmcgui.NOTIFICATION_ERROR
                    )

            playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            resolve_list_item(handle, collection[0][1], password, fetch_subtitles)
            playlist.add(url=collection[0][0], listitem=collection[0][1])
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
            elif "channels" in action:
                xbmcplugin.setContent(handle, "albums")
                collection = listItems.from_collection(api.search(query, "channels"))
                xbmcplugin.addDirectoryItems(handle, collection, len(collection))
                xbmcplugin.endOfDirectory(handle)
            elif "groups" in action:
                xbmcplugin.setContent(handle, "albums")
                collection = listItems.from_collection(api.search(query, "groups"))
                xbmcplugin.addDirectoryItems(handle, collection, len(collection))
                xbmcplugin.endOfDirectory(handle)
            else:
                xbmc.log(addon_id + ": Invalid search action", xbmc.LOGERROR)
        else:
            if action is None:
                # Search root
                items = listItems.search()
                xbmcplugin.addDirectoryItems(handle, items, len(items))
                xbmcplugin.endOfDirectory(handle)
            elif "new" in action:
                # New search
                query = xbmcgui.Dialog().input(addon.getLocalizedString(30101))
                search_history.add(query)
                search(handle, query)
            else:
                xbmc.log(addon_id + ": Invalid search action", xbmc.LOGERROR)

    elif path == PATH_AUTH_LOGIN:
        logout()  # Make sure there is no cached access-token

        device_code_response = api.oauth_device()
        activate_link = device_code_response["activate_link"]
        device_code = device_code_response["device_code"]
        user_code = device_code_response["user_code"]
        xbmcgui.Dialog().ok(
            heading=addon.getLocalizedString(30151),
            message="{}\n{}\n{}\n{}".format(
                addon.getLocalizedString(30152).format(format_bold(activate_link)),
                addon.getLocalizedString(30153).format(format_bold(user_code)),
                addon.getLocalizedString(30154).format(format_bold(user_code)),
                addon.getLocalizedString(30155).format(format_bold("OK")),
            ),
        )

        user_name = api.oauth_device_authorize(user_code, device_code)
        xbmcgui.Dialog().ok(
            heading=addon.getLocalizedString(30151),
            message=addon.getLocalizedString(30156).format(user_name),
        )
        xbmc.executebuiltin("Container.Refresh")

    elif path == PATH_AUTH_LOGOUT:
        logout()
        xbmc.executebuiltin("Container.Refresh")

    elif path == PATH_PROFILE:
        uri = args.get("uri", [""])[0]

        if uri:
            user = api.user(uri)
            profile_options = listItems.profile_sub(user)
            collection = listItems.from_collection(api.call("{}/videos".format(uri)))
            xbmcplugin.addDirectoryItems(handle, profile_options)
            xbmcplugin.addDirectoryItems(handle, collection, len(collection))
            xbmcplugin.endOfDirectory(handle)
        else:
            xbmc.log(addon_id + ": Invalid profile uri", xbmc.LOGERROR)

    elif path == PATH_SETTINGS_CACHE_CLEAR:
        vfs_cache.destroy()
        xbmcgui.Dialog().ok("Vimeo", addon.getLocalizedString(30501))

    else:
        xbmc.log(addon_id + ": Path not found", xbmc.LOGERROR)


def resolve_list_item(handle, list_item, password=None, fetch_subtitles=False):
    resolved_url = api.resolve_media_url(list_item.getProperty("mediaUrl"), password)
    list_item.setPath(resolved_url)
    text_tracks = list_item.getProperty("textTracks")
    if fetch_subtitles and text_tracks:
        list_item = add_subtitles(list_item, text_tracks)
    xbmcplugin.setResolvedUrl(handle, succeeded=True, listitem=list_item)


def search(handle, query):
    search_options = listItems.search_sub(query)
    collection = listItems.from_collection(api.search(query, "videos"))
    xbmcplugin.addDirectoryItems(handle, search_options, len(collection))
    xbmcplugin.addDirectoryItems(handle, collection, len(collection))
    xbmcplugin.endOfDirectory(handle)


def add_subtitles(item, texttracks_url):
    subtitles = api.resolve_texttracks(texttracks_url)
    paths = []
    for subtitle in subtitles:
        file_name = "texttrack.{}.srt".format(subtitle["language"])
        vfs_cache.write(file_name, bytearray(subtitle["srt"], encoding="utf-8"))
        paths.append("special://userdata/addon_data/{}/cache/{}".format(addon_id, file_name))
        item.addStreamInfo("subtitle", {"language": subtitle["language"]})
    item.setSubtitles(paths)
    return item


def logout():
    settings.set("api.accesstoken", "")
    vfs.delete(api.api_user_cache_key)
    vfs_cache.destroy()
