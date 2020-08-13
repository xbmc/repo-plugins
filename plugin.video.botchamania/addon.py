#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
# the YDStreamExtractor needs to be before the future imports. Otherwise u get an 'check hostname' error.
import YDStreamExtractor
from future import standard_library
standard_library.install_aliases()
from builtins import str
import os
import sys
import urllib.parse
import xbmc
import xbmcaddon

LIB_DIR = xbmc.translatePath( os.path.join( xbmcaddon.Addon(id='plugin.video.botchamania').getAddonInfo('path'), 'resources', 'lib' ) )
sys.path.append (LIB_DIR)

from botchamania_const import ADDON, SETTINGS, LANGUAGE, IMAGES_PATH, DATE, VERSION

# Parse parameters...
if len(sys.argv[2]) == 0:
    #
    # Main menu
    #
    xbmc.log("[ADDON] %s, Python Version %s" % (ADDON, str(sys.version)), xbmc.LOGDEBUG)
    xbmc.log( "[ADDON] %s v%s (%s) is starting, ARGV = %s" % ( ADDON, VERSION, DATE, repr(sys.argv) ), xbmc.LOGDEBUG )

    if SETTINGS.getSetting('onlyshowbotchamaniacategory') == 'true':
        import botchamania_list as plugin
    else:
        import botchamania_main as plugin
else:
    action = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['action'][0]
    #
    # List
    #
    if action == 'list':
        import botchamania_list as plugin
    #
    # Play
    #
    elif action == 'play':
        import botchamania_play as plugin

plugin.Main()
