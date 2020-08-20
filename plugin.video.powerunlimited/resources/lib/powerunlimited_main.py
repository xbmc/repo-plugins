#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from future import standard_library
standard_library.install_aliases()
from builtins import object
import sys
import urllib.request, urllib.parse, urllib.error
import xbmcgui
import xbmcplugin
import os

from resources.lib.powerunlimited_const import LANGUAGE, IMAGES_PATH


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
        # Alles
        #
        parameters = {"action": "list", "plugin_category": LANGUAGE(30000),
                      "url": "http://www.pu.nl/media/?page=001", "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30000))
        is_folder = True
        list_item.setArt({'thumb': 'DefaultFolder.png', 'icon': 'DefaultFolder.png',
                          'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # PU-TV
        #
        parameters = {"action": "list", "plugin_category": LANGUAGE(30001),
                      "url": "http://www.pu.nl/media/pu-tv/?page=001", "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30001))
        is_folder = True
        list_item.setArt({'thumb': 'DefaultFolder.png', 'icon': 'DefaultFolder.png',
                          'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Trailers
        #
        parameters = {"action": "list", "plugin_category": LANGUAGE(30002),
                      "url": "http://www.pu.nl/media/trailer/?page=001", "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30002))
        is_folder = True
        list_item.setArt({'thumb': 'DefaultFolder.png', 'icon': 'DefaultFolder.png',
                          'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        # Disable sorting
        xbmcplugin.addSortMethod(handle=self.plugin_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.plugin_handle)
