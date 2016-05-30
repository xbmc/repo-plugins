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
import xbmc
import xbmcgui
import xbmcplugin
from BeautifulSoup import BeautifulSoup

from roosterteeth_const import ADDON, SETTINGS, DATE, VERSION, IMAGES_PATH, RECENTLYADDEDURL, ROOSTERTEETHSHOWSURL, \
    ACHIEVEMENTHUNTERURL, THEKNOWSHOWSURL, FUNHAUSSHOWSURL, SCREWATTACKURL


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

        # Get plugin settings
        self.DEBUG = SETTINGS.getSetting('debug')

        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % (
                ADDON, VERSION, DATE, "ARGV", repr(sys.argv), "File", str(__file__)), xbmc.LOGNOTICE)

        # Parse parameters...
        self.plugin_category = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['plugin_category'][0]
        self.video_list_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['url'][0]
        self.next_page_possible = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['next_page_possible'][0]

        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "self.video_list_page_url", str(self.video_list_page_url)),
                     xbmc.LOGNOTICE)

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
        response = requests.get(self.video_list_page_url)
        html_source = response.text
        html_source = html_source.encode('utf-8', 'ignore')

        # for roosterteeth
        #       <li>
        #         <a href="http://www.roosterteeth.com/show/red-vs-blue">
        #             <div class="block-container">
        #                 <div class="image-container">
        #                     <img src="//s3.amazonaws.com/cdn.roosterteeth.com/uploads/images/9a888611-5b17-49ab-ad49-ca0ad6a86ee1/sm/rvb600.jpg" alt="Red vs. Blue">
        #                 </div>
        #             </div>
        #             <p class="name">Red vs. Blue</p>
        #             <p class="post-stamp">13 seasons | 377 episodes</p>
        #         </a>
        #       </li>

        # for achievementhunter
        # <li>
        #   <a href="http://achievementhunter.roosterteeth.com/show/off-topic-the-achievement-hunter-podcast">
        #     <div class="block-container">
        #         <div class="image-container">
        # 	         <img src="//s3.amazonaws.com/cdn.roosterteeth.com/uploads/images/65924ffb-2ca9-407d-bbd9-b717ed944f75/sm/2013912-1446152735286-Off_Topic_1400x_Logo.jpg" alt="Off Topic">
        # 	      </div>
        #     </div>
        #     <p class="name">Off Topic</p>
        #     <p class="post-stamp">2 seasons | 30 episodes</p>
        #   </a>
        # </li>

        # Parse response...
        soup = BeautifulSoup(html_source)

        shows = soup.findAll('li')

        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "len(shows)", str(len(shows))), xbmc.LOGNOTICE)

        for show in shows:
            video_list_page_url_http = str(self.video_list_page_url).replace("https", "http")
            video_list_page_url_https = str(self.video_list_page_url).replace("http", "https")

            # skip show if it doesn't contain the website show url (https or http)
            if str(video_list_page_url_http).find(RECENTLYADDEDURL) < 0:
                if str(video_list_page_url_https).find(RECENTLYADDEDURL) < 0:
                    if str(video_list_page_url_http).find(ROOSTERTEETHSHOWSURL) < 0:
                        if str(video_list_page_url_https).find(ROOSTERTEETHSHOWSURL) < 0:
                            if str(video_list_page_url_http).find(ACHIEVEMENTHUNTERURL) < 0:
                                if str(video_list_page_url_https).find(ACHIEVEMENTHUNTERURL) < 0:
                                    if str(video_list_page_url_http).find(THEKNOWSHOWSURL) < 0:
                                        if str(video_list_page_url_https).find(THEKNOWSHOWSURL) < 0:
                                            if str(video_list_page_url_http).find(FUNHAUSSHOWSURL) < 0:
                                                if str(video_list_page_url_https).find(FUNHAUSSHOWSURL) < 0:
                                                    if str(video_list_page_url_http).find(SCREWATTACKURL) < 0:
                                                        if str(video_list_page_url_https).find(SCREWATTACKURL) < 0:
                                                            if self.DEBUG == 'true':
                                                                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                                                                    ADDON, VERSION, DATE,
                                                                    "skipped show that doesn't contain website show url",
                                                                    str(video_list_page_url_http)), xbmc.LOGNOTICE)
                                                                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                                                                    ADDON, VERSION, DATE,
                                                                    "skipped show that doesn't contain website show url",
                                                                    str(video_list_page_url_https)), xbmc.LOGNOTICE)
                                                                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                                                                    ADDON, VERSION, DATE,
                                                                    "skipped show that doesn't contain website show url",
                                                                    str(show)), xbmc.LOGNOTICE)
                                                            continue

            # skip show if it contains the website show url (https or http)
            # <li class="upcoming-featured">
            #         <a href="http://roosterteeth.com/episode/ahwu-2016-memorial-day-ahwu-for-may-30-th-2016-319">
            #             <div class="block-container">
            #                 <p class="air-date">Today, 5/30</p>
            #                 <p class="air-time">2:00 pm CDT</p>
            #                 <p class="air-countdown">Starting 2 hours from now</p>
            #                 <div class="image-container">
            #                     <img src="//s3.amazonaws.com/cdn.roosterteeth.com/uploads/images/3dad2181-68ed-46dc-87dd-3c80bc4bef9e/sm/2013912-1464386396337-ahwu_thumb.jpg">
            #                 </div>
            #             <p class="name">
            #                                             <strong>AHWU:</strong> Memorial Day! – AHWU for May 30th , 2016 (#319)
            #             </p>
            #             </div>
            #         </a>
            #     </li>
            if str(show).find("/episode/") < 0 :
                pass
            else:
                if self.DEBUG == 'true':
                    xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                        ADDON, VERSION, DATE,
                        "skipped /episode/ show ",
                        str(show)), xbmc.LOGNOTICE)
                continue

            # Skip a show if it does not contain class="name"
            pos_classname = str(show).find('class="name"')
            if pos_classname < 0:
                if self.DEBUG == 'true':
                    xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                        ADDON, VERSION, DATE, 'skipped show without class="name"', str(show)),
                             xbmc.LOGNOTICE)
                continue

            url = show.a['href']

            try:
                thumbnail_url = "https:" + show.img['src']
            except:
                thumbnail_url = ''

            title = show.a.text
            if title == '':
                try:
                    title = show.img['alt']
                except:
                    title = 'Unknown Show Name'

            # Add to list...
            list_item = xbmcgui.ListItem(label=title, thumbnailImage=thumbnail_url)
            list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                              'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'false')
            parameters = {"action": "list-episodes", "show_name": title, "url": url, "next_page_possible": "False",
                          "title": title}
            url = self.plugin_url + '?' + urllib.urlencode(parameters)
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
