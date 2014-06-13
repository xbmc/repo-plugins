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

def addLinkItem(url, li):
    return xbmcplugin.addDirectoryItem(handle=handle, url=url, 
        listitem=li, isFolder=False)

# UI builder functions
def show_root_folder():
    options = [{"name": "Latest video", "id": "latest"},
        {"name": "More video", "id": "categories"},
        {"name": "Video series", "id": "series"},
        ]
    for option in options:
        liStyle=xbmcgui.ListItem(option["name"])
        addDirectoryItem({"option_id": option["id"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def show_categories():
    gtv = GuardianTV()
    items = gtv.getChannels()

    for item in items:
        liStyle=xbmcgui.ListItem(item["title"])
        addDirectoryItem({"url": item["url"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def show_series():
    gtv = GuardianTV()
    items = gtv.getSeries()

    for item in items:
        liStyle=xbmcgui.ListItem(item["title"])
        addDirectoryItem({"url": item["url"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_video_files(url):
    gtv = GuardianTV()
    items = gtv.getVideoByChannel(url)
    for item in items:
        if "url" in item:
            title = item["title"] + " (" + time.strftime("%d/%m/%Y %H:%M", item["date"]) + ")"
            liStyle=xbmcgui.ListItem(title, thumbnailImage=item["thumb"])
            liStyle.setInfo(type="video",
                infoLabels={"Title": title
                            })
            liStyle.setProperty("mimetype", "video/mp4")
            addLinkItem(item["url"], liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)


# parameter values
params = parameters_string_to_dict(sys.argv[2])
optionId = str(params.get("option_id", ""))
url = str(params.get("url", ""))

if optionId == "" and url == "":
    show_root_folder()
elif optionId == "latest":
    gtv = GuardianTV()
    show_video_files(gtv.getLatestVideoURL())
elif optionId == "categories":
    show_categories()
elif optionId == "series":
    show_series()    
else:
    show_video_files(url)
