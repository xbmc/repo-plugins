#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
import sys
import urllib
import xbmcgui
import xbmcplugin
import os

from hak5_const import LANGUAGE, IMAGES_PATH, HAK5RECENTLYADDEDURL, HAK5SEASONSURLHTTPS, \
    HAKTIKRECENTLYADDEDURL, THREATWIRERECENTLYADDEDURL, TEKTHINGRECENTLYADDEDURL, PINEAPPLEUNIVERSITYRECENTLYADDEDURL, \
    METASPLOITRECENTLYADDEDURL
#
# Main class
#
class Main:
    def __init__(self):
        # Get the command line arguments
        # Get the plugin url in plugin:// notation
        self.plugin_url = sys.argv[0]
        # Get the plugin handle as an integer number
        self.plugin_handle = int(sys.argv[1])

        #
        # Hak5 Recently Added Episodes
        #
        parameters = {"action": "list-episodes", "plugin_category": LANGUAGE(30301), "url": HAK5RECENTLYADDEDURL,
                      "next_page_possible": "False"}
        url = self.plugin_url + '?' + urllib.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30301))
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Hak5 Seasons
        #
        parameters = {"action": "list-seasons", "plugin_category": LANGUAGE(30302), "url": HAK5SEASONSURLHTTPS,
                      "next_page_possible": "False"}
        url = self.plugin_url + '?' + urllib.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30302))
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Haktik Recently Added Episodes
        #
        parameters = {"action": "list-episodes", "plugin_category": LANGUAGE(30303),
                      "url": HAKTIKRECENTLYADDEDURL,
                      "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30303))
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Threatwire Recently Added Episodes
        #
        parameters = {"action": "list-episodes", "plugin_category": LANGUAGE(30304), "url": THREATWIRERECENTLYADDEDURL,
                      "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30304))
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Tekthing Recently Added Episodes
        #
        parameters = {"action": "list-episodes", "plugin_category": LANGUAGE(30305), "url": TEKTHINGRECENTLYADDEDURL,
                      "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30305))
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Metasploit Recently Added Episodes
        #
        parameters = {"action": "list-episodes", "plugin_category": LANGUAGE(30307), "url": METASPLOITRECENTLYADDEDURL,
                      "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30307))
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        # Disable sorting
        xbmcplugin.addSortMethod(handle=self.plugin_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.plugin_handle)
