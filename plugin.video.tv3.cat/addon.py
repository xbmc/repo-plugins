from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import str
import sys
import urllib.parse
import xbmcplugin
import xbmc
from resources.lib.ui.UI import UI


xbmc.log("plugin.video.tv3.cat - addon.py")
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])

xbmc.log(str(sys.argv[2][1:]))
args = urllib.parse.parse_qs(sys.argv[2][1:])

xbmc.log("plugin.video.tv3.cat - addon.py - args: ")
xbmc.log(str(args))

xbmcplugin.setContent(addon_handle, 'movies')

mode = args.get('mode', None)
url = args.get('url', [''])



ui = UI(base_url, addon_handle, args)


ui.run(mode, url)
  
