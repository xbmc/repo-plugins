# -*- coding: utf-8 -*-
# Kodi add-on: Competition Doom (https://doom.com.hr/)
# Lists the Doom speedrun YouTube channels; playback is done by plugin.video.youtube.
# License: GPL-3.0-or-later (see LICENSE.txt)

import xbmcaddon
import xbmcplugin
import xbmcgui

ADDON = xbmcaddon.Addon()
ICON = ADDON.getAddonInfo("icon")
FANART = ADDON.getAddonInfo("fanart")

# (title, YouTube channel id, description)
CHANNELS = (
    ("Competition Doom", "UCuy3ApT1zlEcbSDPkb2j6cA",
     "Competition Doom (CNDOOM) world speed records."),
    ("COMPET-N", "UCfoaUAr2rLZBjLeIJzrS9NQ",
     "The original COMPET-N Doom speed records."),
    ("DSDA", "UCqcYluu5zm7uqBNGL8kextA",
     "Doom Speed Demo Archive."),
)


def youtube_channel_url(channel_id):
    return "plugin://plugin.video.youtube/channel/{}/".format(channel_id)


def main_list(handle):
    xbmcplugin.setContent(handle, "videos")
    for title, channel_id, plot in CHANNELS:
        item = xbmcgui.ListItem(label=title, offscreen=True)
        item.setArt({"icon": ICON, "thumb": ICON, "fanart": FANART})
        tag = item.getVideoInfoTag()
        tag.setTitle(title)
        tag.setPlot(plot)
        xbmcplugin.addDirectoryItem(handle, youtube_channel_url(channel_id), item, isFolder=True)
    xbmcplugin.endOfDirectory(handle)


def run(argv):
    main_list(int(argv[1]))
