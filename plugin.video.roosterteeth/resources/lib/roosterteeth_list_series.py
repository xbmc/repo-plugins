#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from future import standard_library

standard_library.install_aliases()
from builtins import object
import os
import requests
import sys
import urllib.request, urllib.parse, urllib.error
import xbmcgui
import xbmcplugin
import json

from roosterteeth_const import RESOURCES_PATH, HEADERS, LANGUAGE, convertToUnicodeString, log, \
    ROOSTERTEETH_SERIES_BASE_URL, ROOSTERTEETH_GET_EVERYTHING_IN_ONE_PAGE_URL_PART, ROOSTERTEETH_ORDER_URL_PART


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

        # log("ARGV", repr(sys.argv))
        #
        # Parse parameters...
        self.plugin_category = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['plugin_category'][0]
        self.video_list_page_url = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['url'][0]
        self.next_page_possible = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['next_page_possible'][
            0]

        log("self.url", self.video_list_page_url)

        #
        # Get the videos...
        #
        self.getVideos()

    #
    # Get videos...
    #
    def getVideos(self):
        #
        # Init
        #
        # Create a list for our items.
        listing = []

        #
        # Get HTML page
        #
        response = requests.get(self.video_list_page_url, headers=HEADERS)

        html_source = response.text
        html_source = convertToUnicodeString(html_source)

        # log("html_source", html_source)

        try:
            json_data = json.loads(html_source)
        except (ValueError, KeyError, TypeError):
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30109))
            exit(1)

        for item in json_data['data']:
            serie_title = item['attributes']['title']

            summary = item['attributes']['summary']
            last_episode_golive_at = item['attributes']['last_episode_golive_at']
            last_episode_golive_at = last_episode_golive_at[0:10]

            # this part looks like this f.e.: /series/nature-town
            serie_url_middle_part = item['canonical_links']['self']
            serie_name = serie_url_middle_part.replace('/series/', '')

            # log("serie_url_middle_part", serie_url_middle_part)
            # log("serie_name", serie_name)

            # the serie url should become something like this:
            # https://svod-be.roosterteeth.com/api/v1/shows/nature-town/seasons?order=desc
            serie_url = ROOSTERTEETH_SERIES_BASE_URL + '/' + serie_name + '/' + 'seasons' \
                        + ROOSTERTEETH_GET_EVERYTHING_IN_ONE_PAGE_URL_PART + ROOSTERTEETH_ORDER_URL_PART

            thumb = item['included']['images'][0]['attributes']['thumb']

            title = serie_title

            url = serie_url

            thumbnail_url = thumb

            # Add to list...
            list_item = xbmcgui.ListItem(title)
            list_item.setInfo("video",
                             {"title": title, "mediatype": "video",
                              "plot": summary + '\n' + LANGUAGE(30319) + ' ' + last_episode_golive_at})
            list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                              'fanart': os.path.join(RESOURCES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'false')

            # let's remove any non-ascii characters from the title, to prevent errors with urllib.parse.parse_qs
            # of the parameters
            title = title.encode('ascii', 'ignore')

            parameters = {"action": "list-serie-seasons", "url": url, "title": title, "thumbnail_url": thumbnail_url,
                          "next_page_possible": "False"}
            plugin_url_with_parms = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
            is_folder = True
            # Add refresh option to context menu
            list_item.addContextMenuItems([('Refresh', 'Container.Refresh')])
            # Add our item to the listing as a 3-element tuple.
            listing.append((plugin_url_with_parms, list_item, is_folder))

        # Add our listing to Kodi.
        # Large lists and/or slower systems benefit from adding all items at once via addDirectoryItems
        # instead of adding one by ove via addDirectoryItem.
        xbmcplugin.addDirectoryItems(self.plugin_handle, listing, len(listing))
        # Set initial sorting
        xbmcplugin.addSortMethod(handle=self.plugin_handle, sortMethod=xbmcplugin.SORT_METHOD_DATEADDED)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.plugin_handle)