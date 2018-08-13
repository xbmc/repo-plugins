import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib
import urlparse
from resources.lib.live import Live

# plugin constants
__plugin__ = "plugin.video.supertennis"
__author__ = "Nightflyer"

Addon = xbmcaddon.Addon(id=__plugin__)
Icon = os.path.join(Addon.getAddonInfo('path'), 'icon.png')

# plugin handle
handle = int(sys.argv[1])

# utility functions
def parameters_string_to_dict(parameters):
    ''' Convert parameters encoded in a URL to a dict. '''
    paramDict = dict(urlparse.parse_qsl(parameters[1:]))
    return paramDict
 
def addDirectoryItem(parameters, li):
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    return xbmcplugin.addDirectoryItem(handle=handle, url=url, 
        listitem=li, isFolder=True)

def addLinkItem(parameters, li):
    li.setProperty('IsPlayable', 'true')
    li.setInfo('video', {})
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    return xbmcplugin.addDirectoryItem(handle=handle, url=url, 
        listitem=li, isFolder=False)

# UI builder functions
def show_root_menu():
    liStyle=xbmcgui.ListItem("Live", thumbnailImage=Icon)
    addLinkItem({"mode": "live"}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def play_live():
    live = Live()
    xbmc.log("Live streaming...")
    if  Addon.getSetting("stream_source") == "0":
        xbmc.log("Web stream")
        url = live.getUrl()
    else:
        xbmc.log("Mobile stream")
        url = live.getMobileUrl()
    liStyle=xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(handle=handle, succeeded=True, listitem=liStyle)

# parameter values
params = parameters_string_to_dict(sys.argv[2])
mode = str(params.get("mode", ""))
url = str(params.get("url", ""))

if mode == "":
    show_root_menu()
elif mode == "live":
    play_live()
