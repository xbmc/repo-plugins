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

from resources.lib.gamegurumania_const import ADDON,DATE, VERSION, SETTINGS

# Parse parameters...
if len(sys.argv[2]) == 0:
    #
    # Main menu
    #
    xbmc.log("[ADDON] %s, Python Version %s" % (ADDON, str(sys.version)), xbmc.LOGDEBUG)
    xbmc.log("[ADDON] %s v%s (%s) is starting, ARGV = %s" % (ADDON, VERSION, DATE, repr(sys.argv)), xbmc.LOGDEBUG)

    if SETTINGS.getSetting('onlyshowallvideoscategory') == 'true':
        from resources.lib import gamegurumania_list_play as plugin
    else:
        from resources.lib import gamegurumania_main as plugin
else:
    action = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['action'][0]
    #
    # List-play
    #
    if action == 'list-play':
        from resources.lib import gamegurumania_list_play as plugin

plugin.Main()
