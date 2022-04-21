#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import object
import requests
import os
import re
import sys
import urllib.request, urllib.parse, urllib.error
import xbmc
import xbmcgui
import xbmcplugin

from resources.lib.worldstarhiphop_const import ADDON, SETTINGS, LANGUAGE, IMAGES_PATH, DATE, VERSION, BASEURL, HEADERS, convertToUnicodeString, log, getSoup
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

        # Get plugin settings
        self.VIDEO = SETTINGS.getSetting('video')

        log("ARGV", repr(sys.argv))

        try:
            self.plugin_category = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['plugin_category'][0]
            self.video_list_page_url = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['url'][0]
            self.next_page_possible = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['next_page_possible'][0]
        except:
            self.plugin_category = LANGUAGE(30000)
            self.next_page_possible = "True"
            # Get the search-string from the user
            keyboard = xbmc.Keyboard('', LANGUAGE(30103))
            keyboard.doModal()
            if keyboard.isConfirmed():
                self.search_string = keyboard.getText()
                self.video_list_page_url = "http://www.worldstarhiphop.com/videos/search.php?s=%s&start=001" % (
                self.search_string)

        if self.next_page_possible == 'True':
            # Determine current item number, next item number, next_url
            pos_of_page = self.video_list_page_url.rfind('&start=')
            if pos_of_page >= 0:
                page_number_str = str(
                    self.video_list_page_url[pos_of_page + len('&start='):pos_of_page + len('&start=') + len('000')])
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
        is_folder = False
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

        # <a itemprop="url" class="video-box" href="https://worldstar.com/videos/wshhfvUpk4c8RQJu1Ldx/quotgirls-gone-wildquot-chicks-from-the-2000s-era-now-regret-flashing-cameras-exposing-joe-francis">
		#   <img class="lazy" data-original="https://hw-static.worldstarhiphop.com/u/pic/2022/04/8psfWpSeWZE4.jpg" alt="&quot;Girls Gone Wild&quot; Chicks From The 2000s Era Now Regret Flashing Cameras... Exposing Joe Francis!"
        #    itemprop="thumbnailUrl" src="https://hw-static.worldstarhiphop.com/u/pic/2022/04/8psfWpSeWZE4.jpg" style="" width="222" height="125">
		# 	<noscript>
        #     <img src="https://hw-static.worldstarhiphop.com/u/pic/2022/04/8psfWpSeWZE4.jpg" width="222" height="125"
        # 	   alt="&quot;Girls Gone Wild&quot; Chicks From The 2000s Era Now Regret Flashing Cameras... Exposing Joe Francis!" itemprop="thumbnailUrl">
        # 	</noscript>
		# </a>

        items = soup.findAll('a', attrs={'class': re.compile("^video-box")})

        log("len(items)", len(items))

        for item in items:
            try:
                # video_page_url = BASEURL + str(item['href'])
                video_page_url = str(item['href'])
            except:
                # skip the item if it does not have a href

                log("skipping item without href", item)

                continue

            log("video_page_url", video_page_url)

            # # skip the item if the video page url isn't a real video page url
            if str(video_page_url).find('/videos/') == -1:

                log("skipping item because no video could be found", video_page_url)

                continue

            try:
                thumbnail_url = item.img['data-original']
            except:
                thumbnail_url = item.img['src']

            log("thumbnail_url", thumbnail_url)

            title = item.img['alt']

            title = title.replace('-', ' ')
            title = title.replace('/', ' ')
            title = title.replace(' i ', ' I ')
            title = title.replace(' ii ', ' II ')
            title = title.replace(' iii ', ' III ')
            title = title.replace(' iv ', ' IV ')
            title = title.replace(' v ', ' V ')
            title = title.replace(' vi ', ' VI ')
            title = title.replace(' vii ', ' VII ')
            title = title.replace(' viii ', ' VIII ')
            title = title.replace(' ix ', ' IX ')
            title = title.replace(' x ', ' X ')
            title = title.replace(' xi ', ' XI ')
            title = title.replace(' xii ', ' XII ')
            title = title.replace(' xiii ', ' XIII ')
            title = title.replace(' xiv ', ' XIV ')
            title = title.replace(' xv ', ' XV ')
            title = title.replace(' xvi ', ' XVI ')
            title = title.replace(' xvii ', ' XVII ')
            title = title.replace(' xviii ', ' XVIII ')
            title = title.replace(' xix ', ' XIX ')
            title = title.replace(' xx ', ' XXX ')
            title = title.replace(' xxi ', ' XXI ')
            title = title.replace(' xxii ', ' XXII ')
            title = title.replace(' xxiii ', ' XXIII ')
            title = title.replace(' xxiv ', ' XXIV ')
            title = title.replace(' xxv ', ' XXV ')
            title = title.replace(' xxvi ', ' XXVI ')
            title = title.replace(' xxvii ', ' XXVII ')
            title = title.replace(' xxviii ', ' XXVIII ')
            title = title.replace(' xxix ', ' XXIX ')
            title = title.replace(' xxx ', ' XXX ')
            title = title.replace('  ', ' ')
            title = title.replace('  ', ' ')
            # welcome to unescaping-hell
            title = title.replace('&pound;', "Pound Sign")
            title = title.replace('&amp;#039;', "'")
            title = title.replace('&amp;#39;', "'")
            title = title.replace('&amp;quot;', '"')
            title = title.replace("&#039;", "'")
            title = title.replace("&#39;", "'")
            title = title.replace('&amp;amp;', '&')
            title = title.replace('&amp;', '&')
            title = title.replace('&quot;', '"')
            title = title.replace('&ldquo;', '"')
            title = title.replace('&rdquo;', '"')
            title = title.replace('&rsquo;', "'")
            title = title.replace('&ndash;', "/")

            log("title", title)

            # Add to list...
            list_item = xbmcgui.ListItem(title)
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
            listing.append((url, list_item, is_folder))

        # Next page entry
        if self.next_page_possible == 'True':
            thumbnail_url = os.path.join(IMAGES_PATH, 'next-page.png')
            list_item = xbmcgui.ListItem(LANGUAGE(30503))
            list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                              'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'false')
            parameters = {"action": "list", "plugin_category": self.plugin_category, "url": str(self.next_url),
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
