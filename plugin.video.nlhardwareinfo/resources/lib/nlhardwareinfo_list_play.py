#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
import os
import sys
import urllib
import urlparse
import xbmc
import xbmcgui
import xbmcplugin
from BeautifulSoup import BeautifulSoup

from nlhardwareinfo_const import ADDON, SETTINGS, LANGUAGE, IMAGES_PATH, DATE, VERSION
from nlhardwareinfo_utils import HTTPCommunicator


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
        if len(sys.argv[2]) == 0:
            self.plugin_category = LANGUAGE(30000)
            self.video_list_page_url = "http://nl.hardware.info/tv/rss-private/streaming"
            self.next_page_possible = "False"
        else:
            self.plugin_category = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['plugin_category'][0]
            self.video_list_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['url'][0]
            self.next_page_possible = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['next_page_possible'][0]

        if self.next_page_possible == 'True':
            # Determine current item number, next item number, next_url
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
        list_item = ''
        is_folder = False
        # Create a list for our items.
        listing = []

        #
        # Get HTML page...
        #
        html_source = HTTPCommunicator().get(self.video_list_page_url)

        # Parse response...
        soup = BeautifulSoup(html_source)

        # Get the items from the RSS feed
        # <item>
        # <title>Yarvik Xenta 97ic+ &#039;Retina&#039; Android tablet review</title>
        # <description>Yarvik bracht onlangs de Xentra 97ic+ uit, een Android 4.1 tablet met hetzelfde high-res scherm dat ook in de Retina versies van Apple&#039;s iPad worden gebruikt. Voordeel van de tablet van Yarvik is dat slechts zo&#039;n 230 euro kost. Wij zochten uit of er ook nog ergens een addertje onder het gras zit.</description>
        # <pubDate>Mon, 10 Jun 2013 12:34:00 +0200</pubDate>
        # <enclosure url="http://content.hwigroup.net/videos/hwitv-ep498-yarvik/hwitv-ep498-yarvik-1.mp4" type="video/mpeg" />
        # <enclosure url="http://content.hwigroup.net/images/video/video_thumb/000609.jpg" type="image/jpg" />
        # <enclosure url="http://content.hwigroup.net/images/video/video_430/000609.jpg" type="image/jpg" />
        # <guid isPermaLink="false">http://content.hwigroup.net/videos/hwitv-ep498-yarvik/hwitv-ep498-yarvik-1.mp4</guid>
        # <enclosure url="http://youtube.com/watch?v=-TBPcTmZVWI" type="video/youtube" />
        # </item>
        items = soup.findAll('item')

        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "len(items)", str(len(items))), xbmc.LOGNOTICE)

        for item in items:

            # Get the 4 enclosure url's in the item
            # There must be a better way to do this with beautiful soup, but it'll have to do for now
            item_string = str(item)
            start_pos_of_enclosure_1 = item_string.find('enclosure url="', 0)
            start_pos_of_enclosure_url_1 = start_pos_of_enclosure_1 + len('enclosure url="')
            end_pos_of_enclosure_url_1 = item_string.find('"', start_pos_of_enclosure_url_1)
            enclosure_url_1 = item_string[start_pos_of_enclosure_url_1:end_pos_of_enclosure_url_1]

            start_pos_of_enclosure_2 = item_string.find('enclosure url="', start_pos_of_enclosure_1 + 1)
            start_pos_of_enclosure_url_2 = start_pos_of_enclosure_2 + len('enclosure url="')
            end_pos_of_enclosure_url_2 = item_string.find('"', start_pos_of_enclosure_url_2)
            enclosure_url_2 = item_string[start_pos_of_enclosure_url_2:end_pos_of_enclosure_url_2]

            # this enclosure contains the hi res thumbnail
            start_pos_of_enclosure_3 = item_string.find('enclosure url="', start_pos_of_enclosure_2 + 1)
            start_pos_of_enclosure_url_3 = start_pos_of_enclosure_3 + len('enclosure url="')
            end_pos_of_enclosure_url_3 = item_string.find('"', start_pos_of_enclosure_url_3)
            enclosure_url_3 = item_string[start_pos_of_enclosure_url_3:end_pos_of_enclosure_url_3]

            # this enclosure contains the youtube link
            start_pos_of_enclosure_4 = item_string.find('enclosure url="', start_pos_of_enclosure_3 + 1)
            start_pos_of_enclosure_url_4 = start_pos_of_enclosure_4 + len('enclosure url="')
            end_pos_of_enclosure_url_4 = item_string.find('"', start_pos_of_enclosure_url_4)
            enclosure_url_4 = item_string[start_pos_of_enclosure_url_4:end_pos_of_enclosure_url_4]

            if self.DEBUG == 'true':
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "enclosure_url_3", str(enclosure_url_3)), xbmc.LOGNOTICE)
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "enclosure_url_4", str(enclosure_url_4)), xbmc.LOGNOTICE)

            # Get youtube_id
            # http://youtube.com/watch?v=GCnXAEdPDSo
            youtube_id = enclosure_url_4[len("http://youtube.com/watch?v="):]
            youtube_url = 'plugin://plugin.video.youtube/play/?video_id=%s' % youtube_id

            if self.DEBUG == 'true':
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "youtube_url", str(youtube_url)), xbmc.LOGNOTICE)

            # Get thumbnail url
            thumbnail_url = enclosure_url_3

            if self.DEBUG == 'true':
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "thumbnail_url", str(thumbnail_url)), xbmc.LOGNOTICE)

            # Get title
            title = item.title.string

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
            # in the title of the item a single-quote "'" is represented as "&#039;" for some reason . Therefore this replace is needed to fix that.
            title = title.replace("&#039;", "'")

            if self.DEBUG == 'true':
                xbmc.log(
                    "[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "title", str(title)),
                    xbmc.LOGNOTICE)

            # Add to list...
            list_item = xbmcgui.ListItem(title, thumbnailImage=thumbnail_url)
            list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'true')
            is_folder = False
            url = youtube_url
            # Add refresh option to context menu
            list_item.addContextMenuItems([('Refresh', 'Container.Refresh')])
            # Add our item to the listing as a 3-element tuple.
            listing.append((url, list_item, is_folder))

        # Next page entry...
        if self.next_page_possible == 'True':
            list_item = xbmcgui.ListItem(LANGUAGE(30503), thumbnailImage=os.path.join(IMAGES_PATH, 'next-page.png'))
            list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'false')
            parameters = {"action": "list-play", "plugin_category": self.plugin_category, "url": str(self.next_url),
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
