# -*- coding: utf-8 -*-

import routing # pylint: disable=E0401
import xbmcaddon
import xbmcplugin
from resources.lib import kodiutils
from resources.lib import youtubelib
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory


ADDON = xbmcaddon.Addon()
ADDON_NAME = ADDON.getAddonInfo("name")
ICON = ADDON.getAddonInfo("icon")
FANART = ADDON.getAddonInfo("fanart")
plugin = routing.Plugin()


@plugin.route('/')
def index():
    # Live videos
    liz = ListItem("[I]%s[/I]" % (kodiutils.get_string(32010)))
    liz.setInfo(type="video", infoLabels={"plot": kodiutils.get_string(32011)})
    liz.setArt({"thumb": ICON, "icon": ICON, "fanart": FANART})
    liz.setProperty("isPlayable", "true")
    addDirectoryItem(plugin.handle, plugin.url_for(live), liz, False)
    # All videos
    liz = ListItem("[I]%s[/I]" % (kodiutils.get_string(32000)))
    liz.setInfo(type="video", infoLabels={"plot": kodiutils.get_string(32001)})
    liz.setArt({"thumb": ICON, "icon": ICON, "fanart": FANART})
    addDirectoryItem(plugin.handle, plugin.url_for(all_videos, playlist="all"), liz, True)
    # Playlists
    for liz in youtubelib.get_playlists():
        addDirectoryItem(plugin.handle, plugin.url_for(all_videos, playlist=liz.getProperty("playlist_id")), liz, True)
    xbmcplugin.setContent(plugin.handle, 'tvshows')
    endOfDirectory(plugin.handle)


@plugin.route('/videos')
def all_videos():
    #grab kwargs
    page_num = int(plugin.args["page"][0]) if "page" in list(plugin.args.keys()) else 1
    token = plugin.args["token"][0] if "token" in list(plugin.args.keys()) else ""
    playlist = plugin.args["playlist"][0] if "playlist" in list(plugin.args.keys()) else "all"
    upload_playlist = youtubelib.get_upload_playlist() if playlist == "all" else playlist

    for liz in youtubelib.get_videos(playlist, upload_playlist, token, page_num):
        if liz.getProperty("type") == "youtube_video":
            addDirectoryItem(plugin.handle, plugin.url_for(play, liz.getProperty("videoid")), liz, False)
        elif liz.getProperty("type") == "next":
            addDirectoryItem(plugin.handle, plugin.url_for(all_videos, playlist=playlist, page=int(liz.getProperty("page")), token=liz.getProperty("token")), liz, True)
    kodiutils.add_sort_methods(plugin.handle)
    xbmcplugin.setContent(plugin.handle, 'episodes')
    endOfDirectory(plugin.handle)


@plugin.route('/play/<videoid>')
def play(videoid):
    stream = 'plugin://plugin.video.youtube/play/?video_id=%s' % (videoid)
    liz = ListItem()
    liz.setPath(stream)
    xbmcplugin.setResolvedUrl(plugin.handle, True, liz)


@plugin.route('/live')
def live():
    choice = 0
    live_videos = [video for video in youtubelib.get_live_videos()]
    if not live_videos:
        kodiutils.notification(
            ADDON_NAME,
            kodiutils.get_string(32009)
        )
        return

    elif len(live_videos) > 1:
        choice = kodiutils.select(
            kodiutils.get_string(32010),
            [video["label"] for video in live_videos]
        )

    if choice > -1:
        stream = 'plugin://plugin.video.youtube/play/?video_id=%s' % (
            live_videos[choice]["video_id"]
        )
        liz = ListItem()
        liz.setPath(stream)
        xbmcplugin.setResolvedUrl(plugin.handle, True, liz)


def run():
    if not kodiutils.get_setting_as_bool("enter_all_videos"):
        plugin.run()
    else:
        plugin.redirect("/videos")
