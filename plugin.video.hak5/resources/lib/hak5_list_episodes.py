#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import object
import os
import requests
import sys
import urllib.request, urllib.parse, urllib.error
import re
import xbmcgui
import xbmcplugin

from .hak5_const import ADDON, LANGUAGE, IMAGES_PATH, HEADERS, convertToUnicodeString, log, getSoup

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

        # Parse parameters
        self.video_list_page_url = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['url'][0]
        self.next_page_possible = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['next_page_possible'][0]

        self.video_list_page_url = str(self.video_list_page_url).replace('https', 'http')

        log("self.video_list_page_url", self.video_list_page_url)

        if self.next_page_possible == 'True':
            # Determine current item number, next item number, next_url
            pos_of_page = self.video_list_page_url.rfind('page/')
            if pos_of_page >= 0:
                page_number_str = str(
                    self.video_list_page_url[pos_of_page + len('page/'):pos_of_page + len('page/') + len('000')])
                page_number = int(page_number_str)
                page_number_next = page_number + 1
                if page_number_next >= 100:
                    page_number_next_str = str(page_number_next)
                elif page_number_next >= 10:
                    page_number_next_str = '0' + str(page_number_next)
                else:
                    page_number_next_str = '00' + str(page_number_next)
                self.next_url = str(self.video_list_page_url).replace(page_number_str, page_number_next_str)

                log("self.next_url", self.next_url)

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
        previous_video_page_url = ''
        after_tab_episodes = False
        # Create a list for our items.
        listing = []

        #
        # Get HTML page
        #
        response = requests.get(self.video_list_page_url, headers=HEADERS)

        html_source = response.text
        html_source = convertToUnicodeString(html_source)

        # Parse response
        soup = getSoup(html_source)

        episodes = soup.findAll('a', attrs={'class': re.compile("^" + 'tubepress-cursor-pointer')})

        log("len(episodes", len(episodes))

        for episode in episodes:

            # log("episode", episode)

            #video_page_url = episode.a['href']

            youtube_id = episode['class']
            youtube_id = youtube_id[2]
            youtube_id = convertToUnicodeString(youtube_id)
            start_pos_youtube_id = youtube_id.find("itemid-") + len("itemid-")
            youtube_id = youtube_id[start_pos_youtube_id:]
            youtube_url = 'plugin://plugin.video.youtube/play/?video_id=%s' % youtube_id
            video_page_url = youtube_url

            log("video_page_url", video_page_url)

            try:
                thumbnail_url = episode.img['src']
            except:
                # skip video page url without a thumbnail

                log("skipped video_page_url without a thumbnail", video_page_url)

                continue

            log("thumbnail_url", thumbnail_url)

            try:
                title = episode.img['alt']
                title = convertToUnicodeString(title)
            except:
                title = 'No title available'

            log("title", title)

            add_sort_methods()

            context_menu_items = []
            # Add refresh option to context menu
            context_menu_items.append((LANGUAGE(30104), 'Container.Refresh'))
            # Add episode  info to context menu
            context_menu_items.append((LANGUAGE(30105), 'XBMC.Action(Info)'))

            list_item = xbmcgui.ListItem(label=title, thumbnailImage=thumbnail_url)
            list_item.setInfo("video",
                              {"title": title, "studio": ADDON})
            list_item.setInfo("mediatype", "video")
            list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                              'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'true')

            # let's remove any non-ascii characters from the title, to prevent errors with urllib.parse.parse_qs of the parameters
            title = title.encode('ascii', 'ignore')

            parameters = {"action": "play", "video_page_url": video_page_url}
            url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
            is_folder = False
            # Adding context menu items to context menu
            list_item.addContextMenuItems(context_menu_items, replaceItems=False)
            # Add our item to the listing as a 3-element tuple.
            listing.append((url, list_item, is_folder))

        # Next page entry
        if self.next_page_possible == 'True':
            list_item = xbmcgui.ListItem(LANGUAGE(30200), thumbnailImage=os.path.join(IMAGES_PATH, 'next-page.png'))
            list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'false')
            parameters = {"action": "list-episodes", "url": str(self.next_url),
                          "next_page_possible": self.next_page_possible}
            url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
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