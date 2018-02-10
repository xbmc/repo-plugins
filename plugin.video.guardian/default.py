import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib
import urlparse
import time
from resources.lib.guardian import GuardianTV


# plugin constants
__plugin__ = "plugin.video.guardian"
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
def show_categories():
    gtv = GuardianTV()
    items = gtv.getChannels()

    for item in items:
        liStyle=xbmcgui.ListItem(item["title"])
        addDirectoryItem({"mode": "video_files", "url": item["url"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_video_files(url):
    xbmc.log("Category URL: " + url)
    gtv = GuardianTV()
    items = gtv.getVideoByChannel(url)
    for item in items:
        title = item["title"] + " (" + time.strftime("%d/%m/%Y %H:%M", item["date"]) + ")"
        liStyle=xbmcgui.ListItem(title, thumbnailImage=item["thumb"])
        addLinkItem({"mode": "play", "url": item["pageUrl"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def play(pageUrl):
    xbmc.log("Page URL: " + pageUrl)
    gtv = GuardianTV()
    video = gtv.getVideoMetadata(pageUrl)
    
    # Check if video url is present
    if video["url"] == None:
        dialog = xbmcgui.Dialog()
        dialog.ok("The Guardian", "Video URL not found.")
        return
    
    xbmc.log("Video URL: " + video["url"])
        
    liStyle=xbmcgui.ListItem(path=video["url"])
    xbmcplugin.setResolvedUrl(handle=handle, succeeded=True, listitem=liStyle)
    
# parameter values
params = parameters_string_to_dict(sys.argv[2])
mode = str(params.get("mode", ""))
url = str(params.get("url", ""))

if mode == "" and url == "":
    show_categories()
elif mode == "video_files":
    show_video_files(url)
else:
    play(url)