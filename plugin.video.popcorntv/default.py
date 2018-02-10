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
    li.setProperty('IsPlayable', 'true')
    li.setInfo('video', {})
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
    xbmc.log("Category URL: " + url)
    popcorntv = PopcornTV()
    items = popcorntv.getSubCategories(url)

    for item in items:
        liStyle=xbmcgui.ListItem(item["title"])
        addDirectoryItem({"mode": "list", "url": item["url"]}, liStyle)
    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def show_video_files(url):
    xbmc.log("Subcategory URL: " + url)
    popcorntv = PopcornTV()
    page = popcorntv.getVideoBySubCategories(url)
    
    for video in page["videoList"]:
        liStyle=xbmcgui.ListItem(video["title"], thumbnailImage=video["thumb"])
        addLinkItem({"mode": "video", "url": video["url"]}, liStyle)
        
    if page["firstPageUrl"] is not None:
        liStyle=xbmcgui.ListItem("<< First Page", iconImage = "DefaultFolder.png")
        addDirectoryItem({"mode": "list", "url": page["firstPageUrl"]}, liStyle)
        
    if page["prevPageUrl"] is not None:
        liStyle=xbmcgui.ListItem("< Prev Page", iconImage = "DefaultFolder.png")
        addDirectoryItem({"mode": "list", "url": page["prevPageUrl"]}, liStyle)
        
    if page["nextPageUrl"] is not None:
        liStyle=xbmcgui.ListItem("> Next Page", iconImage = "DefaultFolder.png")
        addDirectoryItem({"mode": "list", "url": page["nextPageUrl"]}, liStyle)
        
    if page["lastPageUrl"] is not None:
        liStyle=xbmcgui.ListItem(">> Last Page", iconImage = "DefaultFolder.png")
        addDirectoryItem({"mode": "list", "url": page["lastPageUrl"]}, liStyle)
        
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def play_video(url):
    xbmc.log("Video URL: " + url)
    popcorntv = PopcornTV()
    metadata = popcorntv.getVideoMetadata(url)
    liStyle=xbmcgui.ListItem(path=metadata["videoUrl"])
    xbmcplugin.setResolvedUrl(handle=handle, succeeded=True, listitem=liStyle)
    
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

