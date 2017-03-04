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
DATE = "2017-03-03"
VERSION = "1.3.3"
