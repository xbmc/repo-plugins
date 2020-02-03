#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from future import standard_library

standard_library.install_aliases()
from builtins import object
import os
import sys
import urllib.request, urllib.parse, urllib.error
import xbmcgui
import xbmcplugin

from dumpert_const import LANGUAGE, IMAGES_PATH, DAY, WEEK, MONTH, LATEST_URL, TOPPERS_URL, DUMPERT_TV_URL, SEARCH_URL

#
# Main class
#
class Main(object):
    def __init__(self):
        # Get the command line arguments
        # Get the plugin url in plugin:// notation
        self.plugin_url = sys.argv[0]
        # Get the plugin handle as an integer number
        self.plugin_handle = int(sys.argv[1])

        #
        # Nieuw
        #
        title = LANGUAGE(30001)
        parameters = {"action": "json",
                      "plugin_category": title,
                      "url": LATEST_URL,
                      "next_page_possible": "True"}
        self.add_dir(parameters, title)

        #
        # Dumpert TV
        #
        title = LANGUAGE(30007)
        parameters = {"action": "json",
                      "plugin_category": title,
                      "url": DUMPERT_TV_URL,
                      "next_page_possible": "True"}
        self.add_dir(parameters, title)

        #
        # Dag Toppers
        #
        title = LANGUAGE(30008)
        parameters = {"action": "json",
                      "plugin_category": title,
                      "period": DAY,
                      "days_deducted_from_today": "0",
                      "next_page_possible": "True"}
        self.add_dir(parameters, title)

        #
        # Week Toppers
        #
        title = LANGUAGE(30009)
        parameters = {"action": "json",
                      "plugin_category": title,
                      "period": WEEK,
                      "days_deducted_from_today": "0",
                      "next_page_possible": "True"}
        self.add_dir(parameters, title)

        #
        # Maand Toppers
        #
        title = LANGUAGE(30010)
        parameters = {"action": "json",
                      "plugin_category": title,
                      "period": MONTH,
                      "days_deducted_from_today": "0",
                      "next_page_possible": "True"}
        self.add_dir(parameters, title)

        #
        # Timemachine: Toppers for a given date
        #
        title = LANGUAGE(30005)
        parameters = {"action": "timemachine",
                      "plugin_category": title,
                      "next_page_possible": "True"}
        self.add_dir(parameters, title)

        #
        # Search
        #
        title = LANGUAGE(30004)
        parameters = {"action": "search",
                      "plugin_category": title,
                      "url": SEARCH_URL,
                      "next_page_possible": "True"}
        self.add_dir(parameters, title)

        # Disable sorting
        xbmcplugin.addSortMethod(handle=self.plugin_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.plugin_handle)

    def add_dir(self, parameters, title):
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(title)
        thumbnail_url = 'DefaultFolder.png'
        list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                          'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        is_folder = True
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)