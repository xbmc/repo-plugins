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
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    return xbmcplugin.addDirectoryItem(handle=handle, url=url, 
        listitem=li, isFolder=False)

# UI builder functions
def show_root_folder():
    options = [{"name": "Latest video", "mode": "latest"},
        {"name": "More video", "mode": "categories"},
        {"name": "Video series", "mode": "series"},
        ]
    for option in options:
        liStyle=xbmcgui.ListItem(option["name"])
        addDirectoryItem({"mode": option["mode"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def show_categories():
    gtv = GuardianTV()
    items = gtv.getChannels()

    for item in items:
        liStyle=xbmcgui.ListItem(item["title"])
        addDirectoryItem({"mode": "video_files", "url": item["url"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def show_series():
    gtv = GuardianTV()
    items = gtv.getSeries()

    for item in items:
        liStyle=xbmcgui.ListItem(item["title"])
        addDirectoryItem({"mode": "video_files", "url": item["url"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_video_files(url):
    gtv = GuardianTV()
    items = gtv.getVideoByChannel(url)
    for item in items:
        title = item["title"] + " (" + time.strftime("%d/%m/%Y %H:%M", item["date"]) + ")"
        liStyle=xbmcgui.ListItem(title, thumbnailImage=item["thumb"])
        addLinkItem({"mode": "play", "url": item["pageUrl"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def play(pageUrl):
    gtv = GuardianTV()
    video = gtv.getVideoMetadata(pageUrl)
    
    # Check if video url is present
    if video["url"] == None:
        dialog = xbmcgui.Dialog()
        dialog.ok("The Guardian", "Video URL not found.")
        return
        
    liStyle=xbmcgui.ListItem(video["title"], thumbnailImage=video["thumb"])
    xbmc.Player().play(video["url"], liStyle)
    
# parameter values
params = parameters_string_to_dict(sys.argv[2])
mode = str(params.get("mode", ""))
url = str(params.get("url", ""))

if mode == "" and url == "":
    show_root_folder()
elif mode == "latest":
    gtv = GuardianTV()
    show_video_files(gtv.getLatestVideoURL())
elif mode == "categories":
    show_categories()
elif mode == "series":
    show_series()    
elif mode == "video_files":
    show_video_files(url)
else:
    play(url)