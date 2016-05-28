#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# 
# Constants
#
# also in ..._const
__addon__ = "plugin.video.worldstarcandy"
__date__ = "26 may 2016"
__version__ = "1.0.0"

#
# Imports
#
import os
import re
import sys
import urllib
import urlparse
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

BASEURL = "http://www.worldstarcandy.com"

LIB_DIR = xbmc.translatePath(os.path.join(xbmcaddon.Addon(id=__addon__).getAddonInfo('path'), 'resources', 'lib'))
sys.path.append(LIB_DIR)

# Get plugin settings
DEBUG = xbmcaddon.Addon(id='plugin.video.worldstarcandy').getSetting('debug')

if (DEBUG) == 'true':
    xbmc.log("[ADDON] %s v%s (%s) is starting, ARGV = %s" % (__addon__, __version__, __date__, repr(sys.argv)),
             xbmc.LOGNOTICE)

# Parse parameters...
if len(sys.argv[2]) == 0:
    #
    # Main menu
    #
    import worldstarcandy_list as plugin
else:
    action = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['action'][0]
    #
    # List
    #
    if action == 'list':
        import worldstarcandy_list as plugin
    #
    # Play
    #
    elif action == 'play':
        import worldstarcandy_play as plugin
    #
    # Search
    #
    elif action == 'search':
        import worldstarcandy_search as plugin

plugin.Main()
