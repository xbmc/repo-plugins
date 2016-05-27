#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
import os
import sys
import urlparse
import xbmc
import xbmcaddon

LIB_DIR = xbmc.translatePath(
    os.path.join(xbmcaddon.Addon(id="plugin.video.tweakers").getAddonInfo('path'), 'resources', 'lib'))
sys.path.append(LIB_DIR)

from tweakers_const import ADDON, DATE, VERSION

# Get plugin settings
DEBUG = xbmcaddon.Addon(id=ADDON).getSetting('debug')

# Parse parameters
if len(sys.argv[2]) == 0:
    #
    # Main menu
    #
    if DEBUG == 'true':
        xbmc.log("[ADDON] %s, Python Version %s" % (ADDON, str(sys.version)), xbmc.LOGNOTICE)
        xbmc.log("[ADDON] %s v%s (%s) is starting, ARGV = %s" % (ADDON, VERSION, DATE, repr(sys.argv)), xbmc.LOGNOTICE)

    import tweakers_list as plugin
else:
    action = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['action'][0]
    #
    # List
    #
    if action == 'list':
        import tweakers_list as plugin
    #
    # Play
    #
    elif action == 'play':
        import tweakers_play as plugin
    #
    # Search
    #
    elif action == 'search':
        import tweakers_search as plugin

plugin.Main()
