#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from future import standard_library

standard_library.install_aliases()
from builtins import object
import sys
import requests
import urllib.request, urllib.parse, urllib.error
import xbmcgui
import xbmcplugin
import os
import json

from roosterteeth_const import HEADERS, LANGUAGE, RESOURCES_PATH, ROOSTERTEETH_CHANNELS_URL, ROOSTERTEETH_BASE_URL, \
ROOSTERTEETH_PAGE_URL_PART, ROOSTERTEETH_ORDER_URL_PART, ROOSTERTEETH_CHANNEL_URL_PART, \
ROOSTERTEETH_GET_EVERYTHING_IN_ONE_PAGE_URL_PART, ROOSTERTEETH_SERIES_URL, ROOSTERTEETH_SERIES_BASE_URL, \
convertToUnicodeString, log

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
        # Init
        #
        # Create a list for our items.
        listing = []

        #
        # Get HTML page
        #
        response = requests.get(ROOSTERTEETH_CHANNELS_URL, headers=HEADERS)

        html_source = response.text
        html_source = convertToUnicodeString(html_source)

        # log("html_source", html_source)

        try:
            json_data = json.loads(html_source)
        except (ValueError, KeyError, TypeError):
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30109))
            exit(1)

        for item in json_data['data']:
            thumb = item['included']['images'][0]['attributes']['large']
            channel_name = item['attributes']['name']
            channel_name_in_url = item['attributes']['slug']
            # channel_shows_link = item['links']['shows']
            channel_episodes_link = item['links']['episodes']
            title = channel_name.title() + ' ' + LANGUAGE(30321)

            # Add serie recently added episodes
            url_serie_recently_added_episodes = ROOSTERTEETH_BASE_URL + channel_episodes_link + \
                                                ROOSTERTEETH_PAGE_URL_PART + ROOSTERTEETH_ORDER_URL_PART + \
                                                ROOSTERTEETH_CHANNEL_URL_PART + channel_name_in_url

            # log("serie recently added episode url", url_serie_recently_added_episodes)

            thumbnail_url = thumb

            title = title.encode('ascii', 'ignore')

            parameters = {"action": "list-episodes", "plugin_category": title,
                          "url": url_serie_recently_added_episodes,
                          "show_serie_name": "True", "next_page_possible": "True"}
            list_item = xbmcgui.ListItem(title)
            list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                              'fanart': os.path.join(RESOURCES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'false')
            url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
            is_folder = True
            xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

            # Add serie shows
            title = channel_name.title() + ' ' + LANGUAGE(30302)
            # let's remove any non-ascii characters from the title, to prevent errors with urllib.parse.parse_qs
            # of the parameters
            title = title.encode('ascii', 'ignore')

            url_serie_shows = ROOSTERTEETH_SERIES_BASE_URL + ROOSTERTEETH_GET_EVERYTHING_IN_ONE_PAGE_URL_PART + \
                              ROOSTERTEETH_ORDER_URL_PART + ROOSTERTEETH_CHANNEL_URL_PART + channel_name_in_url

            # log("serie shows url", url_serie_shows)

            parameters = {"action": "list-series", "plugin_category": title,
                          "url": url_serie_shows,
                          "show_serie_name": "True", "next_page_possible": "True"}
            list_item = xbmcgui.ListItem(title)
            list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                              'fanart': os.path.join(RESOURCES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'false')
            url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
            is_folder = True
            xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        # Add Series
        url_series = ROOSTERTEETH_SERIES_URL + ROOSTERTEETH_GET_EVERYTHING_IN_ONE_PAGE_URL_PART + \
                     ROOSTERTEETH_ORDER_URL_PART
        parameters = {"action": "list-series", "plugin_category": LANGUAGE(30302),
                      "url": url_series, "show_serie_name": "True", "next_page_possible": "False"}
        url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
        list_item = xbmcgui.ListItem(LANGUAGE(30302))
        is_folder = True
        list_item.setArt({'fanart': os.path.join(RESOURCES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=url, listitem=list_item, isFolder=is_folder)

        # Set initial sorting
        xbmcplugin.addSortMethod(handle=self.plugin_handle, sortMethod=xbmcplugin.SORT_METHOD_DATEADDED)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.plugin_handle)