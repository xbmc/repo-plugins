#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
import os
import sys
import urllib
import urlparse
import requests
from time import strptime
import xbmc
import xbmcgui
import xbmcplugin
from BeautifulSoup import BeautifulSoup

from nlhardwareinfo_const import ADDON, SETTINGS, LANGUAGE, IMAGES_PATH, DATE, VERSION, HEADERS


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

                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                        ADDON, VERSION, DATE, "self.next_url", str(urllib.unquote_plus(self.next_url))),
                             xbmc.LOGDEBUG)

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
        response = requests.get(self.video_list_page_url, headers=HEADERS)
        html_source = response.text
        html_source = html_source.encode('utf-8', 'ignore')

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

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "len(items)", str(len(items))), xbmc.LOGDEBUG)

        for item in items:

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "item", str(item)), xbmc.LOGDEBUG)

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

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "enclosure_url_3", str(enclosure_url_3)), xbmc.LOGDEBUG)
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "enclosure_url_4", str(enclosure_url_4)), xbmc.LOGDEBUG)

            # Get youtube_id
            # http://youtube.com/watch?v=GCnXAEdPDSo
            youtube_id = enclosure_url_4[len("http://youtube.com/watch?v="):]
            youtube_url = 'plugin://plugin.video.youtube/play/?video_id=%s' % youtube_id

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "youtube_url", str(youtube_url)), xbmc.LOGDEBUG)

            # Get thumbnail url
            thumbnail_url = enclosure_url_3

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "thumbnail_url", str(thumbnail_url)), xbmc.LOGDEBUG)

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

            xbmc.log(
                    "[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "title", str(title)),
                    xbmc.LOGDEBUG)

            context_menu_items = []
            # Add refresh option to context menu
            context_menu_items.append((LANGUAGE(30104), 'Container.Refresh'))
            # Add episode  info to context menu
            context_menu_items.append((LANGUAGE(30105), 'XBMC.Action(Info)'))

            # <title>Samsung Galaxy S7 en S7 Edge review</title>
            # <description>Vanaf vandaag zijn ze eindelijk te koop, de nieuwe Galaxy S7 en S7 Edge van Samsung. De nieuwe toestellen bieden onder andere een betere camera, snellere processor én een grotere accu. Wij konden de afgelopen weken al aan de slag met beide toestellen in deze videoreview vergelijken we ze met de Galaxy S6 én met alle andere high-end smartphones van dit moment.</description>
            # <pubdate>Fri, 01 Mar 2016 17:40:00 +0100</pubdate>
            # <enclosure url="https://content.hwigroup.net/videos/hwitv-ep843-s7/hwitv-ep843-s7-1.mp4" type="video/mpeg">
            # </enclosure><enclosure url="https://content.hwigroup.net/images/video/video_thumb/000979.jpg" type="image/jpg">
            # </enclosure><enclosure url="https://content.hwigroup.net/images/video/video_430/000979.jpg" type="image/jpg">
            # <guid ispermalink="false">https://content.hwigroup.net/videos/hwitv-ep843-s7/hwitv-ep843-s7-1.mp4</guid>
            # </enclosure><enclosure url="http://youtube.com/watch?v=C7ntLwmxOrY" type="video/youtube">
            # </enclosure></item>

            # Get description
            plot = item.description.string
            # in the title of the item a single-quote "'" is represented as "&#039;" for some reason . Therefore this replace is needed to fix that.
            plot = plot.replace("&#039;", "'")

            # Get pupdate
            pubdate = item.pubdate.string
            # Extract date time fields
            day = pubdate[len('Fri, '):len('Fri, ') + 2]
            month_name = pubdate[len('Fri, 01 '):len('Fri, 01 ') + 3]
            year = pubdate[len('Fri, 01 Mar '):len('Fri, 01 Mar ') + 4]
            hour = pubdate[len('Fri, 01 Mar 2016 '):len('Fri, 01 Mar 2016 ') + 2]
            minute = pubdate[len('Fri, 01 Mar 2016 17:'):len('Fri, 01 Mar 2016 17:') + 2]
            second = pubdate[len('Fri, 01 Mar 2016 17:40:'):len('Fri, 01 Mar 2016 17:40:') + 2]

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "extracted pubdate", str(day + '/' + month_name + '/' + year + '/' + hour + '/' + minute + '/' + second)), xbmc.LOGDEBUG)

            month_numeric = strptime(month_name, '%b').tm_mon

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "month_numeric", str(month_numeric)), xbmc.LOGDEBUG)

            if len(str(month_numeric)) == 1:
                month = '0' + str(month_numeric)
            else:
                month = str(month_numeric)

            # Dateadded has this form: 2009-04-05 23:16:04
            dateadded = year + '-' + month + '-' + day + ' ' + hour + ':' + minute + ':' + second

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "dateadded", str(dateadded)), xbmc.LOGDEBUG)

            meta = {'plot': plot,
                    'duration': '',
                    'year': year,
                    'dateadded': dateadded}

            add_sort_methods()

            # Add to list...
            list_item = xbmcgui.ListItem(title, thumbnailImage=thumbnail_url)
            list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'true')
            is_folder = False
            url = youtube_url
            list_item.setInfo("mediatype", "video")
            list_item.setInfo("video", meta)
            # Adding context menu items to context menu
            list_item.addContextMenuItems(context_menu_items, replaceItems=False)
            # Add our item to the listing as a 3-element tuple.
            listing.append((url, list_item, is_folder))

        # Next page entry...
        if self.next_page_possible == 'True':
            context_menu_items = []
            # Add refresh option to context menu
            context_menu_items.append((LANGUAGE(30104), 'Container.Refresh'))

            list_item = xbmcgui.ListItem(LANGUAGE(30503), thumbnailImage=os.path.join(IMAGES_PATH, 'next-page.png'))
            list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'false')
            parameters = {"action": "list-play", "plugin_category": self.plugin_category, "url": str(self.next_url),
                          "next_page_possible": self.next_page_possible}
            url = self.plugin_url + '?' + urllib.urlencode(parameters)
            is_folder = True
            # Adding context menu items to context menu
            list_item.addContextMenuItems(context_menu_items, replaceItems=False)
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

def add_sort_methods():
    sort_methods = [xbmcplugin.SORT_METHOD_UNSORTED,xbmcplugin.SORT_METHOD_LABEL,xbmcplugin.SORT_METHOD_DATE,xbmcplugin.SORT_METHOD_DURATION,xbmcplugin.SORT_METHOD_EPISODE]
    for method in sort_methods:
        xbmcplugin.addSortMethod(int(sys.argv[1]), sortMethod=method)