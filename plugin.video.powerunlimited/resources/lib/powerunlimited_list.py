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
import requests
import json

from resources.lib.powerunlimited_const import ADDON, IMAGES_PATH, HEADERS, VIDEO_LIST_PAGE_URL, convertToUnicodeString, log


#
# Main class
#
class Main(object):
    #
    # Init
    #
    def __init__(self):
        # Get the command line arguments
        # Get the plugin url in plugin:// notation
        self.plugin_url = sys.argv[0]
        # Get the plugin handle as an integer number
        self.plugin_handle = int(sys.argv[1])

        log("ARGV", repr(sys.argv))

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
        # Create a list for our items
        listing = []

        #
        # Get HTML page
        #
        response = requests.get(VIDEO_LIST_PAGE_URL, headers=HEADERS)

        html_source = response.text
        html_source = convertToUnicodeString(html_source)

        # let's try and select the json containing all the needed data from the web page source
        index_start = html_source.find('{"props"')
        # log("index", index_start)
        index_end = html_source.rfind('}')
        # log("index", index_end)
        json_data = html_source[index_start:index_end + 1]
        # log("json_data", json_data)

        # load the json into the json parser
        data = json.loads(json_data)

        # Access the "mp4Url" properties for each video
        mp4_urls = [video['video']['video']['mp4Url'] for video in data['props']['pageProps']['_resources']['videos']]
        # log("mp4_urls", mp4_urls)

        # Access the "thumbnailUrl" properties for each video
        thumbnail_urls = [video['video']['video']['thumbnailUrl'] for video in data['props']['pageProps']['_resources']['videos']]
        # log("thumbnail_urls", thumbnail_urls)

        # Access the "title" properties for each video
        titles = [video['title'] for video in data['props']['pageProps']['_resources']['videos']]
        # log("titles", titles)

        mp4_urls_index = 0
        for mp4_url in mp4_urls:

            log("mp4_url", mp4_url)
            title = titles[mp4_urls_index]
            thumbnail_url = thumbnail_urls[mp4_urls_index]
            video_page_url = mp4_urls[mp4_urls_index]

            # Add to list
            list_item = xbmcgui.ListItem(label=title)
            list_item.setInfo("video", {"title": title, "studio": ADDON})
            list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                              'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'true')
            parameters = {"action": "play", "video_page_url": video_page_url}
            url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
            is_folder = False
            # Add refresh option to context menu
            list_item.addContextMenuItems([('Refresh', 'Container.Refresh')])
            # Add our item to the listing as a 3-element tuple.
            listing.append((url, list_item, is_folder))

            mp4_urls_index = mp4_urls_index + 1

        # Add our listing to Kodi
        # Large lists and/or slower systems benefit from adding all items at once via addDirectoryItems
        # instead of adding one by ove via addDirectoryItem.
        xbmcplugin.addDirectoryItems(self.plugin_handle, listing, len(listing))
        # Disable sorting
        xbmcplugin.addSortMethod(handle=self.plugin_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.plugin_handle)