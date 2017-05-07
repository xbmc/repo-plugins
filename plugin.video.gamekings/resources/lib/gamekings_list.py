#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
import os
import requests
import re
import sys
import urllib
import urlparse
import xbmc
import xbmcgui
import xbmcplugin
from BeautifulSoup import BeautifulSoup

from gamekings_const import ADDON, SETTINGS, LANGUAGE, IMAGES_PATH, DATE, VERSION, BASE_URL_GAMEKINGS_TV

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
        self.BASE_URL = SETTINGS.getSetting('base-url')
        if self.BASE_URL == '':
            self.BASE_URL = BASE_URL_GAMEKINGS_TV
        else:
            if self.BASE_URL.endswith("/"):
                pass
            else:
                # Add a slash at the end
                self.BASE_URL = self.BASE_URL + "/"

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % (
                ADDON, VERSION, DATE, "ARGV", repr(sys.argv), "File", str(__file__)), xbmc.LOGDEBUG)
        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, "self.BASE_URL", str(self.BASE_URL)),
                 xbmc.LOGDEBUG)

        # Parse parameters
        self.plugin_category = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['plugin_category'][0]
        self.video_list_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['url'][0]
        self.next_page_possible = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['next_page_possible'][0]

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "self.video_list_page_url", str(self.video_list_page_url)),
                     xbmc.LOGDEBUG)

        if self.next_page_possible == 'True':
            # Determine current item number, next item number, next_url
            # f.e. http://www.gamekings.tv/category/videos/page/001/
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

                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                        ADDON, VERSION, DATE, "self.next_url", str(urllib.unquote_plus(self.next_url))),
                             xbmc.LOGDEBUG)

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

        #
        # Get HTML page
        #
        response = requests.get(self.video_list_page_url)
        html_source = response.text
        html_source = html_source.encode('utf-8', 'ignore')

        # Parse response
        soup = BeautifulSoup(html_source)

        # Get the items. Each item contains a title, a video page url and a thumbnail url
        # <div class="post post--horizontal">
        #   <a href="http://www.gamekings.tv/videos/e3-2016-vooruitblik-met-shelly/" title="E3 2016 Vooruitblik met Shelly" class="post__thumb">
        #     <img width="270" height="170" data-original="http://www.gamekings.tv/wp-content/uploads/20160527_E3vooruitblikShelly-270x170.jpg"
        #        alt="E3 2016 Vooruitblik met Shelly" class="post__image  lazy">
        #   </a>
        #   <h3 class="post__title">
        #     <a href="http://www.gamekings.tv/videos/e3-2016-vooruitblik-met-shelly/" class="post__titlelink">E3 2016 Vooruitblik met Shelly                </a>
        #   </h3>
        #   <p class="post__summary">De regeltante aan het woord in deze vooruitblik!            </p>
        #     <div class="meta">
        #       <a href="http://www.gamekings.tv/meer-alles/?kings=8284,12375" class="meta__item">Jan &amp; Shelly</a>
        #         <span class="meta__item">07/06/2016</span>
        #       <a href="http://www.gamekings.tv/videos/e3-2016-vooruitblik-met-shelly/#comments" class="meta__item  meta--comments  disqus-comment-count" data-disqus-url="http://www.gamekings.tv/videos/e3-2016-vooruitblik-met-shelly/">0</a>
        #     </div>

        items = soup.findAll('a', attrs={'href': re.compile("^" + self.BASE_URL)})

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "len(items)",
                str(len(items))),
                     xbmc.LOGDEBUG)

        # Create a list for our items.
        listing = []

        for item in items:
            video_page_url = item['href']

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "video_page_url", str(video_page_url)), xbmc.LOGDEBUG)

            # if link ends with a '/': process the link, if not: skip the link
            if video_page_url.endswith('/'):
                pass
            else:
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "skipped video_page_url not ending on '/'",
                    str(video_page_url)),
                         xbmc.LOGDEBUG)
                continue

            # this is category Videos or Afleveringen
            if self.plugin_category == LANGUAGE(30000) or self.plugin_category == LANGUAGE(30001):
                if str(video_page_url).lower().find('videos') >= 0:
                    pass
                elif str(video_page_url).lower().find('uncategorized') >= 0:
                    pass
                elif str(video_page_url).lower().find('premium') >= 0:
                    pass
                else:
                    # skip the url if it is not a video
                    xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                        ADDON, VERSION, DATE, "skipped video_page_url",
                        str(video_page_url)), xbmc.LOGDEBUG)
                    continue

            # Make title
            try:
                title = item['title']
            except:
                # skip the item if it's got no title
                continue

            try:
                # convert from unicode to encoded text (don't use str() to do this)
                title = title.encode('utf-8')
            except:
                pass

            # this is category Gamekings Extra
            if self.plugin_category == LANGUAGE(30002):
                if str(title).lower().find('extra') >= 0:
                    pass
                elif str(title).lower().find('extra') >= 0:
                    pass
                else:
                    # skip the url
                    xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                            ADDON, VERSION, DATE, "skipped non-extra title in gamekings extra category",
                            str(video_page_url)), xbmc.LOGDEBUG)
                    continue

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

            title = str(title).replace("aflevering", "Aflevering")
            title = str(title).replace("Aflevering", str(LANGUAGE(30204)))
            title = str(title).replace("Gamekings Extra: ", "")
            title = str(title).replace("Gamekings Extra over ", "")
            title = str(title).replace("Extra: ", "")
            title = str(title).replace("Extra over ", "")
            title = title.capitalize()

            xbmc.log(
                    "[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "title", str(title)),
                    xbmc.LOGDEBUG)

            # Make thumbnail
            try:
                thumbnail_url = item.img['data-original']
            except:
                # skip the item if it has no thumbnail
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                        ADDON, VERSION, DATE, "skipping item with no thumbnail",
                        str(item)), xbmc.LOGDEBUG)
                continue

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "thumbnail_url", str(thumbnail_url)), xbmc.LOGDEBUG)

            list_item = xbmcgui.ListItem(label=title, thumbnailImage=thumbnail_url)
            list_item.setInfo("video", {"title": title, "studio": ADDON})
            list_item.setInfo("mediatype", "video")
            list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                              'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'true')
            parameters = {"action": "play", "video_page_url": video_page_url, "plugin_category": self.plugin_category,
                          "title": title}
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
