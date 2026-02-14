from logging import DEBUG

import xbmc
import sys
import urllib.parse
import xbmcplugin
from resources.lib.ui.UI import UI

addon_handle = int(sys.argv[1])
args = urllib.parse.parse_qs(sys.argv[2][1:])

xbmc.log("plugin.video.rtve - addon.py - args: " + str(args), xbmc.LOGDEBUG)

xbmcplugin.setContent(addon_handle, 'movies')

ui = UI(sys.argv[0], addon_handle, args)
ui.run(args.get('mode', None), args.get('url', ['']))