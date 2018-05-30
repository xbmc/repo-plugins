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
ADDON = "plugin.video.roosterteeth"
SETTINGS = xbmcaddon.Addon(id=ADDON)
LANGUAGE = SETTINGS.getLocalizedString
IMAGES_PATH = os.path.join(xbmcaddon.Addon(id=ADDON).getAddonInfo('path'), 'resources', 'images')
# This is a random number that identifies the client to the authorization website
KODI_ROOSTERTEETH_ADDON_CLIENT_ID = '4338d2b4bdc8db1239360f28e72f0d9ddb1fd01e7a38fbb07b4b1f4ba4564cc5'
ROOSTERTEETH_AUTHORIZATION_URL = 'https://auth.roosterteeth.com/oauth/token'
ROOSTERTEETH_BASE_URL = 'https://svod-be.roosterteeth.com'
ROOSTERTEETH_SERIES_BASE_URL = 'https://svod-be.roosterteeth.com/api/v1/shows'
ROOSTERTEETH_SERIES_URL = 'https://svod-be.roosterteeth.com/api/v1/shows?per_page=1000&order=desc'
NUMBER_OF_EPISODES_PER_PAGE = '30'
ROOSTERTEETH_RECENTLY_ADDED_VIDEOS_SERIES_URL = 'https://svod-be.roosterteeth.com/api/v1/channels/rooster-teeth/episodes?per_page=' + NUMBER_OF_EPISODES_PER_PAGE
ACHIEVEMENTHUNTER_RECENTLY_ADDED_VIDEOS_SERIES_URL = 'https://svod-be.roosterteeth.com/api/v1/channels/achievement-hunter/episodes?per_page=' + NUMBER_OF_EPISODES_PER_PAGE
FUNHAUS_RECENTLY_ADDED_VIDEOS_SERIES_URL = 'https://svod-be.roosterteeth.com/api/v1/channels/funhaus/episodes?per_page=' + NUMBER_OF_EPISODES_PER_PAGE
SCREWATTACK__RECENTLY_ADDED_VIDEOS_SERIES_URL = 'https://svod-be.roosterteeth.com/api/v1/channels/screwattack/episodes?per_page=' + NUMBER_OF_EPISODES_PER_PAGE
COWCHOP_RECENTLY_ADDED_VIDEOS_SERIES_URL = 'https://svod-be.roosterteeth.com/api/v1/channels/cow-chop/episodes?per_page=' + NUMBER_OF_EPISODES_PER_PAGE
SUGARPINE7__RECENTLY_ADDED_VIDEOS_SERIES_URL = 'https://svod-be.roosterteeth.com/api/v1/channels/sugar-pine-7/episodes?per_page=' + NUMBER_OF_EPISODES_PER_PAGE
GAMEATTACK_RECENTLY_ADDED_VIDEOS_SERIES_URL = 'https://svod-be.roosterteeth.com/api/v1/channels/game-attack/episodes?per_page=' + NUMBER_OF_EPISODES_PER_PAGE
THEKNOW_RECENTLY_ADDED_VIDEOS_SERIES_URL = 'https://svod-be.roosterteeth.com/api/v1/channels/the-know/episodes?per_page=' + NUMBER_OF_EPISODES_PER_PAGE
JTMUSIC_RECENTLY_ADDED_VIDEOS_SERIES_URL = 'https://svod-be.roosterteeth.com/api/v1/channels/jt-music/episodes?per_page=' + NUMBER_OF_EPISODES_PER_PAGE
SPONSOR_ONLY_VIDEO_TITLE_PREFIX = '* '
VQ4K = '4k'
VQ1080P = '1080p'
VQ720P = '720p'
VQ480P = '480p'
VQ360P = '360p'
VQ240P = '240p'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
DATE = "2018-05-15"
VERSION = "1.3.9"


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


def find_all(string_to_be_searched_for, string_to_be_searched_in):
    monitor = xbmc.Monitor()
    start_pos_in_string_to_be_searched_in = 0
    start_pos_array = []
    # exit loop when kodi gets an abort-request
    while not monitor.abortRequested():
        found_start_pos = string_to_be_searched_in.find(string_to_be_searched_for, start_pos_in_string_to_be_searched_in)
        if found_start_pos == -1:
            # exit the loop
            break
        else:
            start_pos_array.append(found_start_pos)
            start_pos_in_string_to_be_searched_in = found_start_pos + 1
    return start_pos_array
