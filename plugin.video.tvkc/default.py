import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib
import urlparse
import time
from resources.lib.tvkc import TVKC


# plugin constants
__plugin__ = "plugin.video.tvkc"
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
def show_series():
    tvkc = TVKC()
    items = tvkc.getSeries()

    for item in items:
        liStyle=xbmcgui.ListItem(item["title"], thumbnailImage=item["thumb"])
        addDirectoryItem({"section": "serie", "url": item["url"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_video_files(url):
    tvkc = TVKC()
    items = tvkc.getVideoList(url)
    for item in items:
        title = item["title"] + " (" + item["date"] + ")"
        liStyle=xbmcgui.ListItem(title, thumbnailImage=item["thumb"])
        liStyle.setProperty('IsPlayable', 'true')
        liStyle.setInfo(type="video", infoLabels={"Title": title})
        addLinkItem({"section": "play", "videoId": item["id"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def play_video(videoId):
    tvkc = TVKC()
    metadata = tvkc.getVideoMetadata(videoId)
    for f in metadata["mediaFiles"]:
        if f["mediaType"] == "MP4":
            video_url = f["streamer"] + \
                " playpath=mp4:" + f["filename"]
            break
    
    liStyle=xbmcgui.ListItem(metadata["title"], thumbnailImage=metadata["images"]["orig"], path=video_url)
    liStyle.setInfo(type="video", infoLabels={"Title": metadata["title"]})

    xbmcplugin.setResolvedUrl(handle=handle, succeeded=True, listitem=liStyle)
    
# parameter values
params = parameters_string_to_dict(sys.argv[2])
section = str(params.get("section", ""))
url = str(params.get("url", ""))
videoId = str(params.get("videoId", ""))
print params

if section == "":
    show_series()
elif section == "serie":
    show_video_files(url)
elif section == "play":
    play_video(videoId)
