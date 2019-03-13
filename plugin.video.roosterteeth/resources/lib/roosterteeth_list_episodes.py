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

from roosterteeth_const import IMAGES_PATH, HEADERS, LANGUAGE, convertToUnicodeString, log, \
    SPONSOR_ONLY_VIDEO_TITLE_PREFIX, ROOSTERTEETH_BASE_URL


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
        self.url = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['url'][0]
        self.next_page_possible = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['next_page_possible'][0]
        self.show_serie_name = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['show_serie_name'][0]

        # log("self.url", self.url)

        # log("self.show_serie_name", self.show_serie_name)

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
        response = requests.get(self.url, headers=HEADERS)

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

            episode_title = item['attributes']['title']

            caption = item['attributes']['caption']

            length = item['attributes']['length']

            channel_slug = item['attributes']['channel_slug']

            # the url should be something like:
            # https://svod-be.roosterteeth.com/api/v1/episodes/ffc530d0-464d-11e7-a302-065410f210c4/videos"
            # or even
            # https://svod-be.roosterteeth.com/api/v1/episodes/lets-play-2011-2/videos
            technical_episode_url_last_part = item['links']['videos']
            technical_episode_url = ROOSTERTEETH_BASE_URL + technical_episode_url_last_part
            technical_url = technical_episode_url

            log("technical_url", technical_url)

            functional_episode_url_middle_part = item['links']['self']
            functional_url = ROOSTERTEETH_BASE_URL + functional_episode_url_middle_part + '/videos'

            log("functional_url", functional_url)

            thumb = item['included']['images'][0]['attributes']['thumb']

            serie_title = item['attributes']['show_title']

            is_sponsor_only = item['attributes']['is_sponsors_only']

            # let's put some more info in the title of the episode
            if self.show_serie_name == "True":
                title = serie_title + ' - ' + episode_title
            else:
                title = episode_title

            if is_sponsor_only:
                title = SPONSOR_ONLY_VIDEO_TITLE_PREFIX + ' ' + title

            title = convertToUnicodeString(title)

            thumbnail_url = thumb

            plot = caption

            duration_in_seconds = length

            studio = channel_slug
            studio = convertToUnicodeString(studio)
            studio = studio.replace("-", " ")
            studio = studio.capitalize()

            # Add to list...
            list_item = xbmcgui.ListItem(label=title, thumbnailImage=thumbnail_url)
            list_item.setInfo("video",
                             {"title": title, "studio": studio, "mediatype": "video",
                              "plot": plot, "duration": duration_in_seconds})
            list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                             'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'true')

            # let's remove any non-ascii characters from the title, to prevent errors with urllib.parse.parse_qs
            # of the parameters
            title = title.encode('ascii', 'ignore')

            parameters = {"action": "play", "functional_url": functional_url, "technical_url": technical_url,
                          "title": title, "is_sponsor_only": is_sponsor_only, "next_page_possible": "False"}

            plugin_url_with_parms = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
            is_folder = False
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