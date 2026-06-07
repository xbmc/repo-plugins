#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from builtins import str, object
import os
import sys
import urllib.parse
import xbmcgui
import xbmcplugin
import requests
import json

# from future import standard_library
# standard_library.install_aliases()

# Import your custom modules
from resources.lib.worldstarhiphop_const import ADDON, SETTINGS, LANGUAGE, IMAGES_PATH, HEADERS, INITIAL_API_VIDEO_URL, add_video_to_listing, log

# Main class
class Main(object):
    """
    Main class for the Kodi addon.
    """
    def __init__(self):
        # Get the command line arguments
        # Get the plugin url in plugin:// notation
        self.plugin_url = sys.argv[0]
        # Get the plugin handle as an integer number
        self.plugin_handle = int(sys.argv[1])

        # Get plugin settings
        self.VIDEO = SETTINGS.getSetting('video')

        log("ARGV", repr(sys.argv))

        self.next_url = None

        # Parse parameters...
        # For the first fetch, assume there's a next page.
        # Check if sys.argv[2] is empty to identify the first call.
        if len(sys.argv[2]) == 0:
            self.plugin_category = LANGUAGE(30000)
            self.next_page_possible = 'True'
            self.video_list_page_url = INITIAL_API_VIDEO_URL
        else:
            self.plugin_category = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['plugin_category'][0]
            self.next_page_possible = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['next_page_possible'][0]
            self.video_list_page_url = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['url'][0]

        log("self.plugin_category", self.plugin_category)
        log("self.next_page_possible", self.next_page_possible)
        log("self.video_list_page_url", self.video_list_page_url)

        # Set search_mode switch to True if the items to be listed are the result of using the search function
        if "searchTerm" in self.video_list_page_url:
            self.list_search_results = True
        else:
            self.list_search_results = False

        log("self.search_mode", self.list_search_results)

        # Get the videos...
        self.getVideos()

    def getVideos(self):
        """Fetches video data and populates the Kodi directory listing."""
        # Init
        listing = []

        # Don't add a search item when processing search results
        if self.list_search_results:
            pass
        else:
            # Add Search item
            search_item_title = LANGUAGE(30103)
            search_item_url = f"{self.plugin_url}?{urllib.parse.urlencode({'action': 'search'})}"
            search_list_item = xbmcgui.ListItem(search_item_title)
            search_list_item.setArt({
                'thumb': '',
                'icon': '',
                'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')
            })
            search_list_item.setInfo("video", {"Title": search_item_title, "Studio": ADDON})
            xbmcplugin.addDirectoryItem(handle=self.plugin_handle, url=search_item_url, listitem=search_list_item, isFolder=True)

        # Get JSON data from the API
        try:
            response = requests.get(self.video_list_page_url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            json_data = response.json()
        except requests.exceptions.RequestException as e:
            log("ERROR", f"Request failed: {e}")
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30508))
            return
        except json.JSONDecodeError as e:
            log("ERROR", f"JSON decoding failed: {e}")
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30508))
            return

        log("json_data", json_data)

        # Get the cursor position for pagination
        # Note: This uses a try-except block to handle cases where 'page_cursor' is missing
        try:
            if self.list_search_results:
                page_cursor = json_data["videos"]["pageCursor"]
            else:
                page_cursor = json_data["pageCursor"]
            self.next_page_possible = 'True'
            # Construct the next page URL
            # Use urllib.parse to safely update the URL parameters
            parsed_url = list(urllib.parse.urlparse(self.video_list_page_url))
            query_params = urllib.parse.parse_qs(parsed_url[4])
            query_params['pageCursor'] = [page_cursor]
            parsed_url[4] = urllib.parse.urlencode(query_params, doseq=True)
            self.next_url = urllib.parse.urlunparse(parsed_url)
        except KeyError:
            page_cursor = ""
            self.next_page_possible = 'False'

        log("pageCursor", page_cursor)

        if self.list_search_results:
            # Process videos found using the search function
            for video in json_data.get("videos", {}).get("result", []):
                add_video_to_listing(video, self.plugin_url, listing, ADDON, IMAGES_PATH, log)
        else:
            # Process featured videos if present
            for video in json_data.get("featuredVideos", {}).get("hero", []):
                add_video_to_listing(video, self.plugin_url, listing, ADDON, IMAGES_PATH, log)

            # Process videos by date
            for date_group in json_data.get("videosByDate", []):
                log("Date", date_group.get('date', 'Unknown Date'))
                for video in date_group.get('videos', []):
                    add_video_to_listing(video, self.plugin_url, listing, ADDON, IMAGES_PATH, log)

        # Add the "Next Page" item if available
        if self.next_page_possible == 'True':
            log("self.next_url", self.next_url)
            next_page_thumbnail = os.path.join(IMAGES_PATH, 'next-page.png')
            next_page_item = xbmcgui.ListItem(LANGUAGE(30503))
            next_page_item.setArt({
                'thumb': next_page_thumbnail,
                'icon': next_page_thumbnail,
                'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')
            })
            next_page_item.setProperty('IsPlayable', 'false')

            next_page_params = {
                "action": "list",
                "plugin_category": self.plugin_category,
                "url": self.next_url,
                "next_page_possible": self.next_page_possible
            }
            next_page_url = f"{self.plugin_url}?{urllib.parse.urlencode(next_page_params)}"

            next_page_item.addContextMenuItems([('Refresh', 'Container.Refresh')])
            listing.append((next_page_url, next_page_item, True))

        # Add all items to the directory at once
        xbmcplugin.addDirectoryItems(self.plugin_handle, listing, len(listing))

        # Disable sorting and finalize the directory
        xbmcplugin.addSortMethod(handle=self.plugin_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.endOfDirectory(self.plugin_handle)