#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
import os
import re
import sys
import urllib
import urlparse
import xbmc
import xbmcgui
import xbmcplugin
from BeautifulSoup import BeautifulSoup

from botchamania_const import ADDON, SETTINGS, LANGUAGE, IMAGES_PATH, DATE, VERSION
from botchamania_utils import HTTPCommunicator


#
# Main class
#
class Main:
    #
    # Init
    #
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

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "self.video_list_page_url", str(self.video_list_page_url)),
                     xbmc.LOGDEBUG)

        # Determine base_url
        # find last slash
        pos_of_last_slash = self.video_list_page_url.rfind('/')
        # remove last slash
        self.video_list_page_url = self.video_list_page_url[0: pos_of_last_slash]
        pos_of_last_slash = self.video_list_page_url.rfind('/')
        self.base_url = self.video_list_page_url[0: pos_of_last_slash + 1]
        # add last slash
        self.video_list_page_url = str(self.video_list_page_url) + "/"

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "self.base_url", str(self.base_url)), xbmc.LOGDEBUG)

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
        current_page = 1
        # title = ""
        thumbnail_url = ""
        list_item = ''
        is_folder = False
        # Create a list for our items.
        listing = []

        #
        # Get HTML page...
        #
        html_source = HTTPCommunicator().get(self.video_list_page_url)

        # Parse response...
        soup = BeautifulSoup(html_source)

        # Find link with maximum category
        # <a href="http://www.botchamaniaarchive.com/category/51-100/">51-100</a></li>
        categories = soup.findAll('a', attrs={'href': re.compile("^http://www.botchamaniaarchive.com/category/")})

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "len(categories)", str(len(categories))), xbmc.LOGDEBUG)

        max_category_number = 0
        max_category = ""
        for category in categories:
            category_str = str(category)
            pos_of_dash = category_str.find('-')
            if pos_of_dash >= 0:
                try:
                    category_number = int(category_str[pos_of_dash + 1:pos_of_dash + 1 + 3])
                except:
                    category_number = 0
                if category_number > max_category_number:
                    max_category_number = category_number
                    max_category = category

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "max_category['href']", str(max_category['href'])), xbmc.LOGDEBUG)

        #
        # Get HTML page...
        #
        html_source = HTTPCommunicator().get(max_category['href'])

        # Parse response...
        soup = BeautifulSoup(html_source)

        #		<a class="clip-link" data-id="776" title="Botchamania 252" href="http://www.botchamaniaarchive.com/botchamania-252/">
        video_page_urls = soup.findAll('a',
                                       attrs={'href': re.compile("^http://www.botchamaniaarchive.com/botchamania-")})

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "len(video_page_urls)", str(len(video_page_urls))), xbmc.LOGDEBUG)

        max_video_page_url_number = 0
        max_video_page_url = ""
        for video_page_url in video_page_urls:
            video_page_url_str = str(video_page_url)
            pos_of_dash = video_page_url_str.find('http://www.botchamaniaarchive.com/botchamania-')
            if pos_of_dash >= 0:
                try:
                    video_page_url_number = int(video_page_url_str[pos_of_dash + len(
                        'http://www.botchamaniaarchive.com/botchamania-'):pos_of_dash + len(
                        'http://www.botchamaniaarchive.com/botchamania-') + 3])
                except:
                    video_page_url_number = 0
                if video_page_url_number > max_video_page_url_number:
                    max_video_page_url_number = video_page_url_number
                    max_video_page_url = video_page_url

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "max_video_page_url_number", str(max_video_page_url_number)), xbmc.LOGDEBUG)

        # http://www.botchamaniaarchive.com/botchamania-27/">
        BASE_URL = "http://www.botchamaniaarchive.com/botchamania-"
        BASE_TITLE = "Botchamania "

        for num in range(1, max_video_page_url_number + 1):
            if num == 1:
                title = str(BASE_TITLE) + '1-2-3'
                video_page_url = str(BASE_URL) + '1-2-3'
            elif num == 2:
                continue
            elif num == 3:
                continue
            else:
                title = str(BASE_TITLE) + str(num)
                video_page_url = str(BASE_URL) + str(num)

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "video_page_url", str(video_page_url)), xbmc.LOGDEBUG)

            # Add to list...
            list_item = xbmcgui.ListItem(label=title, thumbnailImage=thumbnail_url)
            list_item.setInfo("video", {"title": title, "studio": ADDON})
            list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                              'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'true')
            parameters = {"action": "play", "video_page_url": video_page_url, "title": title}
            url = self.plugin_url + '?' + urllib.urlencode(parameters)
            is_folder = False
            # Add refresh option to context menu
            list_item.addContextMenuItems([('Refresh', 'Container.Refresh')])
            # Add our item to the listing as a 3-element tuple.
            listing.append((url, list_item, is_folder))

        # Next page entry...
        if self.next_page_possible == 'True':
            next_page = current_page + 1
            list_item = xbmcgui.ListItem(LANGUAGE(30503), thumbnailImage=os.path.join(IMAGES_PATH, 'next-page.png'))
            list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'false')
            parameters = {"action": "list-specials", "plugin_category": self.plugin_category,
                          "url": str(self.base_url) + str(next_page) + '/',
                          "next_page_possible": self.next_page_possible}
            url = self.plugin_url + '?' + urllib.urlencode(parameters)
            is_folder = True
            # Add refresh option to context menu
            list_item.addContextMenuItems([('Refresh', 'Container.Refresh')])
            # Add our item to the listing as a 3-element tuple.
            listing.append((url, list_item, is_folder))

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "next url", str(url)), xbmc.LOGDEBUG)

        # Add our listing to Kodi.
        # Large lists and/or slower systems benefit from adding all items at once via addDirectoryItems
        # instead of adding one by ove via addDirectoryItem.
        xbmcplugin.addDirectoryItems(self.plugin_handle, listing, len(listing))
        # Disable sorting
        xbmcplugin.addSortMethod(handle=self.plugin_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.plugin_handle)
