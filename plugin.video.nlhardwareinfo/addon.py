#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
import os
import sys
import xbmc
import xbmcaddon

reload(sys)
sys.setdefaultencoding('utf8')

LIB_DIR = xbmc.translatePath(
    os.path.join(xbmcaddon.Addon(id="plugin.video.nlhardwareinfo").getAddonInfo('path'), 'resources', 'lib'))
sys.path.append(LIB_DIR)

from nlhardwareinfo_const import ADDON, SETTINGS, LANGUAGE, IMAGES_PATH, DATE, VERSION

xbmc.log("[ADDON] %s, Python Version %s" % (ADDON, str(sys.version)), xbmc.LOGDEBUG)
xbmc.log("[ADDON] %s v%s (%s) is starting, ARGV = %s" % (ADDON, VERSION, DATE, repr(sys.argv)),
             xbmc.LOGDEBUG)

import nlhardwareinfo_list_play as plugin

plugin.Main()
