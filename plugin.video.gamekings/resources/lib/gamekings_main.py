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

from gamekings_const import LANGUAGE, IMAGES_PATH, BASE_URL_GAMEKINGS_TV


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
        # Premium Videos
        #
        parameters = {"action": "list", "plugin_category": LANGUAGE(30005),
                      "url": BASE_URL_GAMEKINGS_TV + "category/premium/page/001/", "next_page_possible": "False"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30005))
        list_item.setArt({'thumb': "DefaultFolder.png", 'icon': "DefaultFolder.png",
                          'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        is_folder = True
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Videos on frontpage
        #
        # Sometimes videos are not present yet in the video category, but they are present on the frontpage of the site
        parameters = {"action": "list", "plugin_category": LANGUAGE(30006),
                      "url": BASE_URL_GAMEKINGS_TV, "next_page_possible": "False"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30006))
        list_item.setArt({'thumb': "DefaultFolder.png", 'icon': "DefaultFolder.png",
                          'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        is_folder = True
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Videos
        #
        parameters = {"action": "list", "plugin_category": LANGUAGE(30000),
                      "url": BASE_URL_GAMEKINGS_TV + "category/videos/page/001/", "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30000))
        list_item.setArt({'thumb': "DefaultFolder.png", 'icon': "DefaultFolder.png",
                          'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        is_folder = True
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Trailers
        #
        parameters = {"action": "list", "plugin_category": LANGUAGE(30003),
                      "url": BASE_URL_GAMEKINGS_TV + "?s=trailer", "next_page_possible": "False"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30003))
        list_item.setArt({'thumb': "DefaultFolder.png", 'icon': "DefaultFolder.png",
                          'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        is_folder = True
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Afleveringen
        #
        parameters = {"action": "list", "plugin_category": LANGUAGE(30001),
                      "url": BASE_URL_GAMEKINGS_TV + "page/001/?cat=3&s=gamekings+s", "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30001))
        list_item.setArt({'thumb': "DefaultFolder.png", 'icon': "DefaultFolder.png",
                          'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        is_folder = True
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Search in Videos
        #
        parameters = {"action": "search", "plugin_category": LANGUAGE(30004),
                      "url": BASE_URL_GAMEKINGS_TV + "?cat=3&s=%s", "next_page_possible": "False"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30004))
        list_item.setArt({'thumb': "DefaultFolder.png", 'icon': "DefaultFolder.png",
                          'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        is_folder = True
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        # Disable sorting
        xbmcplugin.addSortMethod(handle=self.plugin_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.plugin_handle)
