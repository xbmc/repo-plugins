#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import xbmcaddon

#
# Constants
# 
ADDON = "plugin.video.hak5"
SETTINGS = xbmcaddon.Addon()
LANGUAGE = SETTINGS.getLocalizedString
IMAGES_PATH = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'resources', 'images')
HAK5RECENTLYADDEDURL = 'http://www.hak5.org/category/episodes'
HAK5SEASONSURLHTTPS = 'https://www.hak5.org/shows/hak5'
HAKTIKRECENTLYADDEDURL = 'http://www.hak5.org/category/episodes/haktip/page/001'
THREATWIRERECENTLYADDEDURL = 'http://www.hak5.org/category/episodes/threatwire/page/001'
TEKTHINGRECENTLYADDEDURL = 'http://www.hak5.org/category/episodes/tekthing/page/001'
PINEAPPLEUNIVERSITYRECENTLYADDEDURL = 'http://www.hak5.org/category/episodes/pineapple-university'
METASPLOITRECENTLYADDEDURL = 'http://www.hak5.org/category/episodes/metasploit-minute/page/001'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
DATE = "2017-10-11"
VERSION = "1.0.1"