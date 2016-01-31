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
import re

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
    USERAGENT = "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:42.0) Gecko/20100101 Firefox/42.0"

    opener = urllib2.build_opener()
    # Use Firefox User-Agent
    opener.addheaders = [('User-Agent', USERAGENT)]
    urllib2.install_opener(opener)

    pageUrl = "http://sportube.tv/live"
    htmlData = urllib2.urlopen(pageUrl).read()
    match = re.compile('var base_url = "(.+?)"').findall(htmlData)
    baseUrl = match[0]
    match = re.compile('var API_KEY = "(.+?)"').findall(htmlData)
    apiKey = match[0]
    match = re.compile('var url_cdn = "(.+?)"').findall(htmlData)
    urlCdn = match[0]

    url = baseUrl + "tv.jsonp?callback=sportube_tv&api_key=" + apiKey
    headers = {'referer': pageUrl}
    request = urllib2.Request(url, headers = headers)
    data = urllib2.urlopen(request).read()
    # Convert JSONP object into JSON
    # https://stackoverflow.com/questions/30554522/django-parse-jsonp-json-with-padding
    data_json = data.split("(")[1].strip(")")
    response = json.loads(data_json)

    if "ERROR" in response:
        xbmc.log(msg="API Error: " + response["ERROR"])
    else:
        # Parse video feed
        for live in response["RESULT"]:
            link = live[4]
            imageUrl = live[2]
            title = live[1] + " - " + live[13] + " (" + live[12][11:16] + ")"
            liStyle = xbmcgui.ListItem(title, thumbnailImage=imageUrl)
            addLinkItem(link, liStyle)
    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

show_root_menu()

