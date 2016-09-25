#!/usr/bin/env python
# -*- coding: UTF-8 -*-

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

LIB_DIR = xbmc.translatePath(
    os.path.join(xbmcaddon.Addon(id="plugin.video.worldstarhiphop").getAddonInfo('path'), 'resources', 'lib'))
sys.path.append(LIB_DIR)

from worldstarhiphop_const import ADDON, DATE, VERSION

BASEURL = "http://www.worldstarhiphop.com"

# Parse parameters...
if len(sys.argv[2]) == 0:
    #
    # Main menu
    #
    xbmc.log("[ADDON] %s, Python Version %s" % (ADDON, str(sys.version)), xbmc.LOGDEBUG)
    xbmc.log("[ADDON] %s v%s (%s) is starting, ARGV = %s" % (ADDON, VERSION, DATE, repr(sys.argv)), xbmc.LOGDEBUG)
    import worldstarhiphop_list as plugin
else:
    action = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['action'][0]
    #
    # List
    #
    if action == 'list':
        import worldstarhiphop_list as plugin
    #
    # Play
    #
    elif action == 'play':
        import worldstarhiphop_play as plugin
    #
    # Search
    #
    elif action == 'search':
        import worldstarhiphop_search as plugin

plugin.Main()
