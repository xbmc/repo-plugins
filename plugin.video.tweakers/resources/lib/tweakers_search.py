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
import re
import sys
import requests
import urllib.request, urllib.parse, urllib.error
import xbmc
import xbmcgui
import xbmcplugin

from resources.lib.tweakers_const import LANGUAGE, IMAGES_PATH, VERSION, convertToUnicodeString, log, getSoup


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
        try:
            self.plugin_category = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['plugin_category'][0]
            self.video_list_page_url = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['url'][0]
            self.next_page_possible = \
            urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['next_page_possible'][0]
        except:
            self.plugin_category = LANGUAGE(30000)
            self.next_page_possible = "True"
            # Get the search-string from the user
            keyboard = xbmc.Keyboard('', LANGUAGE(30103))
            keyboard.doModal()
            if keyboard.isConfirmed():
                self.search_string = keyboard.getText()
                self.video_list_page_url = "https://tweakers.net/video/zoeken?keyword=%s&page=001" % (
                    self.search_string)

        log("self.video_list_page_url", self.video_list_page_url)

        if self.next_page_possible == "True":
            # Determine current item number, next item number, next_url
            # f.e. https://www.tweakers.net/category/videos/page/001/
            pos_of_page = self.video_list_page_url.rfind('&page=')
            if pos_of_page >= 0:
                page_number_str = str(
                    self.video_list_page_url[pos_of_page + len('&page='):pos_of_page + len('&page=') + len('000')])
                page_number = int(page_number_str)
                page_number_next = page_number + 1
                if page_number_next >= 100:
                    page_number_next_str = str(page_number_next)
                elif page_number_next >= 10:
                    page_number_next_str = '0' + str(page_number_next)
                else:
                    page_number_next_str = '00' + str(page_number_next)
                self.next_url = self.video_list_page_url.replace(page_number_str, page_number_next_str)

                log("self.next_url", self.next_url)

        #
        # Get the videos
        #
        self.getVideos()

    #
    # Get videos
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
        # Make the headers
        xbmc_version = xbmc.getInfoLabel("System.BuildVersion")
        user_agent = "Kodi Mediaplayer %s / Tweakers Addon %s" % (xbmc_version, VERSION)
        headers = {"User-Agent": user_agent,
                   "Accept-Encoding": "gzip",
                   "X-Cookies-Accepted": "1"}

        # Disable ssl logging (this is needed for python version < 2.7.9 (SNIMissingWarning))
        import logging
        # On iOS the following logging command throws an exception. If that happens, ignore the exception...
        try:
            logging.captureWarnings(True)
        except Exception:

            log("logging exception occured (and ignored)", Exception)

            pass

        # Get HTML page
        response = requests.get(self.video_list_page_url, headers=headers)
        # response.status
        html_source = response.text
        html_source = convertToUnicodeString(html_source)

        # Parse response
        soup = getSoup(html_source)

        # <td class="video-image">
        # <a href="https://tweakers.net/video/16043/oneplus-5t-voor-wie-groter-altijd-beter-vindt.html" class="thumb video"
        # title="OnePlus 5T - Voor wie groter altijd beter vindt">
        # <img src="https://tweakers.net/i/BaASWTU0iU04bYUVfaeGvglzVmE=/124x70/filters:fill(white)/i/2001722571.jpeg?f=thumbs_video" width="124" height="70" alt="">
        # <span class="playtime">05:09</span></a>
        # </td>

        items = soup.findAll('td', attrs={'class': re.compile("^video-image")})

        log("len(items)", len(items))

        for item in items:
            video_page_url = item.a['href']

            # Make title
            title = item.a['title']

            log("title", title)

            thumbnail_url = item.img['src']
            thumbnail_url_str = str(thumbnail_url)
            start_pos_size = thumbnail_url_str.find('size=')
            if start_pos_size >= 0:
                end_pos_size = thumbnail_url_str.find('/', start_pos_size)
                # Let's use the thumbnail itself instead of a scaled down version of it by removing "/size=...x.../"
                thumbnail_url_new = thumbnail_url_str[0:start_pos_size - 1] + thumbnail_url_str[end_pos_size:]
                thumbnail_url = thumbnail_url_new

            log("thumbnail_url", thumbnail_url)

            # Determine video duration in seconds
            try:
                duration_in_mm_ss = item.span.text
                m, s = duration_in_mm_ss.split(':')
                duration_in_seconds = int(m) * 60 + int(s)
            except:
                duration_in_seconds = 0

            log("duration_in_seconds", duration_in_seconds)

            # Determine the plot
            plot = title

            log("plot", plot)

            list_item = xbmcgui.ListItem(title)
            list_item.setInfo("video", {"title": title, "studio": "Tweakers", "mediatype": "video", "plot": plot,
                                        "duration": duration_in_seconds})
            list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                              'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'true')

            # let's remove any non-ascii characters
            title = title.encode('ascii', 'ignore')

            parameters = {"action": "play", "video_page_url": video_page_url, "title": title}
            url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
            is_folder = False
            # Add refresh option to context menu
            list_item.addContextMenuItems([('Refresh', 'Container.Refresh')])
            # Add our item to the listing as a 3-element tuple.
            listing.append((url, list_item, is_folder))

        # Next page entry
        if self.next_page_possible == 'True':
            thumbnail_url = os.path.join(IMAGES_PATH, 'next-page.png')
            list_item = xbmcgui.ListItem(LANGUAGE(30503))
            list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                              'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'false')
            parameters = {"action": "search", "plugin_category": self.plugin_category, "url": str(self.next_url),
                          "next_page_possible": self.next_page_possible}
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
        # Disable sorting
        xbmcplugin.addSortMethod(handle=self.plugin_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.plugin_handle)
