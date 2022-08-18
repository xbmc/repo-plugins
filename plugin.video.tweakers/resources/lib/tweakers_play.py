#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import object
import sys
import requests
import urllib.request, urllib.error, urllib.parse
import xbmc
import xbmcgui
import xbmcplugin

from resources.lib.tweakers_const import SETTINGS, LANGUAGE, VERSION, YOUTUBE_ID_STRING_TO_FIND, convertToUnicodeString, log



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
        # Get the video_page_url.
        self.video_page_url = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['video_page_url'][0]
        self.video_page_url = str(self.video_page_url)
        # Get the title.
        self.title = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['title'][0]
        self.title = str(self.title)

        # Get plugin settings
        self.MAXIMUM_VIDEO_QUALITY = SETTINGS.getSetting('maximum-video-quality')

        log("ARGV", repr(sys.argv))

        #
        # Play video
        #
        self.playVideo()

    #
    # Play video
    #
    def playVideo(self):
        #
        # Show wait dialog while parsing data
        #
        dialog_wait = xbmcgui.DialogProgress()

        # Video_page_url will be something like this: https://tweakers.net/video/7893/world-of-tanks-86-aankondiging.html
        log("self.video_page_url", self.video_page_url)

        # Make the headers
        xbmc_version = xbmc.getInfoLabel("System.BuildVersion")
        user_agent = "Kodi Mediaplayer %s / Tweakers Addon %s" % (xbmc_version, VERSION)
        headers = {"User-Agent": user_agent,
                   "Accept-Encoding": "gzip",
                   "X-Cookies-Accepted": "1"}

        # Disable ssl logging (this is needed for python version < 2.7.9 (SNIMissingWarning))
        import logging
        # On iOS the following logging command throws an exception. If that happens, ignore the exception...
        try:
            logging.captureWarnings(True)
        except Exception:

            log("logging exception occured (and ignored)", Exception)

            pass

        try:
            response = requests.get(self.video_page_url, headers=headers)
            html_source = response.text
            html_source = convertToUnicodeString(html_source)
        except urllib.error.HTTPError as error:

            log("HTTPError", error)

            dialog_wait.close()
            del dialog_wait
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30507) % (str(error)))
            exit(1)

        #log("html_source", html_source)

        # let's find the youtube-id
        # <script>
        #     YouTubePlayer.init('tnet_video_1', {"videoId":17009,"videoTitle":"Techjuwelen - Asus Eee PC - Iedereen aan de netbook","youtubeId":"o48_m3x-qwQ","width":980,"height":551,"playerVars":[],"webTrekkOptions":{"trackId":"318816705845986","trackDomain":"cijfers.tweakers.nl","posInterval":30}});
        # </script>

        youtube_id_found = False
        start_pos_youtube_id = html_source.find(YOUTUBE_ID_STRING_TO_FIND)
        if start_pos_youtube_id >= 0:
            youtube_id_found = True

            start_pos_youtube_id = start_pos_youtube_id + len(YOUTUBE_ID_STRING_TO_FIND)
            end_pos_youtube_id = html_source.find('"', start_pos_youtube_id)
            youtube_id = html_source[start_pos_youtube_id:end_pos_youtube_id]

            log("youtube_id", youtube_id)

            youtube_url = 'plugin://plugin.video.youtube/play/?video_id=%s' % youtube_id

            log("youtube_url", youtube_url)

        if youtube_id_found:
            # Play video
            video_url = youtube_url
            list_item = xbmcgui.ListItem(path=video_url)
            xbmcplugin.setResolvedUrl(self.plugin_handle, True, list_item)

            # Alert user
        else:
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30505))