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

from dumpert_const import ADDON, SETTINGS, LANGUAGE, IMAGES_PATH, DATE, VERSION


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

        # Parse parameters...
        self.plugin_category = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['plugin_category'][0]
        self.video_list_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['url'][0]
        self.next_page_possible = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['next_page_possible'][0]

        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "self.video_list_page_url", str(self.video_list_page_url)),
                     xbmc.LOGNOTICE)

        # Determine base_url
        # http://www.dumpert.nl/
        # find last slash
        pos_of_last_slash = self.video_list_page_url.rfind('/')
        # remove last slash
        self.video_list_page_url = self.video_list_page_url[0: pos_of_last_slash]
        pos_of_last_slash = self.video_list_page_url.rfind('/')
        self.base_url = self.video_list_page_url[0: pos_of_last_slash + 1]
        # add last slash
        self.video_list_page_url = str(self.video_list_page_url) + "/"

        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "self.base_url", str(self.base_url)), xbmc.LOGNOTICE)

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
        current_page = ''
        theme_base_url = ''
        list_item = ''

        #
        # Get HTML page...
        #
        if SETTINGS.getSetting('nsfw') == 'true':
            html_source = requests.get(self.video_list_page_url, cookies={'nsfw': '1'}).text
        else:
            html_source = requests.get(self.video_list_page_url).text

        # Parse response...
        soup = BeautifulSoup(html_source)

        # <img src="http://static.dumpert.nl/s/trailerts_gr.jpg" alt="" />
        thumbnail_urls = soup.findAll('img', attrs={'src': re.compile("^http://static.dumpert.nl/")})

        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "len(thumbnail_urls)", str(len(thumbnail_urls))), xbmc.LOGNOTICE)

        # <a href="/themas/uit_het_archief/" class="themalink big">
        # <a href="/themas/liev/" class="themalink">
        video_page_urls = soup.findAll('a', attrs={'class': re.compile("^themalink")})

        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "len(video_page_urls)", str(len(video_page_urls))), xbmc.LOGNOTICE)

        for video_page_url in video_page_urls:
            video_page_url = video_page_url['href']
            # remove '/themas/'
            video_page_url = video_page_url.replace('/themas/', '')
            # http://www.dumpert.nl/<thema>/
            theme_base_url = str(self.base_url) + str(video_page_url)
            current_page = 1

            if self.DEBUG == 'true':
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "self.theme_base_url", str(theme_base_url)), xbmc.LOGNOTICE)

            # Make title
            # http://static.dumpert.nl/themas/politiek_kl.jpg
            title = str(video_page_url)
            pos_of_last_slash = title.rfind('/')
            # remove last slash
            title = title[0: pos_of_last_slash]
            pos_of_last_slash = title.rfind('/')
            title = title[pos_of_last_slash + 1:]
            title = title.capitalize()
            title = title.replace('-', ' ')
            title = title.replace('/', ' ')
            title = title.replace('_kl', '')
            title = title.replace('_', ' ')

            if self.DEBUG == 'true':
                xbmc.log(
                    "[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "title", str(title)),
                    xbmc.LOGNOTICE)

            if thumbnail_urls_index >= len(thumbnail_urls):
                thumbnail_url = ''
            else:
                thumbnail_url = thumbnail_urls[thumbnail_urls_index]['src']

            # Add to list...
            parameters = {"action": "list", "plugin_category": self.plugin_category,
                          "url": str(theme_base_url) + str(current_page) + '/', "next_page_possible": "True",
                          "title": title}
            url = sys.argv[0] + '?' + urllib.urlencode(parameters)
            list_item = xbmcgui.ListItem(title, thumbnailImage=thumbnail_url)
            list_item.setInfo("video", {"Title": title, "Studio": "Dumpert"})
            list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                              'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'false')
            is_folder = True
            # Add refresh option to context menu
            list_item.addContextMenuItems([('Refresh', 'Container.Refresh')])
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=list_item, isFolder=is_folder)

            thumbnail_urls_index = thumbnail_urls_index + 1

        # Next page entry...
        if self.next_page_possible == 'True':
            next_page = current_page + 1
            parameters = {"action": "list", "plugin_category": self.plugin_category,
                          "url": str(theme_base_url) + str(next_page) + '/',
                          "next_page_possible": self.next_page_possible}
            url = sys.argv[0] + '?' + urllib.urlencode(parameters)
            list_item = xbmcgui.ListItem(LANGUAGE(30503), thumbnailImage=os.path.join(IMAGES_PATH, 'next-page.png'))
            list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'false')
            is_folder = True
            # Add refresh option to context menu
            list_item.addContextMenuItems([('Refresh', 'Container.Refresh')])
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=list_item, isFolder=is_folder)

            if self.DEBUG == 'true':
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "next url", str(url)), xbmc.LOGNOTICE)

        # Sort on labels...
        xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_LABEL)

        # End of directory...
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)
