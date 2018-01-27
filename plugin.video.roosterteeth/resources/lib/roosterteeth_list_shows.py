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
import requests
import sys
import urllib.request, urllib.parse, urllib.error
import xbmcgui
import xbmcplugin

from roosterteeth_const import ADDON, LANGUAGE, IMAGES_PATH, HEADERS, convertToUnicodeString, log, getSoup


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

        log("ARGV", repr(sys.argv))

        # Parse parameters...
        self.plugin_category = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['plugin_category'][0]
        self.video_list_page_url = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['url'][0]
        self.next_page_possible = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['next_page_possible'][0]

        log("self.video_list_page_url", self.video_list_page_url)

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
        response = requests.get(self.video_list_page_url, headers=HEADERS)

        html_source = response.text
        html_source = convertToUnicodeString(html_source)

        # Parse response
        soup = getSoup(html_source)

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

        shows = soup.findAll('li')

        log("len(shows)", len(shows))

        for show in shows:
            # Skip the show if it contains /episode/
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

                log("skipped /episode/ show", show)

                continue

            # Skip a show if it does not contain class="name"
            pos_classname = str(show).find('class="name"')
            if pos_classname < 0:

                log('skipped show without class="name"', show)

                continue

            url = show.a['href']

            try:
                thumbnail_url = "https:" + show.img['src']
            except:
                thumbnail_url = ''

            title = show.a.text.strip()

            # removing this stuff: 15 seasons | 320 episodes
            first_number = re.search("\d", title)
            if first_number:
                title = title[0:first_number.start()]
                title = title.strip()
                if title == "E":
                    title = "E3"

            if title == '':
                try:
                    title = show.img['alt']
                except:
                    title = 'Unknown Show Name'

            log("title", title)

            # Add to list...
            list_item = xbmcgui.ListItem(label=title, thumbnailImage=thumbnail_url)
            list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                              'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'false')
            parameters = {"action": "list-episodes", "show_name": title, "url": url, "next_page_possible": "False",
                          "title": title}
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
