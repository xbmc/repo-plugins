# -*- coding: utf-8 -*-
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import time
import urllib
import urllib2
import urlparse
import feedparser
from BeautifulSoup import BeautifulSoup

# plugin constants
__plugin__ = "plugin.video.vercelliwebtv"
__author__ = "Nightflyer"

Addon = xbmcaddon.Addon(id=__plugin__)

# plugin handle
handle = int(sys.argv[1])

# utility functions
def parameters_string_to_dict(parameters):
    ''' Convert parameters encoded in a URL to a dict. '''
    paramDict = dict(urlparse.parse_qsl(parameters[1:]))
    return paramDict
 
def addLinkItem(parameters, li):
    li.setProperty('IsPlayable', 'true')
    li.setInfo('video', {})
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    return xbmcplugin.addDirectoryItem(handle=handle, url=url, 
        listitem=li, isFolder=False)

# UI builder functions
def show_root_menu():
    ''' Show the plugin root menu '''
    f = feedparser.parse("http://www.vercelliweb.tv/feed/")
    
    for entry in f.entries: 
        pageUrl = entry["link"]
        liStyle=xbmcgui.ListItem(entry.title + " (" + time.strftime("%d-%m-%Y %H:%M", entry.published_parsed) + ")" )
        addLinkItem({"mode": "play", "url": pageUrl}, liStyle)

    # TODO: Sort from most recent entry
    #xbmcplugin.addSortMethod(handle=handle, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)


def play(pageUrl):
    htmlData = urllib2.urlopen(pageUrl).read()
    tree = BeautifulSoup(htmlData, convertEntities=BeautifulSoup.HTML_ENTITIES)

    videoUrl = None
    iframeUrl = tree.find("iframe", "youtube-player")["src"]
    if iframeUrl.find("http://www.youtube.com") != -1:
        videoId = iframeUrl[iframeUrl.rfind("/")+1:iframeUrl.rfind("?")]
        videoUrl = "plugin://plugin.video.youtube/play/?video_id=%s" % videoId
    
    # Check is video not supported
    if videoUrl == None: 
        dialog = xbmcgui.Dialog()
        dialog.ok("VercelliWeb.TV", "Formato video non supportato.")
        return

    xbmc.log("Video URL: " + videoUrl)
    xbmcplugin.setResolvedUrl(handle=handle, succeeded=True, listitem=xbmcgui.ListItem(path=videoUrl))

# parameter values
params = parameters_string_to_dict(sys.argv[2])
mode = str(params.get("mode", ""))
url = str(params.get("url", ""))

if mode == "":
    show_root_menu()
else:
    play(url)
