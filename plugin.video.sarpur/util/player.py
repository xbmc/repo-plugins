#!/usr/bin/env python
# encoding: UTF-8

from __future__ import absolute_import

import sarpur
import xbmcgui
import xbmcplugin


def play(url, name, live=False):
    """
    Play audio or video on a given url"

    :param url: Full url of the video
    :param name: Stream name
    """
    item = xbmcgui.ListItem(name, path=url)
    if live:
        item.setProperty("IsLive", "true")

    xbmcplugin.setResolvedUrl(sarpur.ADDON_HANDLE, True, item)
