#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import xbmcaddon

#
# Constants
# 
ADDON = "plugin.video.gamekings"
SETTINGS = xbmcaddon.Addon()
LANGUAGE = SETTINGS.getLocalizedString
IMAGES_PATH = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'resources', 'images')
BASE_URL_GAMEKINGS_TV = "https://www.gamekings.tv/"
LOGIN_URL = 'https://www.gamekings.tv/wp-login.php'
TWITCH_URL =  'plugin://plugin.video.twitch/playLive/gamekings/'
DATE = "2017-05-17"
VERSION = "1.2.10"
