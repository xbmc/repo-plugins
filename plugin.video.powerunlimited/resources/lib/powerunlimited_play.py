#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from BeautifulSoup import BeautifulSoup
from powerunlimited_const import ADDON, SETTINGS, LANGUAGE, IMAGES_PATH, DATE, VERSION
from powerunlimited_utils import HTTPCommunicator
import os
import re
import sys
import urllib
import urlparse
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin


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
        self.video_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['video_page_url'][0]
        # Get the title.
        self.title = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['title'][0]
        self.title = str(self.title)

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "self.video_page_url", str(self.video_page_url)), xbmc.LOGDEBUG)

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

        #
        # Get current list item details
        #
        #title = unicode(xbmc.getInfoLabel("listitem.Title"), "utf-8")
        thumbnail = xbmc.getInfoImage("list_item.Thumb")
        #studio = unicode(xbmc.getInfoLabel("list_item.Studio"), "utf-8")
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
        except urllib2.HTTPError, error:
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "HTTPError", str(error)), xbmc.LOGDEBUG)
            dialog_wait.close()
            del dialog_wait
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30507) % (str(error)))
            exit(1)

        soup = BeautifulSoup(html_data)

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
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                        ADDON, VERSION, DATE, "video_url", str(video_url)), xbmc.LOGDEBUG)
                if http_communicator.exists(video_url):
                    have_valid_url = True
                    # make youtube plugin url
                    pos_of_last_question_mark = video_url.rfind("?")
                    if pos_of_last_question_mark >= 0:
                        video_url = video_url[0: pos_of_last_question_mark]
                    video_url_len = len(video_url)
                    youtubeID = video_url[len("https://www.youtube.com/embed/"):video_url_len]
                    youtube_url = 'plugin://plugin.video.youtube/play/?video_id=%s' % youtubeID
                else:
                    unplayable_media_file = True

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "no_url_found", str(have_valid_url)), xbmc.LOGDEBUG)
        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "unplayable_media_file", str(have_valid_url)), xbmc.LOGDEBUG)
        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "have_valid_url", str(have_valid_url)), xbmc.LOGDEBUG)
        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "youtube_url", str(youtube_url)), xbmc.LOGDEBUG)

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
