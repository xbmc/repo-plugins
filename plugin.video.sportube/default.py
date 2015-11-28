# -*- coding: utf-8 -*-
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib2
import urlparse
import json

# plugin constants
__plugin__ = "plugin.video.sportube"
__author__ = "Nightflyer"

Addon = xbmcaddon.Addon()

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
    url = "http://rest2.sportube.tv/api/default/tv.jsonp"
    data = urllib2.urlopen(url).read()
    # Convert JSONP object into JSON
    # https://stackoverflow.com/questions/30554522/django-parse-jsonp-json-with-padding
    data_json = data.split("(")[1].strip(")")
    response = json.loads(data_json)
    
    # Parse video feed
    for live in response["RESULT"]:
        link = live[4]
        imageUrl = live[2] 
        title = live[1] + " - " + live[12] + " (" + live[11][11:] + ")"
        liStyle = xbmcgui.ListItem(title, thumbnailImage=imageUrl)
        addLinkItem(link, liStyle)
    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

show_root_menu()

