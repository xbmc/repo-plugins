# -*- coding: utf-8 -*-
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib
import urllib2
import urlparse
from xml.dom import minidom

# plugin constants
__plugin__ = "plugin.video.ilmeteo"
__author__ = "Nightflyer"

Addon = xbmcaddon.Addon(id=__plugin__)

# plugin handle
handle = int(sys.argv[1])

# utility functions
def parameters_string_to_dict(parameters):
    ''' Convert parameters encoded in a URL to a dict. '''
    paramDict = dict(urlparse.parse_qsl(parameters[1:]))
    return paramDict
 
def addLinkItem(url, li):
    return xbmcplugin.addDirectoryItem(handle=handle, url=url, 
        listitem=li, isFolder=False)

# UI builder functions
def show_root_menu():
    ''' Show the plugin root menu '''
    url = "http://iphone.ilmeteo.it/android-app.php?method=listVideos&x=b5669358fa0b426a773d88041e6ae63b&v=2.98"
    xmldata = urllib2.urlopen(url).read()
    dom = minidom.parseString(xmldata)
    
    # Parse video feed
    for videoNode in dom.getElementsByTagName('video'):
        link = videoNode.attributes["url"].value
        d = videoNode.attributes["date"].value
        imageUrl = "http://media.ilmeteo.it/video/img/%s-%s-%s-tg-300.jpg" % (d[:4], d[4:6], d[6:])
        title = videoNode.firstChild.nodeValue
        liStyle = xbmcgui.ListItem(title, thumbnailImage=imageUrl)
        addLinkItem(link, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

show_root_menu()
