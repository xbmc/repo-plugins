#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
import os
import requests
import sys
import urllib
import urlparse
import re
import xbmc
import xbmcgui
import xbmcplugin
from BeautifulSoup import BeautifulSoup

from hak5_const import ADDON, DATE, VERSION, IMAGES_PATH, HEADERS, HAK5SEASONSURLHTTPS, LANGUAGE

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

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % (
                ADDON, VERSION, DATE, "ARGV", repr(sys.argv), "File", str(__file__)), xbmc.LOGDEBUG)

        # Parse parameters...
        self.plugin_category = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['plugin_category'][0]
        self.video_list_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['url'][0]
        self.next_page_possible = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['next_page_possible'][0]

        self.video_list_page_url = str(self.video_list_page_url).replace('https', 'http')

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "self.video_list_page_url", str(self.video_list_page_url)),
                     xbmc.LOGDEBUG)

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
        # Get HTML page...
        #
        response = requests.get(self.video_list_page_url, headers=HEADERS)
        html_source = response.text
        html_source = html_source.encode('utf-8', 'ignore')

        # <a href="https://www.hak5.org/category/episodes/season-22" class="menu-link  sub-menu-link">Season 22 </a>

        # Parse response...
        soup = BeautifulSoup(html_source)

        # xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
        #     ADDON, VERSION, DATE, "html_source", str(html_source)), xbmc.LOGDEBUG)

        #<a href="https://www.hak5.org/category/episodes/season_1" data-ss1507745229="1">Season 1</a>
        seasons = soup.findAll('a', attrs={'href': re.compile("^" + "https://www.hak5.org/category/episodes/season")})

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "len(seasons)", str(len(seasons))), xbmc.LOGDEBUG)

        for season in seasons:

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "season", str(season)), xbmc.LOGDEBUG)

            # let's skip these links
            # <a href="https://www.hak5.org/category/episodes/season-22" class="menu-link  sub-menu-link">Season 22 </a>
            if str(season).find("class=") > 0:
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "skipped season that contains class=", str(season)), xbmc.LOGDEBUG)
                continue

            # let's skip these links
            # <a href="https://www.hak5.org/category/episodes/season-22" rel="category tag">Season 22</a>
            if str(season).find("rel=") > 0:
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "skipped season that contains rel=", str(season)), xbmc.LOGDEBUG)
                continue

            # let's skip links that don't contain the word season
            # <a title="Pineapple Uni" href="https://www.hak5.org/category/episodes/pineapple-university">Pineapple Uni</a>
            if str(season).find("season") > 0:
                pass
            else:
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "skipped season that does not contain the word season", str(season)), xbmc.LOGDEBUG)
                continue

            url = season['href']
            thumbnail_url = ''
            title = season.text

            add_sort_methods()

            context_menu_items = []
            # Add refresh option to context menu
            context_menu_items.append((LANGUAGE(30104), 'Container.Refresh'))

            # Add to list...
            list_item = xbmcgui.ListItem(label=title, thumbnailImage=thumbnail_url)
            list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                              'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'false')
            parameters = {"action": "list-episodes", "season_name": title, "url": url, "next_page_possible": "False",
                          "title": title}
            url = self.plugin_url + '?' + urllib.urlencode(parameters)
            is_folder = True
            # Adding context menu items to context menu
            list_item.addContextMenuItems(context_menu_items, replaceItems=False)
            # Add our item to the listing as a 3-element tuple.
            listing.append((url, list_item, is_folder))

        # Add our listing to Kodi.
        # Large lists and/or slower systems benefit from adding all items at once via addDirectoryItems
        # instead of adding one by ove via addDirectoryItem.
        xbmcplugin.addDirectoryItems(self.plugin_handle, listing, len(listing))
        # Disable sorting
        xbmcplugin.addSortMethod(handle=self.plugin_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.plugin_handle)

def add_sort_methods():
	sort_methods = [xbmcplugin.SORT_METHOD_UNSORTED,xbmcplugin.SORT_METHOD_LABEL,xbmcplugin.SORT_METHOD_DATE,xbmcplugin.SORT_METHOD_DURATION,xbmcplugin.SORT_METHOD_EPISODE]
	for method in sort_methods:
		xbmcplugin.addSortMethod(int(sys.argv[1]), sortMethod=method)