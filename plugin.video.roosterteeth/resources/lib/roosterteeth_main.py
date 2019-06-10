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

from roosterteeth_const import LANGUAGE, IMAGES_PATH, ROOSTERTEETH_SERIES_URL, \
    ROOSTERTEETH_RECENTLY_ADDED_VIDEOS_SERIES_URL, ACHIEVEMENTHUNTER_RECENTLY_ADDED_VIDEOS_SERIES_URL, \
    FUNHAUS_RECENTLY_ADDED_VIDEOS_SERIES_URL, INSIDE_GAMING_RECENTLY_ADDED_VIDEOS_SERIES_URL, \
    SCREWATTACK_RECENTLY_ADDED_VIDEOS_SERIES_URL, SUGARPINE7_RECENTLY_ADDED_VIDEOS_SERIES_URL, \
    COWCHOP_RECENTLY_ADDED_VIDEOS_SERIES_URL, JTMUSIC_RECENTLY_ADDED_VIDEOS_SERIES_URL, \
    KINDAFUNNY_RECENTLY_ADDED_VIDEOS_SERIES_URL, ROOSTERTEETH_GET_EVERYTHING_IN_ONE_PAGE_URL_PART, \
    ROOSTERTEETH_ORDER_URL_PART


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
        # Roosterteeth Recently Added Episodes
        #
        parameters = {"action": "list-episodes", "plugin_category": LANGUAGE(30301),
                      "url": ROOSTERTEETH_RECENTLY_ADDED_VIDEOS_SERIES_URL,
                      "show_serie_name": "True", "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30301))
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Series
        #
        parameters = {"action": "list-series", "plugin_category": LANGUAGE(30302),
                      "url": ROOSTERTEETH_SERIES_URL + ROOSTERTEETH_GET_EVERYTHING_IN_ONE_PAGE_URL_PART +
                             ROOSTERTEETH_ORDER_URL_PART,
                      "show_serie_name": "True", "next_page_possible": "False"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30302))
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Achievement Hunter Recently Added Episodes
        #
        parameters = {"action": "list-episodes", "plugin_category": LANGUAGE(30303),
                      "url": ACHIEVEMENTHUNTER_RECENTLY_ADDED_VIDEOS_SERIES_URL,
                      "show_serie_name": "True", "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30303))
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Fun Haus Recently Added Episodes
        #
        parameters = {"action": "list-episodes", "plugin_category": LANGUAGE(30305),
                      "url": FUNHAUS_RECENTLY_ADDED_VIDEOS_SERIES_URL,
                      "show_serie_name": "True", "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30305))
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Inside Gaming Recently Added Episodes
        #
        parameters = {"action": "list-episodes", "plugin_category": LANGUAGE(30315),
                      "url": INSIDE_GAMING_RECENTLY_ADDED_VIDEOS_SERIES_URL,
                      "show_serie_name": "True", "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30315))
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Screw Attack Recently Added Episodes
        #
        parameters = {"action": "list-episodes", "plugin_category": LANGUAGE(30307),
                      "url": SCREWATTACK_RECENTLY_ADDED_VIDEOS_SERIES_URL,
                      "show_serie_name": "True", "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30307))
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Sugar Pine 7 Recently Added Episodes
        #
        parameters = {"action": "list-episodes", "plugin_category": LANGUAGE(30311),
                      "url": SUGARPINE7_RECENTLY_ADDED_VIDEOS_SERIES_URL,
                      "show_serie_name": "True", "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30311))
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Cow Chop Recently Added Episodes
        #
        parameters = {"action": "list-episodes", "plugin_category": LANGUAGE(30309),
                      "url": COWCHOP_RECENTLY_ADDED_VIDEOS_SERIES_URL,
                      "show_serie_name": "True", "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30309))
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # JT Music Recently Added Episodes
        #
        parameters = {"action": "list-episodes", "plugin_category": LANGUAGE(30317),
                      "url": JTMUSIC_RECENTLY_ADDED_VIDEOS_SERIES_URL,
                      "show_serie_name": "True", "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30317))
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        #
        # Kinda Funny Recently Added Episodes
        #
        parameters = {"action": "list-episodes", "plugin_category": LANGUAGE(30319),
                      "url": KINDAFUNNY_RECENTLY_ADDED_VIDEOS_SERIES_URL,
                      "show_serie_name": "True", "next_page_possible": "True"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30319))
        is_folder = True
        list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        # Disable sorting
        xbmcplugin.addSortMethod(handle=self.plugin_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.plugin_handle)