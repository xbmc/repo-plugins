import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib
import urlparse
import time
from resources.lib.corrieretv import CorriereTV


# plugin constants
__plugin__ = "plugin.video.corrieretv"
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
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    return xbmcplugin.addDirectoryItem(handle=handle, url=url, 
        listitem=li, isFolder=False)

# UI builder functions
def show_categories():
    corrieretv = CorriereTV()
    items = corrieretv.getChannels()

    for item in items:
        liStyle=xbmcgui.ListItem(item["title"])
        addDirectoryItem({"mode": "video_files", "url": item["url"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_video_files(url):
    xbmc.log("Category URL: " + url)
    corrieretv = CorriereTV()
    items = corrieretv.getVideoByChannel(url)
    for item in items:
        title = item["title"] + " (" + item["date"] + ")"
        liStyle=xbmcgui.ListItem(title, thumbnailImage=item["thumb"])
        liStyle.setProperty('IsPlayable', 'true')
        addLinkItem({"mode": "play", "id": item["videoId"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def play(videoId):
    xbmc.log("Video ID: " + videoId)
    corrieretv = CorriereTV()
    videoUrl = corrieretv.getVideoUrl(videoId)
    
    xbmc.log("Video URL: " + videoUrl)
    
    liStyle=xbmcgui.ListItem(path=videoUrl)
    xbmcplugin.setResolvedUrl(handle=handle, succeeded=True, listitem=liStyle)
    
# parameter values
params = parameters_string_to_dict(sys.argv[2])
mode = str(params.get("mode", ""))
url = str(params.get("url", ""))
videoId = str(params.get("id", ""))

if mode == "" and url == "":
    show_categories()
elif mode == "video_files":
    show_video_files(url)
else:
    play(videoId)
