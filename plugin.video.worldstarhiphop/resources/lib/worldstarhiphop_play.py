#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
# the YDStreamExtractor needs to be before the future imports. Otherwise u get an 'check hostname' error.
import YDStreamExtractor
from future import standard_library
standard_library.install_aliases()
from builtins import object

import sys
import urllib.parse
import xbmc
import xbmcgui
import xbmcplugin

from resources.lib.worldstarhiphop_const import SETTINGS, LANGUAGE, log
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
        # Create a list for our items.
        unplayable_media_file = False
        have_valid_url = False

        video_url = self.video_page_url

        log("video_url", video_url)

        try:
            # 2 possible video kinds
            #   video hosted on worldstarhiphop server:
            #   https://worldstar.com/videos/wshhUe2VMr4X59943tcB/bruh-went-crazy-south-korean-man-oh-yohan-broke-the-guinness-world-record-for-most-pull-ups-in-24-hours-with-11-707-reps
            #   video hosted on youtube server:
            #   https://worldstar.com/videos/wshh713c6jtnO4GYA8jg/jim-jones-life-with-you-feat-shyst-vader-and-beaujoli

            vid = YDStreamExtractor.getVideoInfo(video_url, quality=int(
                self.VIDEO))  # quality is 0=SD, 1=720p, 2=1080p and is a maximum
            stream_url = vid.streamURL()

            log("stream_url", stream_url)

            # the 2 possible video kinds result in these stream urls
            #   video hosted on worldstarhiphop server:
            #   https://hw-videos.worldstarhiphop.com/u/vid/2025/06/LDnY4eI5gMB3.mp4|User-Agent=Mozilla%2F5.0+%28Windows+NT+10.0%3B+Win64%3B+x64%29+AppleWebKit%2F537.36+%28KHTML%2C+like+Gecko%29+Chrome%2F75.0.3739.1+Safari%2F537.36
            #   video hosted on youtube server:
            #   https://www.youtube.com/v/f-lwAZ77vSo|User-Agent=Mozilla%2F5.0+%28Windows+NT+10.0%3B+Win64%3B+x64%29+AppleWebKit%2F537.36+%28KHTML%2C+like+Gecko%29+Chrome%2F71.0.3559.2+Safari%2F537.36

            #   For a youtube video: use kodi youtube plugin to play it
            if "youtube" in stream_url.lower():
                # Extract the URL part before the pipe
                url_part = stream_url.split("|User-Agent=")[0]
                # Find the last '/' and extract the ID after it
                youtube_id = url_part.split('/')[-1]

                log("youtube_id:", youtube_id)

                youtube_url = 'plugin://plugin.video.youtube/play/?video_id=%s' % youtube_id
                have_valid_url = True
                video_url = youtube_url
            else:
                # for a video hosted on worldstarhiphop server: play the video file directly
                have_valid_url = True
                video_url = stream_url
        except:
            unplayable_media_file = True

        log("have_valid_url", have_valid_url)
        log("unplayable_media_file", unplayable_media_file)
        log("video_url", video_url)

        if have_valid_url:
            list_item = xbmcgui.ListItem(path=video_url)
            xbmcplugin.setResolvedUrl(self.plugin_handle, True, list_item)
        #
        # Alert user
        #
        elif unplayable_media_file:
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30506))