#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
import os
import re
import requests
import sys
import urllib
import urlparse
import xbmc
import xbmcgui
import xbmcplugin
from BeautifulSoup import BeautifulSoup
from datetime import datetime
import time

from dumpert_const import ADDON, SETTINGS, LANGUAGE, IMAGES_PATH, DATE, VERSION


#
# Main class
#
class Main:
    #
    # Init
    #
    def __init__(self):
        # Get the command line arguments
        # Get the plugin url in plugin:// notation
        self.plugin_url = sys.argv[0]
        # Get the plugin handle as an integer number
        self.plugin_handle = int(sys.argv[1])

        # Get plugin settings
        self.DEBUG = SETTINGS.getSetting('debug')

        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % (
                ADDON, VERSION, DATE, "ARGV", repr(sys.argv), "File", str(__file__)), xbmc.LOGNOTICE)

        date = xbmcgui.Dialog().numeric(1, LANGUAGE(30509))
        if not date is None:
            date = date.replace(' ', '')
            try:
                try:
                    date = datetime.strptime(date, '%d/%m/%Y')
                except TypeError:
                    date = datetime(*(time.strptime(date, '%d/%m/%Y')[0:6]))
            except ValueError:
                date = datetime.now()
        else:
            date = datetime.now()

        if date > datetime.now() or date < datetime(2006, 1, 1):
            date = datetime.now()

        #f.e. http://dumpert.nl/mobile_api/json/top5/dag/2016-03-20/0/
        daytop = 'http://dumpert.nl/mobile_api/json/top5/%s/%s/0/' % ('dag', date.strftime('%Y-%m-%d'))
        weektop = 'http://dumpert.nl/mobile_api/json/top5/%s/%s%s/0/' % (
        'week', date.strftime('%Y'), date.isocalendar()[1])
        monthtop = 'http://dumpert.nl/mobile_api/json/top5/%s/%s/0/' % ('maand', date.strftime('%Y%m'))

        title = LANGUAGE(30510) % date.strftime('%d %b %Y')
        # Next page is not available for top5
        parameters = {"action": "json", "plugin_category": title,
                      "url": daytop, "next_page_possible": "False"}
        url = self.plugin_url + '?' + urllib.urlencode(parameters)
        list_item = xbmcgui.ListItem(title, iconImage="DefaultFolder.png")
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        title = LANGUAGE(30511) % date.strftime('%d %b %Y')
        # Next page is not available for top5
        parameters = {"action": "json", "plugin_category": title,
                      "url": weektop, "next_page_possible": "False"}
        url = self.plugin_url + '?' + urllib.urlencode(parameters)
        list_item = xbmcgui.ListItem(title, iconImage="DefaultFolder.png")
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        title = LANGUAGE(30512) % date.strftime('%d %b %Y')
        # Next page is not available for top5
        parameters = {"action": "json", "plugin_category": title,
                      "url": monthtop, "next_page_possible": "False"}
        url = self.plugin_url + '?' + urllib.urlencode(parameters)
        list_item = xbmcgui.ListItem(title, iconImage="DefaultFolder.png")
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        # Disable sorting
        xbmcplugin.addSortMethod(handle=self.plugin_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.plugin_handle)