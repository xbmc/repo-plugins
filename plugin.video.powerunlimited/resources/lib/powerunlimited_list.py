#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from BeautifulSoup import BeautifulSoup
from powerunlimited_const import ADDON, SETTINGS, LANGUAGE, IMAGES_PATH, DATE, VERSION
import os
import re
import sys
import urllib, urllib2
import urlparse
import xbmc
import xbmcgui
import xbmcplugin
import requests


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

        # Get plugin settings
        self.DEBUG = SETTINGS.getSetting('debug')

        if (self.DEBUG) == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % (
                ADDON, VERSION, DATE, "ARGV", repr(sys.argv), "File", str(__file__)), xbmc.LOGNOTICE)

        # Parse parameters...
        self.plugin_category = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['plugin_category'][0]
        self.video_list_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['url'][0]
        self.next_page_possible = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['next_page_possible'][0]

        if (self.DEBUG) == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "self.video_list_page_url", str(self.video_list_page_url)),
                     xbmc.LOGNOTICE)

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

                if (self.DEBUG) == 'true':
                    xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                        ADDON, VERSION, DATE, "self.next_url", str(urllib.unquote_plus(self.next_url))),
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
        thumbnail_urls_index = 0
        list_item = ''
        # Create a list for our items.
        listing = []

        #
        # Get HTML page...
        #
        response = requests.get(self.video_list_page_url)
        html_source = response.text
        html_source = html_source.encode('utf-8', 'ignore')

        # Parse response...
        soup = BeautifulSoup(html_source)

        # Get thumbnails-urls
        # <img src='http://cdn.pu.nl/thumbnails/144x123/00fa0/hqdefault.jpg' alt='' title='' />
        thumbnail_urls = soup.findAll('img', attrs={'src': re.compile("/thumbnails/")})

        if (self.DEBUG) == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "len(thumbnail_urls)", str(len(thumbnail_urls))), xbmc.LOGNOTICE)

        # Get video-page-urls
        # <a class='article pu-tv featured' href='/media/video/pu-tv/parodie-replacer/'>
        # and not <a class='article' href='/games/briquid/'>
        video_page_urls = soup.findAll('a', attrs={'class': re.compile("^article")})

        if (self.DEBUG) == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "len(video_page_urls)", str(len(video_page_urls))), xbmc.LOGNOTICE)

        for video_page_url in video_page_urls:
            href = video_page_url['href']
            # skip video link if starts with '/games/'
            if str(href).startswith("/games/"):
                if (self.DEBUG) == 'true':
                    xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                        ADDON, VERSION, DATE, "skipped video_page_url with /games/", str(href)), xbmc.LOGNOTICE)
                thumbnail_urls_index = thumbnail_urls_index + 1
                continue

            # skip video link if starts with '/media/gallery/'
            if str(href).startswith("/media/gallery/"):
                if (self.DEBUG) == 'true':
                    xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                        ADDON, VERSION, DATE, "skipped video_page_url with /media/gallery/", str(href)),
                             xbmc.LOGNOTICE)
                thumbnail_urls_index = thumbnail_urls_index + 1
                continue

            # skip video link if starts with '/artikelen/'
            if str(href).startswith("/artikelen/"):
                if (self.DEBUG) == 'true':
                    xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                        ADDON, VERSION, DATE, "skipped video_page_url with /artikelen/", str(href)),
                             xbmc.LOGNOTICE)
                thumbnail_urls_index = thumbnail_urls_index + 1
                continue

            video_page_url = "http://www.pu.nl/media/video%s" % href

            if (self.DEBUG) == 'true':
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "video_page_url", str(video_page_url)), xbmc.LOGNOTICE)

            # Make title
            # /media/video/pu-tv/parodie-replacer/
            # /media/video/trailer/old-republic-dlc-video-laat-nieuwe-planeet-zien/
            title = str(href)
            # remove the trailing /
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

            if (self.DEBUG) == 'true':
                xbmc.log(
                    "[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "title", str(title)),
                    xbmc.LOGNOTICE)

            # if thumbnail_urls_index + 1 >= len(thumbnail_urls):
            if thumbnail_urls_index >= len(thumbnail_urls):
                thumbnail_url = ''
            else:
                thumbnail_url = thumbnail_urls[thumbnail_urls_index]['src']

            # Add to list
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
            xbmc.log("zzzz" + str(url))
            # Add our item to the listing as a 3-element tuple.
            listing.append((url, list_item, is_folder))

            thumbnail_urls_index = thumbnail_urls_index + 1

        # Next page entry
        if self.next_page_possible == 'True':
            next_page = self.current_page + 1
            list_item = xbmcgui.ListItem(LANGUAGE(30503), thumbnailImage=os.path.join(IMAGES_PATH, 'next-page.png'))
            list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'false')
            parameters = {"action": "list", "plugin_category": self.plugin_category, "url": str(self.next_url),
                          "next_page_possible": self.next_page_possible}
            url = self.plugin_url + '?' + urllib.urlencode(parameters)
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



        #
        #     # Add to list...
        #     parameters = {"action": "play", "video_page_url": video_page_url, "title": title}
        #     url = sys.argv[0] + '?' + urllib.urlencode(parameters)
        #     listitem = xbmcgui.ListItem(title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail_url)
        #     listitem.setInfo("video", {"Title": title, "Studio": "Powerunlimited"})
        #     folder = False
        #     xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=folder)
        #
        #     thumbnail_urls_index = thumbnail_urls_index + 1
        #
        # # Next page entry...
        # if self.next_page_possible == 'True':
        #     parameters = {"action": "list", "plugin_category": self.plugin_category, "url": str(self.next_url),
        #                   "next_page_possible": self.next_page_possible}
        #     url = sys.argv[0] + '?' + urllib.urlencode(parameters)
        #     listitem = xbmcgui.ListItem(LANGUAGE(30503), iconImage="DefaultFolder.png",
        #                                 thumbnailImage=os.path.join(IMAGES_PATH, 'next-page.png'))
        #     folder = True
        #     xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=folder)
        #
        # # Disable sorting...
        # xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_NONE)
        #
        # # End of directory...
        # xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)
