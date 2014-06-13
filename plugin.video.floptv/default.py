import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib
import urlparse
from resources.lib.floptv import FlopTV

# plugin constants
__plugin__ = "plugin.video.floptv"
__author__ = "Nightflyer"

Addon = xbmcaddon.Addon(id=__plugin__)

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

def addLinkItem(url, li):
    return xbmcplugin.addDirectoryItem(handle=handle, url=url, 
        listitem=li, isFolder=False)

# UI builder functions
def show_root_folder():
    floptv = FlopTV()
    items = floptv.getShows()

    for item in items:
        liStyle=xbmcgui.ListItem(item["title"], thumbnailImage=item["thumb"])
        addDirectoryItem({"showid": item["id"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_video_files(showId):
    floptv = FlopTV()
    items = floptv.getVideoByShow(showId)
    for item in items:
        liStyle=xbmcgui.ListItem(item["title"], thumbnailImage=item["thumb"])
        liStyle.setInfo(type="video",
            infoLabels={"Tvshowtitle": item["tvshowtitle"], 
                        "Title": item["title"],
                        "Plot": item["description"]
                        })
        addLinkItem(item["url"], liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)


# parameter values
params = parameters_string_to_dict(sys.argv[2])
showid = str(params.get("showid", ""))

if showid == "":
    show_root_folder()
else:
    show_video_files(showid)

