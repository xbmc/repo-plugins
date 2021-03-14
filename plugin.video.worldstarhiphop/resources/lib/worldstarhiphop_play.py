#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
# the YDStreamExtractor needs to be before the future imports. Otherwise u get an 'check hostname' error.
import YDStreamExtractor
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import object

import requests
import sys
import urllib.parse
import xbmc
import xbmcgui
import xbmcplugin
import re

from resources.lib.worldstarhiphop_const import SETTINGS, LANGUAGE, HEADERS, convertToUnicodeString, log, getSoup
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

        # Get plugin settings
        self.VIDEO = SETTINGS.getSetting('video')

        log("ARGV", repr(sys.argv))

        # Parse parameters...
        self.video_page_url = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['video_page_url'][0]

        log("self.video_page_url", self.video_page_url)

        #
        # Play video...
        #
        self.playVideo()

    #
    # Play video...
    #
    def playVideo(self):
        #
        # Init
        #
        is_folder = False
        # Create a list for our items.
        listing = []
        unplayable_media_file = False
        have_valid_url = False
        dialogWait = xbmcgui.DialogProgress()

        #
        # Get current list item details...
        #
        # title = convertToUnicodeString(xbmc.getInfoLabel("list_item.Title"))
        thumbnail_url = convertToUnicodeString(xbmc.getInfoImage("list_item.Thumb"))
        # studio = convertToUnicodeString(xbmc.getInfoLabel("list_item.Studio"))
        plot = convertToUnicodeString(xbmc.getInfoLabel("list_item.Plot"))
        genre = convertToUnicodeString(xbmc.getInfoLabel("list_item.Genre"))

        video_url = self.video_page_url

        try:
            vid = YDStreamExtractor.getVideoInfo(video_url, quality=int(
                self.VIDEO))  # quality is 0=SD, 1=720p, 2=1080p and is a maximum
            video_url = vid.streamURL()
            have_valid_url = True
        except:
            # Maybe it's an 18+ video ?!
            #
            # Get HTML page...
            #
            response = requests.get(video_url, headers=HEADERS)

            html_source = response.text
            html_source = convertToUnicodeString(html_source)

            # Parse response
            soup = getSoup(html_source)

            # log("html_source", html_source)

            # A bit of a dirty hack, but let's try it anyway...
            # so.addVariable("file","http://hw-videos.worldstarhiphop.com/u/vid/2015/09/SAWGSqGpaohk.mp4");
            # or
            # <source src="http://hw-videos.worldstarhiphop.com/u/vid/2017/04/Gtlg3yKHNNqP.mp4" type="video/mp4">
            pos_vid_url = str(html_source).find("hw-videos.worldstarhiphop.com/")
            if pos_vid_url >= 0:
                pos_start_quote = str(html_source).rfind('"', 0, pos_vid_url)
                pos_end_quote = str(html_source).find('"', pos_start_quote + 1)
                video_url = html_source[pos_start_quote + 1: pos_end_quote]
                have_valid_url = True
            else:
                # Maybe it's a youtube video then ?!
                if str(html_source).find("www.youtube.com/embed") >= 0:
                    # Seems like it's an youtube video
                    # <iframe src="http://www.youtube.com/embed/1xcxn7pOYCg?autoplay=1" width="640" height="390" frameborder="0"></iframe>
                    # look for http youtube
                    video_urls = soup.findAll('iframe', attrs={'src': re.compile("^http://www.youtube.com/embed")}, limit=1)
                    if len(video_urls) == 0:
                        # look for https youtube
                        video_urls = soup.findAll('iframe', attrs={'src': re.compile("^https://www.youtube.com/embed")}, limit=1)
                        if len(video_urls) == 0:
                            unplayable_media_file = True
                        else:
                            video_url = video_urls[0]['src']

                            log("video_url", video_url)

                            # make youtube plugin url
                            pos_of_last_question_mark = video_url.rfind("?")
                            video_url = video_url[0: pos_of_last_question_mark]
                            video_url_len = len(video_url)
                            youtubeID = video_url[len("https://www.youtube.com/embed/"):video_url_len]
                            youtube_url = 'plugin://plugin.video.youtube/play/?video_id=%s' % youtubeID
                            have_valid_url = True
                            video_url = youtube_url
                    else:
                        video_url = video_urls[0]['src']

                        log("video_url", video_url)

                        # make youtube plugin url
                        pos_of_last_question_mark = video_url.rfind("?")
                        video_url = video_url[0: pos_of_last_question_mark]
                        video_url_len = len(video_url)
                        youtubeID = video_url[len("http://www.youtube.com/embed/"):video_url_len]
                        youtube_url = 'plugin://plugin.video.youtube/play/?video_id=%s' % youtubeID
                        have_valid_url = True
                        video_url = youtube_url
                else:
                    unplayable_media_file = True

        log("have_valid_url", have_valid_url)

        log("video_url", video_url)

        if have_valid_url:
            list_item = xbmcgui.ListItem(path=video_url)
            xbmcplugin.setResolvedUrl(self.plugin_handle, True, list_item)

        #
        # Alert user
        #
        elif unplayable_media_file:
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30506))