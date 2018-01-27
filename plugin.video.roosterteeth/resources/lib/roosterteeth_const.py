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
ROOSTERTEETHRECENTLYADDEDURL = 'http://roosterteeth.com/episode/recently-added?page=001'
ROOSTERTEETHSHOWSURL = 'http://www.roosterteeth.com/show/'
ACHIEVEMENTHUNTERRECENTLYADDEDURL = 'http://achievementhunter.roosterteeth.com/episode/recently-added?page=001'
ACHIEVEMENTHUNTERSHOWSURL = 'http://achievementhunter.roosterteeth.com/show/'
FUNHAUSRECENTLYADDEDURL = 'http://funhaus.roosterteeth.com/episode/recently-added?page=001'
FUNHAUSSHOWURL = 'http://funhaus.roosterteeth.com/show'
SCREWATTACKRECENTLYADDEDURL = 'http://screwattack.roosterteeth.com/episode/recently-added?page=001'
SCREWATTACKSHOWSURL = 'http://screwattack.roosterteeth.com/show'
GAMEATTACKRECENTLYADDEDURL = 'http://gameattack.roosterteeth.com/episode/recently-added?page=001'
GAMEATTACKSHOWSURL = 'http://gameattack.roosterteeth.com/show'
THEKNOWRECENTLYADDEDURL = 'http://theknow.roosterteeth.com/episode/recently-added?page=001'
THEKNOWSHOWSURL = 'http://theknow.roosterteeth.com/show'
COWCHOPRECENTLYADDEDURL = 'http://cowchop.roosterteeth.com/episode/recently-added?page=001'
COWCHOPSHOWSURL = 'http://cowchop.roosterteeth.com/show'
SUGARPINE7RECENTLYADDEDURL = 'http://sugarpine7.roosterteeth.com/episode/recently-added?page=001'
SUGARPINE7SHOWSURL = 'http://sugarpine7.roosterteeth.com/show'
LOGINURL_RT = 'http://roosterteeth.com/login'
LOGINURL_AH = 'http://achievementhunter.roosterteeth.com/login'
LOGINURL_FH = 'http://funhaus.roosterteeth.com/login'
LOGINURL_SA = 'http://screwattack.roosterteeth.com/login'
LOGINURL_GA = 'http://gameattack.roosterteeth.com/login'
LOGINURL_TK = 'http://theknow.roosterteeth.com/login'
LOGINURL_CC = 'http://cowchop.roosterteeth.com/login'
LOGINURL_SP7 = 'http://sugarpine7.roosterteeth.com/login'
NEWHLS = 'NewHLS-'
VQ1080P = '1080P'
VQ720P = '720P'
VQ480P = '480P'
VQ360P = '360P'
VQ240P = '240P'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
DATE = "2018-02-21"
VERSION = "1.3.5"


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
        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, name_object, convertToUnicodeString(object)), xbmc.LOGDEBUG)
    except:
        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, name_object,
            "Unable to log the object due to an error while converting it to an unicode string"), xbmc.LOGDEBUG)


def getSoup(html, default_parser="html5lib"):
    soup = BeautifulSoup(html, default_parser)
    return soup