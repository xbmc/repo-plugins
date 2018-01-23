#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import range
from builtins import object
import os
import requests
import re
import sys
import urllib.request, urllib.parse, urllib.error
import xbmcgui
import xbmcplugin

from botchamania_const import LANGUAGE, IMAGES_PATH, ADDON, convertToUnicodeString, log, getSoup


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

        # Parse parameters...
        self.plugin_category = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['plugin_category'][0]
        self.video_list_page_url = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['url'][0]
        self.next_page_possible = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['next_page_possible'][0]

        log("self.video_list_page_url", self.video_list_page_url)

        # Determine current page number and base_url
        # find last slash
        pos_of_last_slash = self.video_list_page_url.rfind('/')
        # remove last slash
        self.video_list_page_url = self.video_list_page_url[0: pos_of_last_slash]
        pos_of_last_slash = self.video_list_page_url.rfind('/')
        self.base_url = self.video_list_page_url[0: pos_of_last_slash + 1]
        self.current_page = self.video_list_page_url[pos_of_last_slash + 1:]
        self.current_page = int(self.current_page)
        # add last slash
        self.video_list_page_url = str(self.video_list_page_url) + "/"

        log("self.base_url", self.base_url)

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
        list_item = ''
        # Create a list for our items.
        self.listing = []

        for num in range(self.current_page, 20):
            # http://www.botchamaniaarchive.com/category/specials/page/1/
            self.video_list_page_url = self.base_url + str(num)

            #
            # Get HTML page
            #
            try:
                response = requests.get(self.video_list_page_url)
            except:

                log("first non-existing archive special url", self.video_list_page_url)

                break

            html_source = response.text
            html_source = convertToUnicodeString(html_source)

            # Parse response
            self.soup = getSoup(html_source)

            self.addVideos()

        # Next page entry...
        if self.next_page_possible == 'True':
            next_page = self.current_page + 1
            parameters = {"action": "list-archive-specials", "plugin_category": self.plugin_category,
                          "url": str(self.base_url) + str(next_page) + '/',
                          "next_page_possible": self.next_page_possible}
            url = sys.argv[0] + '?' + urllib.parse.urlencode(parameters)
            list_item = xbmcgui.ListItem(LANGUAGE(30503), thumbnailImage=os.path.join(IMAGES_PATH, 'next-page.png'))
            is_folder = True
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=list_item, isFolder=is_folder)

            log("next url", url)

        # Add our listing to Kodi.
        # Large lists and/or slower systems benefit from adding all items at once via addDirectoryItems
        # instead of adding one by ove via addDirectoryItem.
        xbmcplugin.addDirectoryItems(self.plugin_handle, self.listing, len(self.listing))
        # Disable sorting
        xbmcplugin.addSortMethod(handle=self.plugin_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.plugin_handle)


    def addVideos(self):
        thumbnail_url = ""

        # 		<a class="clip-link" data-id="879" title="Vadermania" href="http://www.botchamaniaarchive.com/vadermania/">
        video_page_urls = self.soup.findAll('a', attrs={'class': re.compile("clip-link")})

        # dirty remove of the first 6 items
        if len(video_page_urls) >= 6:
            video_page_urls = video_page_urls[6:len(video_page_urls)]

        log("len(video_page_urls)", len(video_page_urls))

        for video_page_url in video_page_urls:
            video_page_url = video_page_url['href']
            video_page_url_str = str(video_page_url)
            if video_page_url_str.startswith("http://www.botchamaniaarchive.com/botchamania"):
                # Process the next video_page_url
                continue

            log( "video_page_url", video_page_url)

            title = video_page_url_str.replace("http://www.botchamaniaarchive.com/", "")
            title = title.replace('-', ' ')
            title = title.replace('/', ' ')
            title = title.replace('_', ' ')
            title = title.capitalize()

            # Add to list...
            list_item = xbmcgui.ListItem(label=title, thumbnailImage=thumbnail_url)
            list_item.setInfo("video", {"title": title, "studio": ADDON})
            list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                              'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'true')
            parameters = {"action": "play", "video_page_url": video_page_url, "title": title}
            url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
            is_folder = False
            # Add refresh option to context menu
            list_item.addContextMenuItems([('Refresh', 'Container.Refresh')])
            # Add our item to the listing as a 3-element tuple.
            self.listing.append((url, list_item, is_folder))
