# -*- coding: utf-8 -*-

import routing
import logging
import xbmcaddon
from resources.lib import kodiutils
from resources.lib import kodilogging
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory

import get_streams


ADDON = xbmcaddon.Addon()
logger = logging.getLogger(ADDON.getAddonInfo('id'))
kodilogging.config()
plugin = routing.Plugin()


@plugin.route('/')
def index():
    quality_setting = kodiutils.get_setting("quality")
    quality = None
    if quality_setting == u'0':
        quality = "hd"
    if quality_setting == u'1':
        quality = "high"
    if quality_setting == u'2':
        quality = "low"
    if quality == None:
        quality = "high"
    for stream in get_streams.get_all():
        addDirectoryItem(plugin.handle, stream[quality], ListItem(stream["name"]))
    endOfDirectory(plugin.handle)

def run():
    plugin.run()
