#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import absolute_import, division, unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import str
import os
import sys
import xbmcaddon
import xbmc
from bs4 import BeautifulSoup

#
# Constants
#
ADDON = "plugin.video.tweakers"
SETTINGS = xbmcaddon.Addon()
LANGUAGE = SETTINGS.getLocalizedString
IMAGES_PATH = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'resources')
YOUTUBE_ID_STRING_TO_FIND = '"youtubeId":"'
DATE = "2018-09-30"
VERSION = "1.1.10"

if sys.version_info[0] > 2:
    unicode = str


def convertToUnicodeString(s, encoding='utf-8'):
    """Safe decode byte strings to Unicode"""
    if isinstance(s, bytes):  # This works in Python 2.7 and 3+
        s = s.decode(encoding)
    return s


def convertToByteString(s, encoding='utf-8'):
    """Safe encode Unicode strings to bytes"""
    if isinstance(s, unicode):
        s = s.encode(encoding)
    return s


def log(name_object, object):
    try:
        # Let's try and remove any non-ascii stuff first
        object = object.encode('ascii', 'ignore')
    except:
        pass

    try:
        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, name_object, convertToUnicodeString(object)), xbmc.LOGDEBUG)
    except:
        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, name_object, "Unable to log the object due to an error while converting it to an unicode string"), xbmc.LOGDEBUG)


def getSoup(html,default_parser="html5lib"):
    soup = BeautifulSoup(html, default_parser)
    return soup