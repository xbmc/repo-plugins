#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
import os
import xbmc
import xbmcaddon
from bs4 import BeautifulSoup

#
# Constants
# 
ADDON = "plugin.video.dumpert"
SETTINGS = xbmcaddon.Addon(id=ADDON)
LANGUAGE = SETTINGS.getLocalizedString
IMAGES_PATH = os.path.join(xbmcaddon.Addon(id=ADDON).getAddonInfo('path'), 'resources')
LATEST_URL = "https://api-live.dumpert.nl/mobile_api/json/video/latest/0/"
TOPPERS_URL = "https://api-live.dumpert.nl/mobile_api/json/video/toppers/0/"
DUMPERT_TV_URL = "https://api.dumpert.nl/mobile_api/json/dumperttv/0/"
SEARCH_URL = "https://api-live.dumpert.nl/mobile_api/json/search/"
DAY_TOPPERS_URL = "https://api-live.dumpert.nl/mobile_api/json/video/top5/dag/"
WEEK_TOPPERS_URL = "https://api-live.dumpert.nl/mobile_api/json/video/top5/week/"
MONTH_TOPPERS_URL = "https://api-live.dumpert.nl/mobile_api/json/video/top5/maand/"
SFW_HEADERS = {'X-Dumpert-NSFW': '0'}
NSFW_HEADERS = {'X-Dumpert-NSFW': '1'}
DAY = "day"
WEEK = "week"
MONTH = "month"
VIDEO_QUALITY_MOBILE = "mobile"
VIDEO_QUALITY_TABLET = "tablet"
VIDEO_QUALITY_720P = "720p"
DATE = "2024-10-01"
VERSION = "1.1.12"


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
            ADDON, VERSION, DATE, name_object,
            "Unable to log the object due to an error while converting it to an unicode string"), xbmc.LOGDEBUG)


def getSoup(html,default_parser="html5lib"):
    soup = BeautifulSoup(html, default_parser)
    return soup