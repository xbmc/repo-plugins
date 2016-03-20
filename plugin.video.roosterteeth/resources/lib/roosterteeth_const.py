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
DATE = "SNAPSHOT"
VERSION = "1.2.9"
