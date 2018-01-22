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

from dumpert_const import LANGUAGE, IMAGES_PATH, SETTINGS, convertToUnicodeString, log, getSoup


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

        log("self.base_url", self.base_url)

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

        #
        # Get HTML page...
        #
        if SETTINGS.getSetting('nsfw') == 'true':
            response = requests.get(self.video_list_page_url, cookies={'nsfw': '1'})
        else:
            response = requests.get(self.video_list_page_url)

        html_source = response.text
        html_source = convertToUnicodeString(html_source)

        # Parse response
        soup = getSoup(html_source)

        # <img src="http://static.dumpert.nl/s/trailerts_gr.jpg" alt="" />
        thumbnail_urls = soup.findAll('img', attrs={'src': re.compile("^http://static.dumpert.nl/")})

        log("len(thumbnail_urls)", len(thumbnail_urls))

        # <a href="/themas/uit_het_archief/" class="themalink big">
        # <a href="/themas/liev/" class="themalink">
        video_page_urls = soup.findAll('a', attrs={'class': re.compile("^themalink")})

        log("len(video_page_urls)", len(video_page_urls))

        for video_page_url in video_page_urls:
            video_page_url = video_page_url['href']
            # remove '/themas/'
            video_page_url = video_page_url.replace('/themas/', '')
            # http://www.dumpert.nl/<thema>/
            theme_base_url = str(self.base_url) + str(video_page_url)
            current_page = 1

            log("theme_base_url", theme_base_url)

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

            log("title", title)

            if thumbnail_urls_index >= len(thumbnail_urls):
                thumbnail_url = ''
            else:
                thumbnail_url = thumbnail_urls[thumbnail_urls_index]['src']

            # Add to list...
            parameters = {"action": "list", "plugin_category": self.plugin_category,
                          "url": str(theme_base_url) + str(current_page) + '/', "next_page_possible": "True",
                          "title": title}
            url = sys.argv[0] + '?' + urllib.parse.urlencode(parameters)
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
            url = sys.argv[0] + '?' + urllib.parse.urlencode(parameters)
            list_item = xbmcgui.ListItem(LANGUAGE(30503), thumbnailImage=os.path.join(IMAGES_PATH, 'next-page.png'))
            list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'false')
            is_folder = True
            # Add refresh option to context menu
            list_item.addContextMenuItems([('Refresh', 'Container.Refresh')])
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=list_item, isFolder=is_folder)

            log("next url", url)

        # Sort on labels...
        xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_LABEL)

        # End of directory...
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)
