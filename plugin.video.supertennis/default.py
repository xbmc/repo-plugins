import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib
from resources.lib.supertennis import SuperTennis

# plugin constants
__plugin__ = "plugin.video.supertennis"
__author__ = "Nightflyer"

Addon = xbmcaddon.Addon(id=__plugin__)
Icon = os.path.join(Addon.getAddonInfo('path'), 'icon.png')

# plugin handle
handle = int(sys.argv[1])

supertennis = SuperTennis()
url = supertennis.getUrl()

item=xbmcgui.ListItem("SuperTennis", thumbnailImage=Icon)
item.setInfo(type="Video", infoLabels={"Title": "SuperTennis"})
xbmc.Player().play(url, item)
