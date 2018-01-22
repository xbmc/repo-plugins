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

from dumpert_const import LANGUAGE, IMAGES_PATH, SETTINGS, convertToUnicodeString, log, getSoup


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

        # Parse parameters
        try:
            self.plugin_category = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['plugin_category'][0]
            self.video_list_page_url = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['url'][0]
            self.next_page_possible = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['next_page_possible'][0]
        except KeyError:
            self.plugin_category = LANGUAGE(30001)
            self.video_list_page_url = "http://www.dumpert.nl/1/"
            self.next_page_possible = "True"

        log("self.video_list_page_url", self.video_list_page_url)

        # Determine current page number and base_url
        # http://www.dumpert.nl/toppers/
        # http://www.dumpert.nl/
        # http://www.dumpert.nl/<thema>/
        # find last slash
        pos_of_last_slash = self.video_list_page_url.rfind('/')
        # remove last slash
        self.video_list_page_url = self.video_list_page_url[0: pos_of_last_slash]
        pos_of_last_slash = self.video_list_page_url.rfind('/')
        self.base_url = self.video_list_page_url[0: pos_of_last_slash + 1]
        self.current_page = self.video_list_page_url[pos_of_last_slash + 1:]
        self.current_page = int(self.current_page)
        # add last slash
        self.video_list_page_url = self.video_list_page_url + "/"

        log("self.base_url", self.base_url)

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
        titles_and_thumbnail_urls_index = 0
        # Create a list for our items.
        listing = []

        #
        # Get HTML page
        #
        if SETTINGS.getSetting('nsfw') == 'true':
            response = requests.get(self.video_list_page_url, cookies={'nsfw': '1'})
        else:
            response = requests.get(self.video_list_page_url)

        html_source = response.text
        html_source = convertToUnicodeString(html_source)

        # Parse response
        soup = getSoup(html_source)

        # Find titles and thumnail-urls
        # img src="http://static.dumpert.nl/sq_thumbs/2245331_272bd4c3.jpg" alt="Turnlulz" title="Turnlulz" width="100" height="100" />
        # titles_and_thumbnail_urls = soup.findAll('img', attrs={'src': re.compile("^http://static.dumpert.nl/")} )
        titles_and_thumbnail_urls = soup.findAll('img', attrs={'src': re.compile("thumb")})

        log("titles_and_thumbnail_urls", titles_and_thumbnail_urls)

        # Find video page urls
        # <a href="http://www.dumpert.nl/mediabase/2245331/272bd4c3/turnlulz.html" class="dumpthumb" title="Turnlulz">
        video_page_urls = soup.findAll('a', attrs={'class': re.compile("dumpthumb")})

        log("len(video_page_urls)", len(video_page_urls))

        # in thema pages the first thumbnail is a thumbnail of the thema itself and not of a video
        # if that's the case: skip the first thumbnail
        if len(titles_and_thumbnail_urls) == len(video_page_urls) + 1:
            titles_and_thumbnail_urls_index = titles_and_thumbnail_urls_index + 1

        for video_page_url in video_page_urls:
            pos_of_video_tag = str(video_page_url).find('class="video"')
            if pos_of_video_tag >= 0:
                pass
            else:
                # skip video page url without a video

                log("skipped video_page_url without video", video_page_url)

                titles_and_thumbnail_urls_index = titles_and_thumbnail_urls_index + 1
                continue

            video_page_url = video_page_url['href']

            log("video_page_url", video_page_url)

            # if link doesn't contain 'html': skip the link ('continue')
            if video_page_url.find('html') >= 0:
                pass
            else:
                log("skipped video_page_url without html", video_page_url)
                titles_and_thumbnail_urls_index = titles_and_thumbnail_urls_index + 1
                continue

            description = '...'
            #<a href="http://www.dumpert.nl/mediabase/6721593/46f416fa/stukje_snowboarden.html?thema=bikini" class="dumpthumb" title="Stukje snowboarden">
            #	<img src="http://media.dumpert.nl/sq_thumbs/6721593_46f416fa.jpg" alt="Stukje snowboarden" title="Stukje snowboarden" width="100" height="100" />
            #	<span class="video"></span>
            #	<div class="details">
            #		<h1>Stukje snowboarden</h1>
            #		<date>5 februari 2016 10:32</date>
            #		<p class="stats">views: 63687 kudos: 313</p>
            #		<p class="description">Fuck winterkleding </p>
            #	</div>
            #</a>
            try:
                description = titles_and_thumbnail_urls[titles_and_thumbnail_urls_index].parent.find("p","description").string
            except:
                pass

            # Make title
            try:
                title = titles_and_thumbnail_urls[titles_and_thumbnail_urls_index]['title']
            # <a href="http://www.dumpert.nl/mediabase/1958831/21e6267f/pixar_s_up_inspreken.html?thema=animatie" class="dumpthumb" title="Pixar's &quot;Up&quot; inspreken ">
            except KeyError:
                # http://www.dumpert.nl/mediabase/6532392/82471b66/dumpert_heeft_talent.html
                title = str(video_page_url)
                pos_last_slash = title.rfind('/')
                pos_last_dot = title.rfind('.')
                title = title[pos_last_slash + 1:pos_last_dot]
                title = title.capitalize()
            except UnicodeDecodeError:
                pass

            title = title.replace('-', ' ')
            title = title.replace('/', ' ')
            title = title.replace('_', ' ')

            log("title", title)

            if titles_and_thumbnail_urls_index >= len(titles_and_thumbnail_urls):
                thumbnail_url = ''
            else:
                thumbnail_url = titles_and_thumbnail_urls[titles_and_thumbnail_urls_index]['src'].replace("sq_thumbs","stills/large")

            list_item = xbmcgui.ListItem(label=title, thumbnailImage=thumbnail_url)
            list_item.setInfo("video", {"title": title, "studio": "Dumpert", "mediatype": "video", "plot": description})
            list_item.setArt({'thumb': thumbnail_url, 'icon': thumbnail_url,
                              'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'true')
            parameters = {"action": "play", "video_page_url": video_page_url, "title": title}
            url = self.plugin_url + '?' + urllib.parse.urlencode(parameters)
            is_folder = False
            # Add refresh option to context menu
            list_item.addContextMenuItems([('Refresh', 'Container.Refresh')])
            # Add our item to the listing as a 3-element tuple.
            listing.append((url, list_item, is_folder))

            titles_and_thumbnail_urls_index = titles_and_thumbnail_urls_index + 1

        # Next page entry
        if self.next_page_possible == 'True':
            next_page = self.current_page + 1
            list_item = xbmcgui.ListItem(LANGUAGE(30503), thumbnailImage=os.path.join(IMAGES_PATH, 'next-page.png'))
            list_item.setArt({'fanart': os.path.join(IMAGES_PATH, 'fanart-blur.jpg')})
            list_item.setProperty('IsPlayable', 'false')
            parameters = {"action": "list", "plugin_category": self.plugin_category,
                          "url": str(self.base_url) + str(next_page) + '/',
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

