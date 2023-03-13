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

from gamekings_const import ADDON, LANGUAGE, IMAGES_PATH, BASE_URL_GAMEKINGS_TV, PREMIUM_ONLY_VIDEO_TITLE_PREFIX, \
    convertToUnicodeString, log, getSoup

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

        # Parse parameters
        try:
            self.plugin_category = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['plugin_category'][0]
            self.video_list_page_url = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['url'][0]
            self.next_page_possible = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['next_page_possible'][0]
        except KeyError:
            self.plugin_category = LANGUAGE(30000)
            self.video_list_page_url = BASE_URL_GAMEKINGS_TV + "category/videos/page/001/"
            self.next_page_possible = "True"

        log("self.video_list_page_url", self.video_list_page_url)

        if self.next_page_possible == 'True':
            # Determine current item number, next item number, next_url
            # f.e. https://www.gamekings.tv/category/videos/page/001/
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

                log("self.next_url", self.next_url)

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
        # Create a list for our items.
        listing = []

        #
        # Get HTML page
        #
        response = requests.get(self.video_list_page_url)

        html_source = response.text
        html_source = convertToUnicodeString(html_source)

        # Parse response
        soup = getSoup(html_source)

        # Get the items. Each item contains a title, a video page url and a thumbnail url
        #
        # <div class="post post--horizontal">
        #   <a href="https://www.gamekings.tv/videos/e3-2016-vooruitblik-met-shelly/" title="E3 2016 Vooruitblik met Shelly" class="post__thumb">
        #     <img width="270" height="170" data-original="https://www.gamekings.tv/wp-content/uploads/20160527_E3vooruitblikShelly-270x170.jpg"
        #        alt="E3 2016 Vooruitblik met Shelly" class="post__image  lazy">
        #   </a>
        #
        #   <h3 class="post__title">
        #   or
        #   <h3 class="post__title post__title--premium">
        #
        #     <a href="https://www.gamekings.tv/videos/e3-2016-vooruitblik-met-shelly/" class="post__titlelink">E3 2016 Vooruitblik met Shelly                </a>
        #   </h3>
        #   <p class="post__summary">De regeltante aan het woord in deze vooruitblik!            </p>
        #     <div class="meta">
        #       <a href="https://www.gamekings.tv/meer-alles/?kings=8284,12375" class="meta__item">Jan &amp; Shelly</a>
        #         <span class="meta__item">07/06/2016</span>
        #       <a href="https://www.gamekings.tv/videos/e3-2016-vooruitblik-met-shelly/#comments" class="meta__item  meta--comments  disqus-comment-count" data-disqus-url="https://www.gamekings.tv/videos/e3-2016-vooruitblik-met-shelly/">0</a>
        #     </div>

        # Sometimes the videos on the frontpage are not yet present on the video page, therefore added an videos on frontpage section
        if self.video_list_page_url == BASE_URL_GAMEKINGS_TV:
            # find the videos on the frontpage
            items = soup.findAll('a', attrs={'class': re.compile("^" + "slider__link")})
        else:
            # find the videos on the video page
            items = soup.findAll('div', attrs={'class': re.compile("^" + "post")})

        log("len(items", len(items))

        for item in items:

            item = convertToUnicodeString(item)

            # log("item", item)

            if self.video_list_page_url == BASE_URL_GAMEKINGS_TV:
                title = item.text

                video_page_url = item['href']

                log("video_page_url", video_page_url)

                thumbnail_url = ""

            else:
                # if item contains 'postcontainer, skip the item
                if str(item).find('postcontainer') >= 0:

                    # log("skipped item containing 'postcontainer'", item)

                    continue

                video_page_url = item.a['href']

                log("video_page_url", video_page_url)

                # if link ends with a '/': process the link, if not: skip the link
                if video_page_url.endswith('/'):
                    pass
                else:

                    log("skipped video_page_url not ending on '/'", video_page_url)

                    continue

                # Make title
                try:
                    title = item.a['title']
                except:
                    # skip the item if it's got no title
                    continue

                # this is category Gamekings Extra
                if self.plugin_category == LANGUAGE(30002):
                    if str(title).lower().find('extra') >= 0:
                        pass
                    elif str(title).lower().find('extra') >= 0:
                        pass
                    else:
                        # skip the url

                        log("skipped non-extra title in gamekings extra category", video_page_url)

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
            title = title.replace("aflevering", "Aflevering")
            title = title.replace("Aflevering", (LANGUAGE(30204)))
            title = title.replace("Gamekings Extra: ", "")
            title = title.replace("Gamekings Extra over ", "")
            title = title.replace("Extra: ", "")
            title = title.replace("Extra over ", "")
            title = title.strip()
            title = title.capitalize()

            # log("title", title)

            if str(item).find("title--premium") >= 0:
                title = PREMIUM_ONLY_VIDEO_TITLE_PREFIX + ' ' + title
            elif str(item).lower().find("premium") >= 0:
                title = PREMIUM_ONLY_VIDEO_TITLE_PREFIX + ' ' + title

            # Make thumbnail
            try:
                thumbnail_url = item.a.img['data-original']
            except:
                if self.video_list_page_url == BASE_URL_GAMEKINGS_TV:
                    pass
                else:
                    # skip the item if it has no thumbnail

                    log("skipping item with no thumbnail", item)

                    continue

            list_item = xbmcgui.ListItem(label=title, thumbnailImage=thumbnail_url)
            list_item.setInfo("video", {"title": title, "studio": ADDON})
            list_item.setInfo("mediatype", "video")
            list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                              'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'true')
            parameters = {"action": "play", "video_page_url": video_page_url, "plugin_category": self.plugin_category}
            url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
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
            url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
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