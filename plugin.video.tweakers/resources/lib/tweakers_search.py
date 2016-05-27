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

from tweakers_const import ADDON, SETTINGS, LANGUAGE, IMAGES_PATH, DATE, VERSION
from tweakers_utils import HTTPCommunicator


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

        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % (
                ADDON, VERSION, DATE, "ARGV", repr(sys.argv), "File", str(__file__)), xbmc.LOGNOTICE)

        # Parse parameters
        try:
            self.plugin_category = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['plugin_category'][0]
            self.video_list_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['url'][0]
            self.next_page_possible = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['next_page_possible'][0]
        except:
            self.plugin_category = LANGUAGE(30000)
            self.next_page_possible = "True"
            # Get the search-string from the user
            keyboard = xbmc.Keyboard('', LANGUAGE(30103))
            keyboard.doModal()
            if keyboard.isConfirmed():
                self.search_string = keyboard.getText()
                self.video_list_page_url = "http://tweakers.net/video/zoeken?keyword=%s&page=001" % (self.search_string)

        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "self.video_list_page_url", str(self.video_list_page_url)), xbmc.LOGNOTICE)

        if self.next_page_possible == "True":
            # Determine current item number, next item number, next_url
            # f.e. http://www.tweakers.net/category/videos/page/001/
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

                if self.DEBUG == 'true':
                    xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                        ADDON, VERSION, DATE, "self.next_url", str(urllib.unquote_plus(self.next_url))), xbmc.LOGNOTICE)

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
        thumbnail_urls_index = 0
        # Create a list for our items.
        listing = []

        #
        # Get HTML page
        #
        html_source = HTTPCommunicator().get(self.video_list_page_url)

        # Parse response
        soup = BeautifulSoup(html_source)

        # Get the thumbnail urls
        # <img src="http://ic.tweakimg.net/img/accountid=1/externalid=7515/size=124x70/image.jpg" width=124 height=70 alt="">
        thumbnail_urls = soup.findAll('img', attrs={'src': re.compile("^http://ic.tweakimg.net/")})

        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "len(thumbnail_urls)", str(len(thumbnail_urls))), xbmc.LOGNOTICE)

        # Get the video page urls
        # <td class="video-image">
        #	<a href="http://tweakers.net/video/7517/showcase-trailer-van-cryengine-3-van-gdc-2013.html" class="thumb video" title="Showcase-trailer van CryEngine 3 van GDC 2013">
        #   <img src="http://ic.tweakimg.net/img/accountid=1/externalid=7517/size=124x70/image.jpg" width=124 height=70 alt=""><span class="playtime">04:00</span></a>
        # </td>
        video_page_url_in_tds = soup.findAll('td', attrs={'class': re.compile("video-image")})
        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "len(video_page_url_in_tds)", str(len(video_page_url_in_tds))), xbmc.LOGNOTICE)

        #skip the first thumbnails
        if len(thumbnail_urls) - len(video_page_url_in_tds) > 0:
            thumbnail_urls_index = thumbnail_urls_index + (len(thumbnail_urls) - len(video_page_url_in_tds))

        for video_page_url_in_td in video_page_url_in_tds:
            video_page_url = video_page_url_in_td.a['href']

            # Make title
            title = video_page_url_in_td.a['title']

            # Convert from unicode to encoded text (don't use str() to do this)
            try:
                title = title.encode('utf-8')
            except:
                pass

            if self.DEBUG == 'true':
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "title", str(title)),
                         xbmc.LOGNOTICE)

            if thumbnail_urls_index >= len(thumbnail_urls):
                thumbnail_url = ''
            else:
                thumbnail_url = thumbnail_urls[thumbnail_urls_index]['src']

            list_item = xbmcgui.ListItem(label=title, thumbnailImage=thumbnail_url)
            list_item.setInfo("video", {"title": title, "studio": ADDON})
            list_item.setInfo("mediatype", "video")
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

            thumbnail_urls_index = thumbnail_urls_index + 1

        # Next page entry
        if self.next_page_possible == 'True':
            list_item = xbmcgui.ListItem(LANGUAGE(30503), thumbnailImage=os.path.join(IMAGES_PATH, 'next-page.png'))
            list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'false')
            parameters = {"action": "search", "plugin_category": self.plugin_category, "url": str(self.next_url),
                          "next_page_possible": self.next_page_possible}
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
