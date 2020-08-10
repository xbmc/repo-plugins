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

from resources.lib.dumpert_const import ADDON, DATE, VERSION, SETTINGS

# Parse parameters...
if len(sys.argv[2]) == 0:
    #
    # Main menu
    #
    xbmc.log("[ADDON] %s, Python Version %s" % (ADDON, str(sys.version)), xbmc.LOGDEBUG)
    xbmc.log("[ADDON] %s v%s (%s) is starting, ARGV = %s" % (ADDON, VERSION, DATE, repr(sys.argv)),
                 xbmc.LOGDEBUG)

    if SETTINGS.getSetting('onlyshownewimagescategory') == 'true':
        import resources.lib.dumpert_json as plugin
    else:
        import resources.lib.dumpert_main as plugin
else:
    action = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['action'][0]
    #
    # Search
    #
    if action == 'search':
        import resources.lib.dumpert_search as plugin
    #
    # Timemachine
    #
    elif action == 'timemachine':
        import resources.lib.dumpert_timemachine as plugin
    #
    # JSON
    #
    if action == 'json':
        import resources.lib.dumpert_json as plugin

plugin.Main()
