#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from future import standard_library
standard_library.install_aliases()
from builtins import str
import sys
import urllib.parse
import xbmc

from resources.lib.gamekings_const import ADDON, SETTINGS, DATE, VERSION

# Parse parameters
if len(sys.argv[2]) == 0:
    #
    # Main menu
    #
    xbmc.log("[ADDON] %s, Python Version %s" % (ADDON, str(sys.version)), xbmc.LOGDEBUG)
    xbmc.log("[ADDON] %s v%s (%s) is starting, ARGV = %s" % (ADDON, VERSION, DATE, repr(sys.argv)),
                 xbmc.LOGDEBUG)

    if SETTINGS.getSettingBool('onlyshowvideoscategory'):
        import resources.lib.gamekings_list as plugin
    else:
        import resources.lib.gamekings_main as plugin

else:
    action = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['action'][0]
    #
    # List
    #
    if action == 'list':
        import resources.lib.gamekings_list as plugin
    #
    # Play
    #
    elif action == 'play':
        import resources.lib.gamekings_play as plugin
    #
    # Play
    #
    elif action == 'search':
        import resources.lib.gamekings_search as plugin

plugin.Main()
