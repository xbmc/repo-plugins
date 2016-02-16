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

from botchamania_const import ADDON, SETTINGS, LANGUAGE, IMAGES_PATH, DATE, VERSION


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

        # #
        # # All Videos
        # #
        # parameters = {"action" : "list", "plugin_category" : LANGUAGE(30000), "url" : "http://botchamania.com/page/1/", "next_page_possible": "True"}
        # url = self.plugin_url + '?' + urllib.urlencode(parameters)
        # list_item = xbmcgui.ListItem( LANGUAGE(30000), iconImage="DefaultFolder.png" )
        # is_folder = True
        # list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        # list_item.setProperty('IsPlayable', 'false')
        # xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Botchamania
        #
        parameters = {"action": "list", "plugin_category": LANGUAGE(30001),
                      "url": "http://botchamania.com/category/botchamania/page/1/", "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30001), iconImage="DefaultFolder.png")
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # OSWReview
        #
        parameters = {"action": "list", "plugin_category": LANGUAGE(30002),
                      "url": "http://botchamania.com/category/oswreview/page/1/", "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30002), iconImage="DefaultFolder.png")
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # NerdSlam
        #
        parameters = {"action": "list", "plugin_category": LANGUAGE(30003),
                      "url": "http://botchamania.com/category/nerdslam/page/1/", "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30003), iconImage="DefaultFolder.png")
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        #   PPV Recaps
        #
        parameters = {"action": "list", "plugin_category": LANGUAGE(30008),
                      "url": "http://botchamania.com/category/ppv-recaps/page/1/", "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30008), iconImage="DefaultFolder.png")
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Botchamania Archive   
        #
        parameters = {"action": "list-archive", "plugin_category": LANGUAGE(30011),
                      "url": "http://botchamaniaarchive.com/", "next_page_possible": "False"}
        url = self.plugin_url + '?' + urllib.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30011), iconImage="DefaultFolder.png")
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Botchamania Archive Specials
        #
        parameters = {"action": "list-archive-specials", "plugin_category": LANGUAGE(30012),
                      "url": "http://www.botchamaniaarchive.com/category/specials/page/1/",
                      "next_page_possible": "False"}
        url = self.plugin_url + '?' + urllib.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30012), iconImage="DefaultFolder.png")
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        # Disable sorting
        xbmcplugin.addSortMethod(handle=self.plugin_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.plugin_handle)
