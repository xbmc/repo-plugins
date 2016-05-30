#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import xbmcaddon

#
# Constants
# 
ADDON = "plugin.video.roosterteeth"
SETTINGS = xbmcaddon.Addon(id=ADDON)
LANGUAGE = SETTINGS.getLocalizedString
IMAGES_PATH = os.path.join(xbmcaddon.Addon(id=ADDON).getAddonInfo('path'), 'resources', 'images')
RECENTLYADDEDURL = 'http://roosterteeth.com/episode/recently-added?page=001'
ROOSTERTEETHSHOWSURL = 'http://www.roosterteeth.com/show/'
ACHIEVEMENTHUNTERURL = 'http://achievementhunter.roosterteeth.com/show/'
THEKNOWSHOWSURL = 'http://theknow.roosterteeth.com/show'
FUNHAUSSHOWSURL = 'http://funhaus.roosterteeth.com/show'
SCREWATTACKURL = 'http://screwattack.roosterteeth.com/show'
DATE = "2016-05-30"
VERSION = "1.3.1"
