#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from BeautifulSoup import BeautifulSoup
from worldstarhiphop_const import ADDON, SETTINGS, LANGUAGE, IMAGES_PATH, DATE, VERSION
from worldstarhiphop_utils import HTTPCommunicator
import os
import re
import sys
import urllib, urllib2
import urlparse
import xbmc
import xbmcgui
import xbmcplugin

BASEURL = "http://www.worldstarhiphop.com"

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
            self.video_list_page_url = BASEURL + "/videos/?start=001"
            self.next_page_possible = "True"
        else:
            self.plugin_category = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['plugin_category'][0]
            self.video_list_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['url'][0]
            self.next_page_possible = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['next_page_possible'][0]

        if self.next_page_possible == 'True':
            # Determine current item number, next item number, next_url
            pos_of_page = self.video_list_page_url.rfind('start=')
            if pos_of_page >= 0:
                page_number_str = str(
                    self.video_list_page_url[pos_of_page + len('start='):pos_of_page + len('start=') + len('000')])
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

        # <section class="box">
        #                 <a href="/videos/video.php?v=wshhf1jtojJPKCOEOd1n" class="video-box">
        #                 <img src="http://hw-static.worldstarhiphop.com/u/pic/2015/06/Oe4nzSMG4iuf.jpg" width="222" height="125" alt="">
        #                 </a>
        #                 <strong class="title"><a href="/videos/video.php?v=wshhf1jtojJPKCOEOd1n">Blues Version Of &quot;The Fresh Prince Of Bel-Air&quot; Theme!</a></strong>
        #                 <div>
        #                         <span class="views">58,847</span>
        #                         <span class="comments"><a href="http://www.worldstarhiphop.com/videos/video.php?v=wshhf1jtojJPKCOEOd1n#disqus_thread" data-disqus-identifier="83085"></a></span>
        #                 </div>
        # </section>

        # Clean title: Blues Version Of "The Fresh Prince Of Bel-Air" Theme!

        items = soup.findAll('section', attrs={'class': re.compile("^box")})

        if (self.DEBUG) == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "len(items)", str(len(items))), xbmc.LOGNOTICE)

        # Add Search item
        video_page_url = ""
        title = LANGUAGE(30103)
        thumbnail_url = ""
        parameters = {"action": "search", "video_page_url": video_page_url}
        url = sys.argv[0] + '?' + urllib.urlencode(parameters)
        listitem = xbmcgui.ListItem(title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail_url)
        listitem.setInfo("video", {"Title": title, "Studio": "WorldWideHipHop"})
        folder = True
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=folder)

        for item in items:
            item_string = str(item)

            # Get video-page-url
            start_pos_url1 = item_string.find('"/videos/video.php?v=', 0)

            # skip the item if nothing was found
            if start_pos_url1 == -1:
                continue

            end_pos_url1 = item_string.find('"', start_pos_url1 + 1)
            video_url = item_string[start_pos_url1 + 1:end_pos_url1]
            video_page_url = BASEURL + video_url

            if (self.DEBUG) == 'true':
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "video_page_url", str(video_page_url)), xbmc.LOGNOTICE)

            # Get thumbnail url
            item_string = str(item)
            start_pos_url = item_string.find('http://hw-static.worldstarhiphop.com', 0)
            end_pos_url = item_string.find('"', start_pos_url)
            thumbnail_url = item_string[start_pos_url:end_pos_url]

            if (self.DEBUG) == 'true':
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "thumbnail_url", str(thumbnail_url)), xbmc.LOGNOTICE)

            # Get title
            start_pos_url2 = item_string.find('"/videos/video.php?v=', end_pos_url1 + 1)
            end_pos_url2 = item_string.find('"', start_pos_url2 + 1)
            start_pos_title = item_string.find('>', end_pos_url2 + 1)
            end_pos_title = item_string.find('<', start_pos_title + 1)
            title = item_string[start_pos_title + 1:end_pos_title]

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
