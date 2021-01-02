# -*- coding: utf-8 -*-

import routing
import logging
import xbmcaddon
from resources.lib import kodiutils
from resources.lib import kodilogging
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory


ADDON = xbmcaddon.Addon()
logger = logging.getLogger(ADDON.getAddonInfo('id'))
kodilogging.config()
plugin = routing.Plugin()


@plugin.route('/')
def index():
    addDirectoryItem(plugin.handle, "http://listen.technobase.fm/mp3", ListItem("TechnoBase.FM"))
    addDirectoryItem(plugin.handle, "http://listen.housetime.fm/mp3", ListItem("HouseTime.FM"))
    addDirectoryItem(plugin.handle, "http://listen.hardbase.fm/mp3", ListItem("HardBase.FM"))
    addDirectoryItem(plugin.handle, "http://listen.trancebase.fm/mp3", ListItem("TranceBase.FM"))
    addDirectoryItem(plugin.handle, "http://listen.coretime.fm/mp3", ListItem("CoreTime.FM"))
    addDirectoryItem(plugin.handle, "http://listen.clubtime.fm/mp3", ListItem("ClubTime.FM"))
    addDirectoryItem(plugin.handle, "http://listen.teatime.fm/mp3", ListItem("TeaTime.FM"))
    addDirectoryItem(plugin.handle, "http://listen.replay.fm/mp3", ListItem("Replay.FM"))
    endOfDirectory(plugin.handle)

def run():
    plugin.run()
