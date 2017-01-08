#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from BeautifulSoup import BeautifulSoup
from worldstarcandy_const import ADDON, SETTINGS, LANGUAGE, IMAGES_PATH, DATE, VERSION
from worldstarcandy_utils import HTTPCommunicator
import os
import re
import sys
import urllib, urllib2
import urlparse
import xbmc
import xbmcgui
import xbmcplugin

BASEURL = "http://www.worldstarcandy.com"

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
        self.VIDEO = SETTINGS.getSetting('video')

        if (self.DEBUG) == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % (
                ADDON, VERSION, DATE, "ARGV", repr(sys.argv), "File", str(__file__)), xbmc.LOGNOTICE)

        # Parse parameters...
        if len(sys.argv[2]) == 0:
            self.plugin_category = LANGUAGE(30000)
            #http://www.worldstarcandy.com/latest.php?page=001
            self.video_list_page_url = BASEURL + "/latest.php?page=001"
            self.next_page_possible = "True"
        else:
            self.plugin_category = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['plugin_category'][0]
            self.video_list_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['url'][0]
            self.next_page_possible = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['next_page_possible'][0]

        if self.next_page_possible == 'True':
            # Determine current item number, next item number, next_url
            pos_of_page = self.video_list_page_url.rfind('/latest.php?page=')
            if pos_of_page >= 0:
                page_number_str = str(
                    self.video_list_page_url[pos_of_page + len('/latest.php?page='):pos_of_page + len('/latest.php?page=') + len('000')])
                page_number = int(page_number_str)
                page_number_next = page_number + 1
                if page_number_next >= 100:
                    page_number_next_str = str(page_number_next)
                elif page_number_next >= 10:
                    page_number_next_str = '0' + str(page_number_next)
                else:
                    page_number_next_str = '00' + str(page_number_next)
                self.next_url = str(self.video_list_page_url).replace(page_number_str, page_number_next_str)

                if self.DEBUG == 'true':
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
        is_folder = False
        # Create a list for our items.
        listing = []

        #
        # Get HTML page...
        #
        html_source = HTTPCommunicator().get(self.video_list_page_url)

        # Parse response...
        soup = BeautifulSoup(html_source)

        # <a href="http://www.worldstarcandy.com/candy/77459" target="_blank">
        # <div class="vidthumbone"><img src="http://hw-static.worldstarhiphop.com/u/pic/2015/03/15/FixedColombia4482akuyhstgbwysws.jpg" width="227" height="167">
        # <div class="thumbtitle"><img src="http://hw-static.worldstarhiphop.com/u/pic/2015/03/15/FixedColombia4482akuyhstgbwysws.jpg" align="left" />Sweat Series W/ Alejan</div>
        # </div>
        # </a>

        items = soup.findAll('a', attrs={'href': re.compile("^http://www.worldstarcandy.com/candy/")})

        if (self.DEBUG) == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "len(items)", str(len(items))), xbmc.LOGNOTICE)

        for item in items:
            video_page_url = str(item['href'])

            if (self.DEBUG) == 'true':
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "video_page_url", str(video_page_url)), xbmc.LOGNOTICE)

            # Get thumbnail url
            thumbnail_url = str(item.img['src'])

            if (self.DEBUG) == 'true':
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "thumbnail_url", str(thumbnail_url)), xbmc.LOGNOTICE)

            # Get title
            title = str(item.text)

            # Clean up title
            try:
                title = title.encode('utf-8')
            except:
                pass

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
            # welcome to characterset-hell
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

            if (self.DEBUG) == 'true':
                xbmc.log(
                    "[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "title", str(title)),
                    xbmc.LOGNOTICE)

            # Add to list...
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
