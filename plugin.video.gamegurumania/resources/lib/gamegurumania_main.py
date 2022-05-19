#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import object
from .gamegurumania_const import LANGUAGE, IMAGES_PATH
import sys
import urllib.request, urllib.parse, urllib.error
import xbmcgui
import xbmcplugin
import os


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
        # All Videos
        #
        parameters = {"action": "list-play", "plugin_category": LANGUAGE(30000),
                      "url": "https://www.ggmania.com/more.php3?next=000", "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30000), iconImage="DefaultFolder.png")
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Movie
        #
        parameters = {"action": "list-play", "plugin_category": LANGUAGE(30001),
                      "url": "https://www.ggmania.com/more.php3?next=000&kategory=movie", "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30001), iconImage="DefaultFolder.png")
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Console
        #
        parameters = {"action": "list-play", "plugin_category": LANGUAGE(30002),
                      "url": "https://www.ggmania.com/more.php3?next=000&kategory=console", "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30002), iconImage="DefaultFolder.png")
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Preview
        #
        parameters = {"action": "list-play", "plugin_category": LANGUAGE(30003),
                      "url": "https://www.ggmania.com/more.php3?next=000&kategory=preview", "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30003), iconImage="DefaultFolder.png")
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Tech
        #
        parameters = {"action": "list-play", "plugin_category": LANGUAGE(30004),
                      "url": "https://www.ggmania.com/more.php3?next=000&kategory=tech", "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30004), iconImage="DefaultFolder.png")
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Demo
        #
        parameters = {"action": "list-play", "plugin_category": LANGUAGE(30005),
                      "url": "https://www.ggmania.com/more.php3?next=000&kategory=demo", "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30005), iconImage="DefaultFolder.png")
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Interview
        #
        parameters = {"action": "list-play", "plugin_category": LANGUAGE(30006),
                      "url": "https://www.ggmania.com/more.php3?next=000&kategory=interview",
                      "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30006), iconImage="DefaultFolder.png")
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # FreeGame
        #
        parameters = {"action": "list-play", "plugin_category": LANGUAGE(30007),
                      "url": "https://www.ggmania.com/more.php3?next=000&kategory=freegame",
                      "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30007), iconImage="DefaultFolder.png")
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Media
        #
        parameters = {"action": "list-play", "plugin_category": LANGUAGE(30008),
                      "url": "https://www.ggmania.com/more.php3?next=000&kategory=media", "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30008), iconImage="DefaultFolder.png")
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Gold
        #
        parameters = {"action": "list-play", "plugin_category": LANGUAGE(30009),
                      "url": "https://www.ggmania.com/more.php3?next=000&kategory=gold", "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30009), iconImage="DefaultFolder.png")
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        # Disable sorting
        xbmcplugin.addSortMethod(handle=self.plugin_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.plugin_handle)
