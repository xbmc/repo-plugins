# -*- coding: utf-8 -*-

import routing
import sys
import time
import urllib
import urlparse

from resources.data import config
from resources.lib.guide import show_guide
from resources.lib.youtube import get_live_video_id_from_channel_id
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory, setContent

plugin = routing.Plugin()
setContent(plugin.handle, 'videos')


@plugin.route('/')
def index():
    video_id, title = get_live_video_id_from_channel_id(config.CHANNEL_ID)
    url = "plugin://plugin.video.youtube/play/?video_id=%s" % video_id
    li = ListItem(label="Live | " + title,
                  thumbnailImage="https://i.ytimg.com/vi/%s/maxresdefault_live.jpg#%s" % (video_id, time.localtime()))
    li.setProperty('isPlayable', 'true')
    li.setInfo(type=u'video', infoLabels={'title': title, 'plot': 'The live stream.'})
    addDirectoryItem(plugin.handle, url, li)

    url = "plugin://plugin.video.youtube/user/%s/" % config.CHANNEL_ID
    addDirectoryItem(plugin.handle, url, ListItem('Mediathek'), True)

    url = "plugin://plugin.video.youtube/channel/%s/" % config.LETS_PLAY_CHANNEL_ID
    addDirectoryItem(
        plugin.handle, url, ListItem('Let\'s-Play-Mediathek'), True)

    addDirectoryItem(
        plugin.handle, plugin.url_for(guide), ListItem('Sendeplan'), True)

    endOfDirectory(plugin.handle)


@plugin.route('/guide')
def guide():
    guide_items = show_guide()

    for guide_item in guide_items:
        li = ListItem(guide_item)
        addDirectoryItem(plugin.handle, '', li)
    endOfDirectory(plugin.handle)


def run():
    plugin.run()
