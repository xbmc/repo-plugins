#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import object
from resources.lib.powerunlimited_const import LANGUAGE, HEADERS, convertToUnicodeString, log, getSoup
import re
import sys
import urllib.request, urllib.parse, urllib.error
import xbmc
import xbmcgui
import xbmcplugin
import requests


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
        self.video_page_url = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['video_page_url'][0]

        log("self.video_page_url", self.video_page_url)

        #
        # Play video
        #
        self.playVideo()

    #
    # Play video
    #
    def playVideo(self):
        #
        # Init
        #
        no_url_found = False
        unplayable_media_file = False
        have_valid_url = False
        dialog_wait = xbmcgui.DialogProgress()

        #
        # Get current list item details
        #
        #title = xbmc.getInfoLabel("listitem.Title")
        thumbnail = xbmc.getInfoImage("list_item.Thumb")
        #studio = xbmc.getInfoLabel("list_item.Studio")
        plot = xbmc.getInfoLabel("list_item.Plot")
        genre = xbmc.getInfoLabel("list_item.Genre")

        #
        # Get HTML page
        #
        response = requests.get(self.video_page_url, headers=HEADERS)

        html_source = response.text
        html_source = convertToUnicodeString(html_source)

        # Parse response
        soup = getSoup(html_source)

        youtube_url = ""

        # Parse video file url
        # <iframe width="967" height="544" src="https://www.youtube.com/embed/-XpoD7OgLFM?feature=oembed" frameborder="0" allowfullscreen>
        # or
        # <iframe width="967" height="544" src="https://www.youtube.com/embed/-XpoD7OgLFM" frameborder="0" allowfullscreen>
        video_urls = soup.findAll('iframe', attrs={'src': re.compile("^https://www.youtube.com/embed")}, limit=1)
        if len(video_urls) == 0:
            no_url_found = True
        else:
            for video_url in video_urls:
                video_url = video_urls[0]['src']

                log("video_url", video_url)

                have_valid_url = True
                # make youtube plugin url
                pos_of_last_question_mark = video_url.rfind("?")
                if pos_of_last_question_mark >= 0:
                    video_url = video_url[0: pos_of_last_question_mark]
                video_url_len = len(video_url)
                youtubeID = video_url[len("https://www.youtube.com/embed/"):video_url_len]
                youtube_url = 'plugin://plugin.video.youtube/play/?video_id=%s' % youtubeID

        log("have_valid_url", have_valid_url)

        log("youtube_url", youtube_url)

        if have_valid_url:
            video_url = youtube_url
            list_item = xbmcgui.ListItem(path=video_url)
            xbmcplugin.setResolvedUrl(self.plugin_handle, True, list_item)
        #
        # Alert user
        #
        elif no_url_found:
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30505))
        elif unplayable_media_file:
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30506))