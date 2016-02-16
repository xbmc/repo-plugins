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

        # Get plugin settings
        self.DEBUG = SETTINGS.getSetting('debug')

        if self.DEBUG == 'true':
            print 'Python Version: ' + sys.version
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % (
                ADDON, VERSION, DATE, "ARGV", repr(sys.argv), "File", str(__file__)), xbmc.LOGNOTICE)

        # Parse parameters
        self.plugin_category = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['plugin_category'][0]
        self.video_list_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['url'][0]
        self.next_page_possible = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['next_page_possible'][0]

        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "self.video_list_page_url", str(self.video_list_page_url)),
                     xbmc.LOGNOTICE)

        # Determine current page number and base_url
        # find last slash
        pos_of_last_slash = self.video_list_page_url.rfind('/')
        # remove last slash
        self.video_list_page_url = self.video_list_page_url[0: pos_of_last_slash]
        pos_of_last_slash = self.video_list_page_url.rfind('/')
        self.base_url = self.video_list_page_url[0: pos_of_last_slash + 1]
        self.current_page = self.video_list_page_url[pos_of_last_slash + 1:]
        self.current_page = int(self.current_page)
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
        list_item = ''
        is_folder = False
        # Create a list for our items.
        listing = []

        #
        # Get HTML page
        #
        html_source = HTTPCommunicator().get(self.video_list_page_url)

        # Parse response
        soup = BeautifulSoup(html_source)

        # Find titles, thumbnail-urls and videopage-urls
        # <div class="item-header">
        #  <a href="http://botchamania.com/delriomania/" class="img-hover-effect loadingvideo">
        #     <img src="http://botchamania.com/wp-content/themes/videomag-theme/images/aspect-px.png" width="16" height="9" class="aspect-px" rel="http://botchamania.com/wp-content/uploads/2014/08/delriomania-549x316_c.jpg" alt="DelRioMania" />
        #  </a>
        # </div>
        titles_thumbnail_videopage_urls = soup.findAll('div', attrs={'class': re.compile("item-header")})

        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "len(titles_thumbnail_videopage_urls)",
                str(len(titles_thumbnail_videopage_urls))), xbmc.LOGNOTICE)

        for titles_thumbnail_videopage_url in titles_thumbnail_videopage_urls:
            video_page_url = titles_thumbnail_videopage_url.a['href']

            if self.DEBUG == 'true':
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "video_page_url", str(video_page_url)), xbmc.LOGNOTICE)

            title = ''
            # Make title
            try:
                title = titles_thumbnail_videopage_url.img['alt']
                # convert from unicode to encoded text (don't use str() to do this)
                title = title.encode('utf-8')
            except KeyError:
                pass
            except UnicodeDecodeError:
                pass

            title = title.replace('-', ' ')
            title = title.replace('/', ' ')
            title = title.replace('_', ' ')

            if self.DEBUG == 'true':
                xbmc.log(
                    "[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "title", str(title)),
                    xbmc.LOGNOTICE)

            thumbnail_url = titles_thumbnail_videopage_url.img['rel']

            if self.DEBUG == 'true':
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "thumbnail_url", str(thumbnail_url)), xbmc.LOGNOTICE)

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
            next_page = self.current_page + 1
            list_item = xbmcgui.ListItem(LANGUAGE(30503), thumbnailImage=os.path.join(IMAGES_PATH, 'next-page.png'))
            list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'false')
            parameters = {"action": "list", "plugin_category": self.plugin_category,
                          "url": str(self.base_url) + str(next_page) + '/',
                          "next_page_possible": self.next_page_possible}
            url = self.plugin_url + '?' + urllib.urlencode(parameters)
            is_folder = True
            # Add refresh option to context menu
            list_item.addContextMenuItems([('Refresh', 'Container.Refresh')])
            # Add our item to the listing as a 3-element tuple.
            listing.append((url, list_item, is_folder))

            if self.DEBUG == 'true':
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "next url", str(url)), xbmc.LOGNOTICE)

        # Add our listing to Kodi.
        # Large lists and/or slower systems benefit from adding all items at once via addDirectoryItems
        # instead of adding one by ove via addDirectoryItem.
        xbmcplugin.addDirectoryItems(self.plugin_handle, listing, len(listing))
        # Disable sorting
        xbmcplugin.addSortMethod(handle=self.plugin_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.plugin_handle)
