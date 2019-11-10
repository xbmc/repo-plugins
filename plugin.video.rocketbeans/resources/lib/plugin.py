# -*- coding: utf-8 -*-
import routing

from resources.data import config
from resources.lib.youtube import YoutubeStream
from resources.lib.twitch import TwitchStream
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory, setContent
from xbmcaddon import Addon


plugin = routing.Plugin()
setContent(plugin.handle, 'videos')

livestream_thumbnail = None
livestream_url = None

__addon__ = Addon()

def getString(string_id):
    return __addon__.getLocalizedString(string_id).encode('utf-8', 'ignore')

def get_livestream():
    if __addon__.getSetting("stream") == 0:
        t = TwitchStream(config.TWITCH_USER_LOGIN)
        livestream_url, title, livestream_thumbnail = t.url, t.title, t.thumbnail
    else:
        livestream_url, title, livestream_thumbnail = YoutubeStream().get_live_video_info_from_channel_id(config.CHANNEL_ID)
    return livestream_url, livestream_thumbnail, title

@plugin.route('/')
def index():
    livestream_url, livestream_thumbnail, title = get_livestream()
    li = createListItem(
        ('Live | %s' % title),
        livestream_thumbnail,
        True,
        getString(32001),
        0
    )
    addDirectoryItem(
        plugin.handle,
        livestream_url,
        li
    )

    url = "plugin://plugin.video.youtube/user/%s/" % config.CHANNEL_ID
    addDirectoryItem(
        plugin.handle,
        url,
        ListItem(getString(32007)),
        True
    )

    url = "plugin://plugin.video.youtube/channel/%s/" % config.LETS_PLAY_CHANNEL_ID
    addDirectoryItem(
        plugin.handle, 
        url, 
        ListItem(getString(32006)),
        True
    )

    addDirectoryItem(
        plugin.handle, 
        "plugin://plugin.video.youtube/channel/%s/" % config.KINO_PLUS_CHANNEL_ID, 
        ListItem(getString(32009)),
        True
    )

    addDirectoryItem(
        plugin.handle,
        "plugin://plugin.video.youtube/channel/%s/" % config.GAME_TWO_CHANNEL_ID,
        ListItem(getString(32005)),
        True 
    )

    addDirectoryItem(
        plugin.handle, 
        "plugin://plugin.video.youtube/channel/%s/" % config.KINO_PLUS_CHANNEL_ID, 
        ListItem(getString(32009)),
        True
    )

    addDirectoryItem(
        plugin.handle,
        "plugin://plugin.video.youtube/channel/%s/" % config.HAENGI_HQ_CHANNEL_ID,
        ListItem(getString(32008)),
        True 
    )

    addDirectoryItem(
        plugin.handle,
        "plugin://plugin.video.twitch/?mode=channel_video_list&broadcast_type=upload&channel_id=%s" %(config.TWITCH_CHANNEL_ID),
        ListItem(getString(32004)),
        True
    )

    endOfDirectory(plugin.handle)


def createListItem(label, thumbnailImage, isPlayable, plot, duration):
    li = ListItem(
        label=label,
        thumbnailImage=thumbnailImage
    )
        
    if isPlayable:
        infoLabels = {}
        infoLabels['plot'] = plot

        if duration > 0:
            infoLabels['duration'] = duration

        li.setInfo(type='video', infoLabels=infoLabels)
        li.setProperty('isPlayable', 'true')

    return li

def run():
    plugin.run()
