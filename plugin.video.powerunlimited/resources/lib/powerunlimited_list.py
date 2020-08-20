#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import object
from resources.lib.powerunlimited_const import ADDON, LANGUAGE, IMAGES_PATH, HEADERS, convertToUnicodeString, log, getSoup
import os
import re
import sys
import urllib.request, urllib.parse, urllib.error
import xbmcgui
import xbmcplugin
import requests


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

        if self.next_page_possible == 'True':
            # Determine current item number, next item number, next_url
            # http://www.pu.nl/media/pu-tv/?page=001/
            pos_of_page = self.video_list_page_url.rfind('?page=')
            if pos_of_page >= 0:
                page_number_str = str(
                    self.video_list_page_url[pos_of_page + len('?page='):pos_of_page + len('?page=') + len('000')])
                page_number = int(page_number_str)
                self.current_page = page_number
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
        # thumbnail_urls_index = 0
        list_item = ''
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

        # Get video-page-urls
        # <a class='article pu-tv featured' href='/media/video/pu-tv/parodie-replacer/'>
        # and not <a class='article' href='/games/briquid/'>
        video_page_url_items = soup.findAll('a', attrs={'class': re.compile("^article")})

        log("len(video_page_url_items", len(video_page_url_items))

        for video_page_url_item in video_page_url_items:

            log("video_page_url_item", video_page_url_item)

            #<a class="article trailer featured" href="/media/video/trailer/pizza-connection-terug-trailer/"><span class="type"></span>
            # <article><div class="article-image">
            # <img alt="" src="http://cdn.pu.nl/thumbnails/144x123/e8a2a/pizza_maken.jpg" title=""/>
            # </div><header><h4><strong>Pizzaatjes bakken</strong> in Pizza Connection -<strong> trailer</strong></h4></header><div class="date hidden-phone">

            href = video_page_url_item['href']

            # skip empty video link
            if str(href) == '':

                log("skipped empty href", href)

                continue

            # skip video link if starts with '/games/'
            if str(href).startswith("/games/"):

                log("skipped href with /games/", href)

                continue

            # skip video link if starts with '/media/gallery/'
            if str(href).startswith("/media/gallery/"):

                log("skipped href with /media/gallery/", href)

                continue

            # skip video link if starts with '/artikelen/'
            if str(href).startswith("/artikelen/"):

                log("skipped href with /artikelen/", href)

                continue

            video_page_url = "http://www.pu.nl/media/video%s" % href

            log("video_page_url", video_page_url)

            # Make title
            # /media/video/pu-tv/parodie-replacer/
            # /media/video/trailer/old-republic-dlc-video-laat-nieuwe-planeet-zien/
            # remove the trailing /
            title = str(href)
            title = title[0:len(title) - len('/')]
            pos_of_last_slash = title.rfind('/')
            title = title[pos_of_last_slash + 1:]
            title = title.capitalize()
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

            log("title", title)

            # find thumbnail url
            start_pos_src_thumbnail_url = str(video_page_url_item).find('src="')
            if start_pos_src_thumbnail_url >= 0:
                start_pos_thumbnail_url = start_pos_src_thumbnail_url + len('src="')
                end_pos_thumbnail_url = str(video_page_url_item).find('"', start_pos_thumbnail_url)
                thumbnail_url = str(video_page_url_item)[start_pos_thumbnail_url:end_pos_thumbnail_url]
            else:
                thumbnail_url = ''

            log("thumbnail_url", thumbnail_url)

            # Add to list
            list_item = xbmcgui.ListItem(label=title)
            list_item.setInfo("video", {"title": title, "studio": ADDON})
            list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                              'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'true')
            parameters = {"action": "play", "video_page_url": video_page_url}
            url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
            is_folder = False
            # Add refresh option to context menu
            list_item.addContextMenuItems([('Refresh', 'Container.Refresh')])
            # Add our item to the listing as a 3-element tuple.
            listing.append((url, list_item, is_folder))

        # Next page entry
        if self.next_page_possible == 'True':
            next_page = self.current_page + 1
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

        # Add our listing to Kodi
        # Large lists and/or slower systems benefit from adding all items at once via addDirectoryItems
        # instead of adding one by ove via addDirectoryItem.
        xbmcplugin.addDirectoryItems(self.plugin_handle, listing, len(listing))
        # Disable sorting
        xbmcplugin.addSortMethod(handle=self.plugin_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.plugin_handle)
