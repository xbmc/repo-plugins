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

from gamekings_const import ADDON, SETTINGS, LANGUAGE, IMAGES_PATH, DATE, VERSION
from gamekings_utils import HTTPCommunicator


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
        self.plugin_category = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['plugin_category'][0]
        self.video_list_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['url'][0]
        self.next_page_possible = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['next_page_possible'][0]

        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "self.video_list_page_url", str(self.video_list_page_url)),
                     xbmc.LOGNOTICE)

        if self.next_page_possible == 'True':
            # Determine current item number, next item number, next_url
            # f.e. http://www.gamekings.nl/category/videos/page/001/
            pos_of_page = self.video_list_page_url.rfind('/page/')
            if pos_of_page >= 0:
                page_number_str = str(
                    self.video_list_page_url[pos_of_page + len('/page/'):pos_of_page + len('/page/') + len('000')])
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
        list_item = ''

        #
        # Get HTML page
        #
        html_source = HTTPCommunicator().get(self.video_list_page_url)

        # Parse response
        soup = BeautifulSoup(html_source)

        # Get the thumbnail urls
        # <img src="http://www.gamekings.nl/wp-content/uploads/20130307_gowascensionreviewsplash1-75x75.jpg" alt="God of War: Ascension Review">
        # for http://www.gamekings.nl/pcgamersunite/ the thumbnail links sometimes contain '//': f.e. http://www.gamekings.nl//wp-content/uploads/20110706_hww_alienwarelaptop_slider-75x75.jpg
        # thumbnail_urls = soup.findAll('img', attrs={'src': re.compile("^http://www.gamekings.nl/wp-content/uploads/")})
        thumbnail_urls = soup.findAll('img', attrs={'src': re.compile("^http://www.gamekings.nl/")})

        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "len(thumbnail_urls)", str(len(thumbnail_urls))), xbmc.LOGNOTICE)

        # Get the titles and video page urls
        # <a href="http://www.gamekings.nl/videos/lars-gustavsson-over-battlefield-4/" title="Lars Gustavsson over Battlefield 4">
        # skip this: <a href='http://www.gamekings.nl/videos/lars-gustavsson-over-battlefield-4/#disqus_thread'>

        video_page_urls_and_titles = ''
        # this is Videos
        if self.plugin_category == LANGUAGE(30000):
            video_page_urls_and_titles = soup.findAll('a', attrs={'href': re.compile("^http://www.gamekings.nl/")})
        # this is Afleveringen
        elif self.plugin_category == LANGUAGE(30001):
            video_page_urls_and_titles = soup.findAll('a', attrs={'href': re.compile("^http://www.gamekings.nl/")})
        # this is Gamekings Extra
        elif self.plugin_category == LANGUAGE(30002):
            video_page_urls_and_titles = soup.findAll('a',
                                                      attrs={'href': re.compile("^http://www.gamekings.nl/nieuws/")})
        # this is Trailers
        elif self.plugin_category == LANGUAGE(30003):
            video_page_urls_and_titles = soup.findAll('a',
                                                      attrs={'href': re.compile("^http://www.gamekings.nl/nieuws/")})
        # this is E3
        elif self.plugin_category == LANGUAGE(30004):
            video_page_urls_and_titles = soup.findAll('a', attrs={'href': re.compile("^http://www.gamekings.nl/")})

        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "len(video_page_urls_and_titles)",
                str(len(video_page_urls_and_titles))),
                     xbmc.LOGNOTICE)

        # Create a list for our items.
        listing = []

        for video_page_url_and_title in video_page_urls_and_titles:
            video_page_url = video_page_url_and_title['href']
            # if link ends with a '/': process the link, if not: skip the link
            if video_page_url.endswith('/'):
                pass
            else:
                if self.DEBUG == 'true':
                    xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                        ADDON, VERSION, DATE, "skipped video_page_url not ending on '/'",
                        str(video_page_url)),
                             xbmc.LOGNOTICE)
                continue

            # this is category Videos
            if self.plugin_category == LANGUAGE(30000):
                if video_page_url.find('videos') >= 0:
                    pass
                elif video_page_url.find('uncategorized') >= 0:
                    pass
                else:
                    # skip url
                    if self.DEBUG == 'true':
                        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                            ADDON, VERSION, DATE, "skipped video_page_url aflevering in video category",
                            str(video_page_url)), xbmc.LOGNOTICE)
                    continue

            # don't skip aflevering if category is 'afleveringen'
            if self.plugin_category == LANGUAGE(30001):
                pass
            # if 'aflevering' found in video page url, skip the video page url
            elif video_page_url.find('aflevering') >= 0:
                if self.DEBUG == 'true':
                    xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                        ADDON, VERSION, DATE,
                        "skipped video_page_url aflevering in non-afleveringen category",
                        str(video_page_url)), xbmc.LOGNOTICE)
                    # skip the thumbnail too
                thumbnail_urls_index = thumbnail_urls_index + 1
                continue

            # Make title
            # for category is 'afleveringen' use the video_page_url to make the title
            if self.plugin_category == LANGUAGE(30001):
                title = str(video_page_url)
                title = title[31:]
                title = title.capitalize()
            # for other categories use the title attribute
            else:
                try:
                    title = video_page_url_and_title['title']
                except:
                    # skip the item if it's got no title
                    continue

                try:
                    # convert from unicode to encoded text (don't use str() to do this)
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

            # remove space on first position in the title
            if title[0:1] == " ":
                title = title[1:]

            if self.DEBUG == 'true':
                xbmc.log(
                    "[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "title", str(title)),
                    xbmc.LOGNOTICE)

            title_lowercase = str(title.lower())

            # this is category Gamekings Extra
            if self.plugin_category == LANGUAGE(30002):
                if title_lowercase.find('gamekings extra') >= 0:
                    pass
                else:
                    # skip url
                    if self.DEBUG == 'true':
                        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                            ADDON, VERSION, DATE, "skipped video_page_url in gamekings extra category",
                            str(video_page_url)), xbmc.LOGNOTICE)
                    # skip the thumbnail too
                    thumbnail_urls_index = thumbnail_urls_index + 1
                    continue

            # this is category Gamekings Extra
            if self.plugin_category == LANGUAGE(30002):
                title = title.replace('Gamekings Extra: ', '')

            if thumbnail_urls_index >= len(thumbnail_urls):
                thumbnail_url = ''
            else:
                thumbnail_url = thumbnail_urls[thumbnail_urls_index]['src']

            if self.DEBUG == 'true':
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "thumbnail_url", str(thumbnail_url)), xbmc.LOGNOTICE)

            # in afleveringen category, skip link if there's no thumbnail. i do this because those links repeat on every page and are redundant imho.
            # it's bit of a hack but it'll do for now
            if self.plugin_category == LANGUAGE(30001):
                if thumbnail_url == '':
                    if self.DEBUG == 'true':
                        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE,
                                                                              "skipped video_page_url aflevering because it doesn't have a thumbnail",
                                                                              str(video_page_url_and_title)),
                                 xbmc.LOGNOTICE)
                    continue

            list_item = xbmcgui.ListItem(label=title, thumbnailImage=thumbnail_url)
            list_item.setInfo("video", {"title": title, "studio": ADDON})
            list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                              'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'true')
            parameters = {"action" : "play", "video_page_url" : video_page_url, "plugin_category" : self.plugin_category, "title": title}
            url = self.plugin_url + '?' + urllib.urlencode(parameters)
            is_folder = False
            # Add refresh option to context menu
            list_item.addContextMenuItems([('Refresh', 'Container.Refresh')])
            # Add our item to the listing as a 3-element tuple.
            listing.append((url, list_item, is_folder))

            thumbnail_urls_index = thumbnail_urls_index + 1

            # list_item = xbmcgui.ListItem(label=title, thumbnailImage=thumbnail_url)
            # list_item.setInfo("video", {"title": title, "studio": ADDON})
            # list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
            #                   'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            # list_item.setProperty('IsPlayable', 'true')
            # parameters = {"action": "play", "video_page_url": video_page_url, "plugin_category": self.plugin_category, "title": title}
            # url = self.plugin_url + '?' + urllib.urlencode(parameters)
            # is_folder = False
            # # Add refresh option to context menu
            # list_item.addContextMenuItems([('Refresh', 'Container.Refresh')])
            # # Add our item to the listing as a 3-element tuple.
            # listing.append((url, list_item, is_folder))

        # Next page entry
        if self.next_page_possible == 'True':
            list_item = xbmcgui.ListItem(LANGUAGE(30503), thumbnailImage=os.path.join(IMAGES_PATH, 'next-page.png'))
            list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'false')
            parameters = {"action" : "list", "plugin_category" : self.plugin_category, "url" : str(self.next_url), "next_page_possible": self.next_page_possible}
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
