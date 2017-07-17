#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
import sys
import urlparse
import xbmc

reload(sys)
sys.setdefaultencoding('utf8')

from resources.lib.gamegurumania_const import ADDON,DATE, VERSION

# Parse parameters...
if len(sys.argv[2]) == 0:
    #
    # Main menu
    #
    xbmc.log("[ADDON] %s, Python Version %s" % (ADDON, str(sys.version)), xbmc.LOGDEBUG)
    xbmc.log("[ADDON] %s v%s (%s) is starting, ARGV = %s" % (ADDON, VERSION, DATE, repr(sys.argv)),
                 xbmc.LOGDEBUG)
    from resources.lib import gamegurumania_main as plugin
else:
    action = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['action'][0]
    #
    # List-play
    #
    if action == 'list-play':
        from resources.lib import gamegurumania_list_play as plugin

plugin.Main()
