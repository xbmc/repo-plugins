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

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % (
            ADDON, VERSION, DATE, "ARGV", repr(sys.argv), "File", str(__file__)), xbmc.LOGDEBUG)

        # Parse parameters
        self.plugin_category = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['plugin_category'][0]
        self.video_list_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['url'][0]
        self.next_page_possible = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['next_page_possible'][0]

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, "self.video_list_page_url", str(self.video_list_page_url)),
                 xbmc.LOGDEBUG)

        if self.next_page_possible == 'True':
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

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "self.base_url", str(self.base_url)), xbmc.LOGDEBUG)

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
        # first 3 posts:
        # <li style = "background-image: url('http://botchamania.com/wp-content/uploads/2016/03/botchamania-300.jpg') !important">
        # <a href = "http://botchamania.com/2016/03/13/botchamania-300/">
        # <article id = "post-5333" class ="post-5333 post type-post status-publish format-standard has-post-thumbnail hentry category-botchamania tag-aj-styles tag-botchamania tag-botchamania-300 tag-brock-lesnar tag-john-cena tag-ladder-match tag-maffew tag-tna tag-wrestling tag-wwe tag-wwe-fast-lane-2016 tag-wwf">
        # <footer class ="entry-footer">
        # <h3 class ="entry-category">botchamania </ h3>
        # </ footer> <!--.entry - footer -->
        # <header class ="entry-header">
        # <h2 class ="entry-title"> Botchamania 300 </ h2>
        # </header>
        # <div class ="entry-content">
        # <div class ="entry-description">
        # <p> Same as it’s always been, it’s Botchamania 300: Paul London Has Fallen!</ p>
        # </ div>
        # </ div> <!--.entry - content -->
        # </ article> </ a> <!--  # post-## -->
        # </ li>

        # post 4 and up:
        # <li>
        # <a href = "http://botchamania.com/2016/01/18/botchamania-298/">
        # <article id = "post-5286" class ="post-5286 post type-post status-publish format-standard has-post-thumbnail hentry category-botchamania tag-botchamania tag-botchamania-298 tag-botches tag-czw tag-john-cena tag-kenny-omega tag-knockout-battle-royal tag-mistakes tag-njpw tag-nwa tag-pwg tag-tna tag-wcw tag-wrestle-kingdom-10 tag-wrestling tag-wwe tag-wwf tag-xpw">
        # <img class ="entry-image" src="http://botchamania.com/wp-content/uploads/2016/01/botchamania-298.jpg">
        # <div class ="entry-content">
        # <footer class ="entry-footer">
        # <h3 class ="entry-category">botchamania </ h3>
        # </ footer> <!--.entry - footer -->
        # <header class ="entry-header">
        # <h2 class ="entry-title">Botchamania 298 </ h2>
        # </ header>
        # </ div>
        # </ article> </ a> <!--  # post-## -->
        # </ li>
        titles_thumbnail_videopage_urls = soup.findAll('li')

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, "len(titles_thumbnail_videopage_urls)",
            str(len(titles_thumbnail_videopage_urls))), xbmc.LOGDEBUG)

        for titles_thumbnail_videopage_url in titles_thumbnail_videopage_urls:
            if str(titles_thumbnail_videopage_url).__contains__("article id"):
                pass
            else:
                # skip this one
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "skipping this video_page_url", str(titles_thumbnail_videopage_url)),
                         xbmc.LOGDEBUG)
                continue

            video_page_url = titles_thumbnail_videopage_url.a['href']

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "video_page_url", str(video_page_url)), xbmc.LOGDEBUG)

            title = ''
            # Make title
            try:
                title = titles_thumbnail_videopage_url.h2.string
                title = title.strip()
                # convert from unicode to encoded text (don't use str() to do this)
                title = title.encode('utf-8')
            except KeyError:
                pass
            except UnicodeDecodeError:
                pass

            title = title.replace('-', ' ')
            title = title.replace('/', ' ')
            title = title.replace('_', ' ')
            # welcome to characterset-hell
            title = title.replace('&#038;', '&')
            title = title.replace('&#8211;', '-')
            title = title.replace("&#8217;", "'")
            title = title.replace('&#8220;', '"')
            title = title.replace('&#8221;', '"')

            xbmc.log(
                "[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "title", str(title)),
                xbmc.LOGDEBUG)

            thumbnail_url = ""
            try:
                thumbnail_url = str(titles_thumbnail_videopage_url['style'])
                thumbnail_url = thumbnail_url.replace("background-image: url('", "")
                thumbnail_url = thumbnail_url[0:thumbnail_url.find("'")]
            except (TypeError, KeyError):
                pass

            if thumbnail_url == "":
                try:
                    thumbnail_url = titles_thumbnail_videopage_url.img['src']
                except (TypeError, KeyError):
                    pass

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "thumbnail_url", str(thumbnail_url)), xbmc.LOGDEBUG)

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

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "next url", str(url)), xbmc.LOGDEBUG)

        # Add our listing to Kodi.
        # Large lists and/or slower systems benefit from adding all items at once via addDirectoryItems
        # instead of adding one by ove via addDirectoryItem.
        xbmcplugin.addDirectoryItems(self.plugin_handle, listing, len(listing))
        # Disable sorting
        xbmcplugin.addSortMethod(handle=self.plugin_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.plugin_handle)
