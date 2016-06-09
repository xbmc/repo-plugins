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

reload(sys)
sys.setdefaultencoding('utf8')

LIB_DIR = xbmc.translatePath(
    os.path.join(xbmcaddon.Addon(id="plugin.video.gamekings").getAddonInfo('path'), 'resources', 'lib'))
sys.path.append(LIB_DIR)

from gamekings_const import ADDON, SETTINGS, LANGUAGE, IMAGES_PATH, DATE, VERSION

# Parse parameters
if len(sys.argv[2]) == 0:
    #
    # Main menu
    #
    xbmc.log("[ADDON] %s, Python Version %s" % (ADDON, str(sys.version)), xbmc.LOGDEBUG)
    xbmc.log("[ADDON] %s v%s (%s) is starting, ARGV = %s" % (ADDON, VERSION, DATE, repr(sys.argv)),
                 xbmc.LOGDEBUG)
    import gamekings_main as plugin
else:
    action = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['action'][0]
    #
    # List
    #
    if action == 'list':
        import gamekings_list as plugin
    #
    # Play
    #
    elif action == 'play':
        import gamekings_play as plugin
    #
    # Play
    #
    elif action == 'search':
        import gamekings_search as plugin

plugin.Main()
