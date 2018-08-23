#!/usr/bin/env python
# encoding: UTF-8

import xbmc
import xbmcgui


def play(url, name):
    """
    Play audio or video on a given url"

    :param url: Full url of the video
    :param name: Stream name
    """
    xbmc.Player().play(url, xbmcgui.ListItem(name))
