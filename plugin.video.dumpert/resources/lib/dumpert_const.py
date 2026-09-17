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
INITIAL_PAGE_NUMBER = "0"
# In between part 1 and 2 there will be a page number, the first one will be "0"
LATEST_URL_PART_1 = "https://post.dumpert.nl/api/v1.0/latest/"
LATEST_URL_PART_2 = "/?app=www.dumpert.nl"
# In between part 1 and 2 there will be a page number, the first one will be "0"
TOPPERS_URL_PART_1 = "https://post.dumpert.nl/api/v1.0/toppers/"
TOPPERS_URL_PART_2 = "/?app=www.dumpert.nl"
# In between part 1 and 2 there will be a page number, the first one will be "0"
DUMPERT_TV_URL_PART_1 = "https://post.dumpert.nl/api/v1.0/dumperttv/"
DUMPERT_TV_URL_PART_2 = "/?order=date&media_type=all&app=www.dumpert.nl"
# "https://post.dumpert.nl/api/v1.0/search/<search-term>/<page-number>/?order=date&media_type=all&app=www.dumpert.nl"
# In between part 1 and 2 there will be a search term
# In between part 2 and 3 there will be a page number, the first one will be "0"
SEARCH_URL_PART_1 = "https://post.dumpert.nl/api/v1.0/search/"
SEARCH_URL_PART_2 = "/"
SEARCH_URL_PART_3 = "/?order=date&media_type=all&app=www.dumpert.nl"
# In between part 1 and 2 there will be a date (yyyy-mm-dd)
DAY_TOPPERS_URL_PART_1 = "https://post.dumpert.nl/api/v1.0/top5/dag/"
DAY_TOPPERS_URL_PART_2 = "/?app=www.dumpert.nl"
# In between part 1 and 2 there will be a week (yyyyww)
WEEK_TOPPERS_URL_PART_1 = "https://post.dumpert.nl/api/v1.0/top5/week/"
WEEK_TOPPERS_URL_PART_2 = "/?app=www.dumpert.nl"
# in between part 1 and 2 there will be a month (yyyymm)
MONTH_TOPPERS_URL_PART_1 = "https://post.dumpert.nl/api/v1.0/top5/maand/"
MONTH_TOPPERS_URL_PART_2 = "/?app=www.dumpert.nl"
SFW_HEADERS = {'X-Dumpert-NSFW': '0'}
NSFW_HEADERS = {'X-Dumpert-NSFW': '1'}
DAY = "day"
WEEK = "week"
MONTH = "month"
VIDEO_QUALITY_MOBILE = "mobile"
VIDEO_QUALITY_TABLET = "tablet"
VIDEO_QUALITY_720P = "720p"
DATE = "2026-09-15"
VERSION = "1.1.14"

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


def getSoup(html, default_parser="html5lib"):
    soup = BeautifulSoup(html, default_parser)
    return soup
