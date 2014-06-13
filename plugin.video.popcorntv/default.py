import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib
import urlparse
from resources.lib.popcorntv import PopcornTV

# plugin constants
__plugin__ = "plugin.video.popcorntv"
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
    popcorntv = PopcornTV()
    items = popcorntv.getCategories()

    for item in items:
        liStyle=xbmcgui.ListItem(item["title"])
        addDirectoryItem({"mode": "folder", "url": item["url"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_category_folder(url):
    popcorntv = PopcornTV()
    items = popcorntv.getSubCategories(url)

    for item in items:
        liStyle=xbmcgui.ListItem(item["title"])
        addDirectoryItem({"mode": "list", "url": item["url"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def show_video_files(url):
    popcorntv = PopcornTV()
    items = popcorntv.getVideoBySubCategories(url)
    
    for item in items:
        liStyle=xbmcgui.ListItem(item["title"], thumbnailImage=item["thumb"])
        addLinkItem({"mode": "video", "url": item["url"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def play_video(url):
    popcorntv = PopcornTV()
    #video_url = popcorntv.getVideoURL(popcorntv.getSmilUrl(url))
    video_url = popcorntv.getAndroidVideoURL(popcorntv.getSmilUrl(url))
    xbmc.Player().play(video_url)
    
# parameter values
params = parameters_string_to_dict(sys.argv[2])
mode = str(params.get("mode", ""))
url = str(params.get("url", ""))

if mode == "":
    show_root_folder()
elif mode == "folder":
    show_category_folder(url)
elif mode == "list":
    show_video_files(url)
elif mode == "video":
    play_video(url)

