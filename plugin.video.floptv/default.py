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

def addLinkItem(parameters, li):
    li.setProperty('IsPlayable', 'true')
    li.setInfo('video', {})
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    return xbmcplugin.addDirectoryItem(handle=handle, url=url, 
        listitem=li, isFolder=False)

# UI builder functions
def show_root_folder():
    floptv = FlopTV()
    items = floptv.getShows()
    
    for item in items:
        liStyle=xbmcgui.ListItem(item["title"], thumbnailImage=item["thumb"])
        addDirectoryItem({"mode": "video_files", "url": item["pageUrl"]}, liStyle)
    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_video_files(pageUrl):
    xbmc.log("Show URL: " + pageUrl)
    floptv = FlopTV()
    items = floptv.getVideoByShow(pageUrl)
    
    for item in items:
        liStyle=xbmcgui.ListItem(item["title"], thumbnailImage=item["thumb"])
        addLinkItem({"mode": "play", "url": item["pageUrl"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def play(pageUrl):
    xbmc.log("Page URL: " + pageUrl)
    
    floptv = FlopTV()
    videoUrl = floptv.getVideoUrl(pageUrl)
    xbmc.log("Video URL: " + videoUrl)
        
    liStyle=xbmcgui.ListItem(path=videoUrl)
    xbmcplugin.setResolvedUrl(handle=handle, succeeded=True, listitem=liStyle)
    
# parameter values
params = parameters_string_to_dict(sys.argv[2])
mode = str(params.get("mode", ""))
url = str(params.get("url", ""))

if mode == "" and url == "":
    show_root_folder()
elif mode == "video_files":
    show_video_files(url)
else:
    play(url)