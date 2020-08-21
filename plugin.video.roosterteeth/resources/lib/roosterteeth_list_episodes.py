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

from resources.lib.roosterteeth_const import RESOURCES_PATH, HEADERS, LANGUAGE, convertToUnicodeString, log, \
    FIRST_MEMBER_ONLY_VIDEO_TITLE_PREFIX, ROOSTERTEETH_BASE_URL


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

        # log("self.next_page_possible", self.next_page_possible)

        # Make the next page url
        if self.next_page_possible == 'True':
            # Determine current item number, next item number, next_url
            pos_of_page = self.url.rfind('page=')

            # log("pos_of_page", pos_of_page)

            if pos_of_page >= 0:
                page_number_str = str(
                    self.url[pos_of_page + len('page='):pos_of_page + len('page=') + len('000')])
                page_number = int(page_number_str)
                self.page_number_next = page_number + 1
                if self.page_number_next >= 100:
                    page_number_next_str = str(self.page_number_next)
                elif self.page_number_next >= 10:
                    page_number_next_str = '0' + str(self.page_number_next)
                else:
                    page_number_next_str = '00' + str(self.page_number_next)

                self.next_url = self.url.replace('page=' + page_number_str, 'page=' + page_number_next_str)

                # log("self.next_url", self.next_url)

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
        except (ValueError, KeyError, TypeError):
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30109))
            exit(1)

        for item in json_data['data']:

            # log("item", item)

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

            original_air_date = item['attributes']['original_air_date']
            original_air_date = original_air_date[0:10]

            # The backend still calls it sponsor instead of first member
            is_first_member_only = item['attributes']['is_sponsors_only']

            # let's put some more info in the title of the episode
            if self.show_serie_name == "True":
                title = serie_title + ' - ' + episode_title
            else:
                title = episode_title

            if is_first_member_only:
                title = FIRST_MEMBER_ONLY_VIDEO_TITLE_PREFIX + ' ' + title

            title = convertToUnicodeString(title)

            thumbnail_url = thumb

            plot = caption

            duration_in_seconds = length

            studio = channel_slug
            studio = convertToUnicodeString(studio)
            studio = studio.replace("-", " ")
            studio = studio.capitalize()

            # Add to list...
            list_item = xbmcgui.ListItem(title)
            list_item.setInfo("video",
                             {"title": title, "studio": studio, "mediatype": "video", \
                              "plot": plot + '\n' + LANGUAGE(30318) + ' ' + original_air_date, \
                              "aired": original_air_date, "duration": duration_in_seconds})
            list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                             'fanart': os.path.join(RESOURCES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'true')

            # let's remove any non-ascii characters from the title, to prevent errors with urllib.parse.parse_qs
            # of the parameters
            title = title.encode('ascii', 'ignore')

            parameters = {"action": "play", "functional_url": functional_url, "technical_url": technical_url,
                          "title": title, "is_first_member_only": is_first_member_only, "next_page_possible": "False"}

            plugin_url_with_parms = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
            is_folder = False
            # Add refresh option to context menu
            list_item.addContextMenuItems([('Refresh', 'Container.Refresh')])
            # Add our item to the listing as a 3-element tuple.
            listing.append((plugin_url_with_parms, list_item, is_folder))

        # Make a next page item, if a next page is possible
        total_pages_str = json_data['total_pages']
        total_pages = int(total_pages_str)
        if self.page_number_next <= total_pages:
            # Next page entry
            if self.next_page_possible == 'True':
                list_item = xbmcgui.ListItem(LANGUAGE(30200))
                list_item.setArt({'thumb': os.path.join(RESOURCES_PATH, 'next-page.png'),
                                 'fanart': os.path.join(RESOURCES_PATH, 'fanart-blur.jpg')})
                list_item.setProperty('IsPlayable', 'false')
                parameters = {"action": "list-episodes", "url": str(self.next_url),
                              "next_page_possible": self.next_page_possible, "show_serie_name": self.show_serie_name}
                url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
                is_folder = True
                # Add refresh option to context menu
                list_item.addContextMenuItems([('Refresh', 'Container.Refresh')])
                # Add our item to the listing as a 3-element tuple.
                listing.append((url, list_item, is_folder))

        # Add our listing to Kodi.
        # Large lists and/or slower systems benefit from adding all items at once via addDirectoryItems
        # instead of adding one by ove via addDirectoryItem.
        xbmcplugin.addDirectoryItems(self.plugin_handle, listing, len(listing))
        # Set initial sorting
        xbmcplugin.addSortMethod(handle=self.plugin_handle, sortMethod=xbmcplugin.SORT_METHOD_DATEADDED)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.plugin_handle)