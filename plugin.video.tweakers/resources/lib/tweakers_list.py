#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
import os
import re
import requests
import sys
import urllib
import urlparse
import xbmc
import xbmcgui
import xbmcplugin
from BeautifulSoup import BeautifulSoup

from tweakers_const import ADDON, SETTINGS, LANGUAGE, IMAGES_PATH, DATE, VERSION


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

        # Parse parameters
        if len(sys.argv[2]) == 0:
            self.plugin_category = LANGUAGE(30000)
            self.video_list_page_url = "http://tweakers.net/video/zoeken/?page=001"
            self.video_list_page_url = str(self.video_list_page_url)
            self.next_page_possible = "True"
        else:
            self.plugin_category = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['plugin_category'][0]
            self.video_list_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['url'][0]
            self.video_list_page_url = str(self.video_list_page_url)
            self.next_page_possible = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['next_page_possible'][0]

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "self.video_list_page_url", str(self.video_list_page_url)), xbmc.LOGDEBUG)

        if self.next_page_possible == "True":
            # Determine current item number, next item number, next_url
            # f.e. http://www.tweakers.net/category/videos/page/001/
            pos_of_page = self.video_list_page_url.rfind('?page=')
            if pos_of_page >= 0:
                page_number_str = str(
                    self.video_list_page_url[pos_of_page + len('?page='):pos_of_page + len('?page=') + len('000')])
                page_number = int(page_number_str)
                page_number_next = page_number + 1
                if page_number_next >= 100:
                    page_number_next_str = str(page_number_next)
                elif page_number_next >= 10:
                    page_number_next_str = '0' + str(page_number_next)
                else:
                    page_number_next_str = '00' + str(page_number_next)
                self.next_url = self.video_list_page_url.replace(page_number_str, page_number_next_str)

                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                        ADDON, VERSION, DATE, "self.next_url", str(urllib.unquote_plus(self.next_url))), xbmc.LOGDEBUG)

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
        # Make the headers
        xbmc_version = xbmc.getInfoLabel("System.BuildVersion")
        user_agent = "Kodi Mediaplayer %s / Tweakers Addon %s" % (xbmc_version, VERSION)
        headers = {"User-Agent": user_agent,
                   "Accept-Encoding": "gzip",
                   "X-Cookies-Accepted": "1"}
        # Disable ssl logging (this is needed for python version < 2.7.9 (SNIMissingWarning))
        import logging
        logging.captureWarnings(True)
        # Get HTML page
        response = requests.get(self.video_list_page_url, headers=headers)
        # response.status
        html_source = response.text
        html_source = html_source.encode('utf-8', 'ignore')

        # Parse response
        soup = BeautifulSoup(html_source)

        # Get the thumbnail urls
        # <img src="http://ic.tweakimg.net/img/accountid=1/externalid=7515/size=124x70/image.jpg" width=124 height=70 alt="">
        thumbnail_urls = soup.findAll('img', attrs={'src': re.compile("^http://ic.tweakimg.net/")})

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "len(thumbnail_urls)", str(len(thumbnail_urls))), xbmc.LOGDEBUG)

        # Get the video page urls
        # <td class="video-image">
        #	<a href="https://tweakers.net/video/7517/showcase-trailer-van-cryengine-3-van-gdc-2013.html" class="thumb video" title="Showcase-trailer van CryEngine 3 van GDC 2013">
        #   <img src="http://ic.tweakimg.net/img/accountid=1/externalid=7517/size=124x70/image.jpg" width=124 height=70 alt=""><span class="playtime">04:00</span></a>
        # </td>
        video_page_url_in_tds = soup.findAll('td', attrs={'class': re.compile("video-image")})
        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "len(video_page_url_in_tds)", str(len(video_page_url_in_tds))), xbmc.LOGDEBUG)

        # Add Search item
        video_page_url = ""
        title = LANGUAGE(30103)
        thumbnail_url = ""
        list_item = xbmcgui.ListItem(label=title, thumbnailImage=thumbnail_url)
        list_item.setInfo("video", {"title": title, "studio": ADDON})
        list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                          'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
        list_item.setProperty('IsPlayable', 'false')
        parameters = {"action": "search", "video_page_url": video_page_url, "title": title}
        url = self.plugin_url + '?' + urllib.urlencode(parameters)
        is_folder = True
        # Add refresh option to context menu
        list_item.addContextMenuItems([('Refresh', 'Container.Refresh')])
        # Add our item to the listing as a 3-element tuple.
        listing.append((url, list_item, is_folder))

        for video_page_url_in_td in video_page_url_in_tds:
            video_page_url = video_page_url_in_td.a['href']

            # Make title
            title = video_page_url_in_td.a['title']

            # Convert from unicode to encoded text (don't use str() to do this)
            try:
                title = title.encode('utf-8')
            except:
                pass

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "title", str(title)),
                         xbmc.LOGDEBUG)

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
            parameters = {"action": "list", "plugin_category": self.plugin_category, "url": str(self.next_url),
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
