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
__plugin__ = "plugin.video.3bmeteo"
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
    # 3bmeteo Android app
    userAgent = "Dalvik/1.6.0 (Linux; U; Android 4.2.2; GT-I9105P Build/JDQ39)"
    url = "http://api.3bmeteo.com/mobile/video_previsionali_feed"
    
    headers = {'User-Agent': userAgent}
    req = urllib2.Request(url, None, headers)
    xmldata = urllib2.urlopen(req).read()
    dom = minidom.parseString(xmldata)
    
    # Parse video feed
    for videoNode in dom.getElementsByTagName('video'):
        link = videoNode.getElementsByTagName('url')[0].firstChild.nodeValue
        imageUrl = videoNode.getElementsByTagName('thumbnail')[0].firstChild.nodeValue
        title = videoNode.getElementsByTagName('titolo')[0].firstChild.nodeValue
        liStyle = xbmcgui.ListItem(title, thumbnailImage=imageUrl)
        addLinkItem(link, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

show_root_menu()
