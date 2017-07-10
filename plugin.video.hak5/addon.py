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
    os.path.join(xbmcaddon.Addon(id="plugin.video.hak5").getAddonInfo('path'), 'resources', 'lib'))
sys.path.append(LIB_DIR)

from hak5_const import ADDON, DATE, VERSION

# Parse parameters...
if len(sys.argv[2]) == 0:
    #
    # Main menu
    #
    xbmc.log("[ADDON] %s, Python Version %s" % (ADDON, str(sys.version)), xbmc.LOGDEBUG)
    xbmc.log("[ADDON] %s v%s (%s) is starting, ARGV = %s" % (ADDON, VERSION, DATE, repr(sys.argv)),
                 xbmc.LOGDEBUG)
    import hak5_main as plugin
else:
    action = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['action'][0]
    #
    # List Episodes
    #
    if action == 'list-episodes':
        import hak5_list_episodes as plugin
    #
    # List Seasons
    #
    if action == 'list-seasons':
        import hak5_list_seasons as plugin
    #
    # Play Video
    #
    elif action == 'play':
        import hak5_play as plugin

plugin.Main()
