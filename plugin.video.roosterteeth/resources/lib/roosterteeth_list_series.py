#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from future import standard_library

standard_library.install_aliases()
from builtins import str
from builtins import object
import os
import requests
import sys
import urllib.request, urllib.parse, urllib.error
import xbmcgui
import xbmcplugin
import json

from roosterteeth_const import IMAGES_PATH, HEADERS, LANGUAGE, convertToUnicodeString, log, ROOSTERTEETH_SERIES_BASE_URL


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

        log("ARGV", repr(sys.argv))

        # Parse parameters...
        self.plugin_category = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['plugin_category'][0]
        self.video_list_page_url = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['url'][0]
        self.next_page_possible = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['next_page_possible'][0]

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

            # for item in json_data['data']:
            #     log("attribute1", item['canonical_links']['self'])
            #     log("attribute2", item['attributes']['title'])
            #     exit(1)

        except (ValueError, KeyError, TypeError):
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30109))
            exit(1)

        for item in json_data['data']:
            serie_title = item['attributes']['title']

            serie_url_middle_part = item['canonical_links']['self']
            # the serie url should something like this:
            # https://svod-be.roosterteeth.com/api/v1/shows/always-open/seasons
            serie_url = ROOSTERTEETH_SERIES_BASE_URL + serie_url_middle_part + '/seasons'
            # remove '/series/' from the url
            serie_url = serie_url.replace('/series/', '/')

            thumb = item['included']['images'][0]['attributes']['thumb']

            title = serie_title

            log("title", title)

            url = serie_url

            log("url", url)

            thumbnail_url = thumb

            log("thumbnail_url", thumbnail_url)

            # Add to list...
            list_item = xbmcgui.ListItem(label=title, thumbnailImage=thumbnail_url)
            list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                              'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'false')

            # let's remove any non-ascii characters from the title, to prevent errors with urllib.parse.parse_qs
            # of the parameters
            title = title.encode('ascii', 'ignore')

            parameters = {"action": "list-serie-seasons", "url": url, "title": title, "thumbnail_url": thumbnail_url ,
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
        # Disable sorting
        xbmcplugin.addSortMethod(handle=self.plugin_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.plugin_handle)