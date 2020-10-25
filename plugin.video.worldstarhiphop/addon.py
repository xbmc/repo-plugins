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
import sys
import urllib.parse
import xbmc

from resources.lib.worldstarhiphop_const import ADDON, DATE, VERSION, BASEURL

# Parse parameters...
if len(sys.argv[2]) == 0:
    #
    # Main menu
    #
    xbmc.log("[ADDON] %s, Python Version %s" % (ADDON, str(sys.version)), xbmc.LOGDEBUG)
    xbmc.log("[ADDON] %s v%s (%s) is starting, ARGV = %s" % (ADDON, VERSION, DATE, repr(sys.argv)), xbmc.LOGDEBUG)

    from resources.lib import worldstarhiphop_list as plugin

else:
    action = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['action'][0]
    #
    # List
    #
    if action == 'list':
        from resources.lib import worldstarhiphop_list as plugin
    #
    # Play
    #
    elif action == 'play':
        from resources.lib import worldstarhiphop_play as plugin
    #
    # Search
    #
    elif action == 'search':
        from resources.lib import worldstarhiphop_search as plugin

plugin.Main()