#!/usr/bin/env python
# encoding: UTF-8

import xbmc, xbmcgui

def play(url):
    "Play audio or video on a given url"
    xbmc.Player().play(url)

def play_stream(playpath, sfwplayer, rtmp_url, url, name):
    "Play flash videos"
    item = xbmcgui.ListItem(name)
    item.setProperty("PlayPath", playpath)
    item.setProperty("SWFPlayer", sfwplayer)
    item.setProperty("PageURL", url)
    xbmc.Player().play(rtmp_url, item)

