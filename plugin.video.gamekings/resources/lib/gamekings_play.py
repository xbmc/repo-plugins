#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
import base64
import re
import sys
import urllib2
import urlparse
import xbmc
import xbmcgui
import xbmcplugin
from BeautifulSoup import BeautifulSoup

from gamekings_const import ADDON, SETTINGS, LANGUAGE, DATE, VERSION
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
        self.video_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['video_page_url'][0]
        # Get the title.
        self.title = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['title'][0]
        self.title = str(self.title)

        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "self.video_page_url", str(self.video_page_url)), xbmc.LOGNOTICE)

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
        video_url = ""

        #
        # Get current list item details
        #
        # title = unicode(xbmc.getInfoLabel("listitem.Title"), "utf-8")
        thumbnail = xbmc.getInfoImage("list_item.Thumb")
        # studio = unicode(xbmc.getInfoLabel("list_item.Studio"), "utf-8")
        plot = unicode(xbmc.getInfoLabel("list_item.Plot"), "utf-8")
        genre = unicode(xbmc.getInfoLabel("list_item.Genre"), "utf-8")

        #
        # Show wait dialog while parsing data
        #
        dialog_wait = xbmcgui.DialogProgress()
        dialog_wait.create(LANGUAGE(30504), self.title)
        # wait 1 second
        xbmc.sleep(1000)

        http_communicator = HTTPCommunicator()

        html_data = ''
        try:
            html_data = http_communicator.get(self.video_page_url)
            html_data_str = str(html_data)
        except urllib2.HTTPError, error:
            if self.DEBUG == 'true':
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "HTTPError", str(error)), xbmc.LOGNOTICE)
            dialog_wait.close()
            del dialog_wait
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30507) % (str(error)))
            exit(1)

        # Get the video url
        # <div class="content  content--page  content--bglight  content--blue">
        #             <div class="video">
        #             <div id='videoplayer'></div>
        #             <script type="text/javascript">
        #                 jwplayer('videoplayer').setup({
        #                     file: 'https://player.vimeo.com/external/166503498.hd.mp4?s=c44264eced6082c0789371cb5209af96bc44035b',
        #                     image: 'http://www.gamekings.nl/wp-content/uploads/20160513_gk1702_splash.jpg',
        #                     title: 'Gamekings S17E02: De Synergie Aflevering',
        #                     width: '100%',
        #                     aspectratio: '16:9',
        #                     skin: '',
        #                     primary: 'html5',
        #                     autostart: 'true',
        #                     startparam: 'start',
        #                     ...
        no_url_found = False
        have_valid_url = True
        start_pos_video_url = html_data_str.find("http://player.vimeo.com")
        if start_pos_video_url == -1:
            start_pos_video_url = html_data_str.find("https://player.vimeo.com")
            if start_pos_video_url == -1:
                start_pos_video_url = html_data_str.find("http://www.youtube.com/")
                if start_pos_video_url == -1:
                    start_pos_video_url = html_data_str.find("https://www.youtube.com/")
                    if start_pos_video_url == -1:
                        no_url_found = True
                        have_valid_url = False

        # Make video url
        if have_valid_url:
            end_pos_video_url = html_data_str.find("'", start_pos_video_url)
            video_url = html_data_str[start_pos_video_url:end_pos_video_url]
            if video_url.find("http://www.youtube.com/channel/") >= 0:
                no_url_found = True
                have_valid_url = False
            else:
                if video_url.find("https://www.youtube.com/channel/") >= 0:
                    no_url_found = True
                    have_valid_url = False

            if self.DEBUG == 'true':
                xbmc.log(
                    "[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "video_url", str(video_url)),
                    xbmc.LOGNOTICE)

        # Play video
        if have_valid_url:
            if video_url.find("youtube") > 0:
                youtube_id = str(video_url)
                youtube_id = youtube_id.replace("http://www.youtube.com/embed/", "")
                youtube_id = youtube_id.replace("https://www.youtube.com/embed/", "")
                youtube_id = youtube_id.replace("http://www.youtube.com/watch?v=", "")
                youtube_id = youtube_id.replace("https://www.youtube.com/watch?v=", "")
                youtube_id = youtube_id.replace("http://www.youtube.com/", "")
                youtube_id = youtube_id.replace("https://www.youtube.com/", "")
                video_url = 'plugin://plugin.video.youtube/play/?video_id=%s' % youtube_id
            list_item = xbmcgui.ListItem(path=video_url)
            xbmcplugin.setResolvedUrl(self.plugin_handle, True, list_item)
        #
        # Alert user
        #
        elif no_url_found:
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30505))
