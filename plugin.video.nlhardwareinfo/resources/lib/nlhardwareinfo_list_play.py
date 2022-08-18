#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import object
import os
import sys
import urllib.request, urllib.parse, urllib.error
import requests
from time import strptime
import xbmcgui
import xbmcplugin

from .nlhardwareinfo_const import LANGUAGE, IMAGES_PATH, HEADERS, convertToUnicodeString, log, getSoup


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
        if len(sys.argv[2]) == 0:
            self.plugin_category = LANGUAGE(30000)
            self.video_list_page_url = "http://nl.hardware.info/tv/rss-private/streaming"
            self.next_page_possible = "False"
        else:
            self.plugin_category = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['plugin_category'][0]
            self.video_list_page_url = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['url'][0]
            self.next_page_possible = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['next_page_possible'][0]

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

                log("self.next_url", self.next_url)

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
        # response.status
        html_source = response.text
        html_source = convertToUnicodeString(html_source)

        # Parse response
        soup = getSoup(html_source)

        # <item>
        # <title>HP Elitebook x360 review</title>
        # <description>De tijd dat HP's Elitebooks relatief saaie, zakelijke machines waren ligt achter ons. Want de nieuwe Elitebook x360 is weliswaar nog steeds een apparaat voor de zakelijke markt, maar het is vooral ook een dunne, lichte notebook met een fraai design.
        # De x360 kan bovendien ook in tablet- en in tentmodus gebruikt worden, waardoor het apparaat niet alleen geschikt is om op te werken en presentaties te geven, maar ook om onderuit op de bank wat te surfen of een film te kijken.</description>
        # <pubdate>Wed, 10 May 2017 15:45:00 +0200</pubdate>
        # <enclosure type="video/mpeg" url="https://content.hwigroup.net/videos/hwitv-ep917-elitebook/hwitv-ep917-elitebook-1.mp4">
        # <enclosure type="image/jpg" url="https://content.hwigroup.net/images/video/video_thumb/001059.jpg">
        # <enclosure type="image/jpg" url="https://content.hwigroup.net/images/video/video_430/001059.jpg">
        # <guid ispermalink="false">https://content.hwigroup.net/videos/hwitv-ep917-elitebook/hwitv-ep917-elitebook-1.mp4</guid>
        # <enclosure type="video/youtube" url="http://youtube.com/watch?v=-0Fban2eHQo">
        # </enclosure></enclosure></enclosure></enclosure>
        # </item>
        items = soup.findAll('item')

        log("len(items)", len(items))

        for item in items:

            # log("item)", item)

            # Get the 4 enclosure url's in the item
            # There must be a better way to do this with beautiful soup, but it'll have to do for now
            item_string = str(item)
            start_pos_of_enclosure_1 = item_string.find('url="', 0)
            start_pos_of_enclosure_url_1 = start_pos_of_enclosure_1 + len('url="')
            end_pos_of_enclosure_url_1 = item_string.find('"', start_pos_of_enclosure_url_1)
            enclosure_url_1 = item_string[start_pos_of_enclosure_url_1:end_pos_of_enclosure_url_1]

            start_pos_of_enclosure_2 = item_string.find('url="', start_pos_of_enclosure_1 + 1)
            start_pos_of_enclosure_url_2 = start_pos_of_enclosure_2 + len('url="')
            end_pos_of_enclosure_url_2 = item_string.find('"', start_pos_of_enclosure_url_2)
            enclosure_url_2 = item_string[start_pos_of_enclosure_url_2:end_pos_of_enclosure_url_2]

            # this enclosure contains the hi res thumbnail
            start_pos_of_enclosure_3 = item_string.find('url="', start_pos_of_enclosure_2 + 1)
            start_pos_of_enclosure_url_3 = start_pos_of_enclosure_3 + len('url="')
            end_pos_of_enclosure_url_3 = item_string.find('"', start_pos_of_enclosure_url_3)
            enclosure_url_3 = item_string[start_pos_of_enclosure_url_3:end_pos_of_enclosure_url_3]

            # this enclosure contains the youtube link
            start_pos_of_enclosure_4 = item_string.find('url="', start_pos_of_enclosure_3 + 1)
            start_pos_of_enclosure_url_4 = start_pos_of_enclosure_4 + len('url="')
            end_pos_of_enclosure_url_4 = item_string.find('"', start_pos_of_enclosure_url_4)
            enclosure_url_4 = item_string[start_pos_of_enclosure_url_4:end_pos_of_enclosure_url_4]

            log("enclosure_url_1", enclosure_url_1)
            log("enclosure_url_2", enclosure_url_2)
            log("enclosure_url_3", enclosure_url_3)
            log("enclosure_url_4", enclosure_url_4)

            # Get youtube_id
            # http://youtube.com/watch?v=GCnXAEdPDSo
            youtube_id = enclosure_url_4[len("http://youtube.com/watch?v="):]
            youtube_url = 'plugin://plugin.video.youtube/play/?video_id=%s' % youtube_id

            log("youtube_url", youtube_url)

            # Get thumbnail url
            thumbnail_url = enclosure_url_3

            log("thumbnail_url", thumbnail_url)

            # Get title
            title = item.title.string

            log("title", title)

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

            # Get pupdate
            pubdate = item.pubdate.string
            # Extract date time fields
            day = pubdate[len('Fri, '):len('Fri, ') + 2]
            month_name = pubdate[len('Fri, 01 '):len('Fri, 01 ') + 3]
            year = pubdate[len('Fri, 01 Mar '):len('Fri, 01 Mar ') + 4]
            hour = pubdate[len('Fri, 01 Mar 2016 '):len('Fri, 01 Mar 2016 ') + 2]
            minute = pubdate[len('Fri, 01 Mar 2016 17:'):len('Fri, 01 Mar 2016 17:') + 2]
            second = pubdate[len('Fri, 01 Mar 2016 17:40:'):len('Fri, 01 Mar 2016 17:40:') + 2]

            log("extracted pubdate", day + '/' + month_name + '/' + year + '/' + hour + '/' + minute + '/' + second)

            month_numeric = strptime(month_name, '%b').tm_mon

            log("month_numeric", month_numeric)

            if len(str(month_numeric)) == 1:
                month = '0' + str(month_numeric)
            else:
                month = str(month_numeric)

            # Dateadded has this form: 2009-04-05 23:16:04
            dateadded = year + '-' + month + '-' + day + ' ' + hour + ':' + minute + ':' + second

            log("dateadded", dateadded)

            meta = {'plot': plot,
                    'duration': '',
                    'year': year,
                    'dateadded': dateadded}

            add_sort_methods()

            # Add to list...
            list_item = xbmcgui.ListItem(title)
            list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                              'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
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
            thumbnail_url = os.path.join(IMAGES_PATH, 'next-page.png')
            list_item = xbmcgui.ListItem(LANGUAGE(30503))
            list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                              'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'false')
            parameters = {"action": "list-play", "plugin_category": self.plugin_category, "url": str(self.next_url),
                          "next_page_possible": self.next_page_possible}
            url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
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