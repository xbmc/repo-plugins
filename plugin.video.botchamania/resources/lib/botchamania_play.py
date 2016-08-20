#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from BeautifulSoup import BeautifulSoup
from botchamania_const import ADDON, SETTINGS, LANGUAGE, IMAGES_PATH, DATE, VERSION
from botchamania_utils import HTTPCommunicator
import os
import re
import base64
import ast
import sys
import urllib, urllib2
import urlparse
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import YDStreamExtractor

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
        self.VIDEO = SETTINGS.getSetting('video')

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % (
                ADDON, VERSION, DATE, "ARGV", repr(sys.argv), "File", str(__file__)), xbmc.LOGDEBUG)

        # Parse parameters...
        self.video_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['video_page_url'][0]
        # Get the title.
        self.title = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['title'][0]
        self.title = str(self.title)

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "self.video_page_url", str(self.video_page_url)), xbmc.LOGDEBUG)

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
        no_url_found = False
        unplayable_media_file = False
        have_valid_url = False

        #
        # Get current list item details...
        #
        #title = unicode(xbmc.getInfoLabel("listitem.Title"), "utf-8")
        thumbnail_url = xbmc.getInfoImage("list_item.Thumb")
        #studio = unicode(xbmc.getInfoLabel("list_item.Studio"), "utf-8")
        plot = unicode(xbmc.getInfoLabel("list_item.Plot"), "utf-8")
        genre = unicode(xbmc.getInfoLabel("list_item.Genre"), "utf-8")

        #
        # Show wait dialog while parsing data...
        #
        dialog_wait = xbmcgui.DialogProgress()
        dialog_wait.create(LANGUAGE(30504), self.title)
        # wait 1 second
        xbmc.sleep(1000)

        stream_video_url = ''
        # We still need to find out the video-url
        if str(self.video_page_url).startswith("http://botchamania.com/") or str(self.video_page_url).startswith(
                "http://www.botchamaniaarchive.com/"):

            http_communicator = HTTPCommunicator()
            html_data = ''

            try:
                html_data = http_communicator.get(self.video_page_url)
            except urllib2.HTTPError, error:
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                        ADDON, VERSION, DATE, "first HTTPError", str(error)), xbmc.LOGDEBUG)
                # Retry to (hopefully) get rid of a time-out http error
                try:
                    html_data = http_communicator.get(self.video_page_url)
                except urllib2.HTTPError, error:
                    xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                            ADDON, VERSION, DATE, "second HTTPError", str(error)), xbmc.LOGDEBUG)
                    dialog_wait.close()
                    del dialog_wait
                    xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30507) % (str(error)))
                    exit(1)

            soup = BeautifulSoup(html_data)

            # Parse video file url
            video_urls = soup.findAll('iframe')

            video_urls_index = 0
            video_url = ''
            stream_video_url = ''
            for video_url in video_urls:
                no_url_found = False
                unplayable_media_file = False
                have_valid_url = False

                if len(video_urls) == 0:
                    no_url_found = True
                elif len(video_urls) == 1:
                    video_url = video_urls[video_urls_index]['src']
                    # eventually fix video-url
                    video_url = str(video_url)
                    if video_url.startswith("http"):
                        pass
                    elif video_url.startswith("//"):
                        video_url = "http:" + video_url
                    elif video_url.startswith("/"):
                        video_url = "http:/" + video_url
                    else:
                        video_url = "http://" + video_url

                    xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                            ADDON, VERSION, DATE, "video_url", str(video_url)), xbmc.LOGDEBUG)
                    try:
                        vid = YDStreamExtractor.getVideoInfo(video_url, quality=int(
                            self.VIDEO))  # quality is 0=SD, 1=720p, 2=1080p and is a maximum
                        # found a working video! (champagne for everybody!), exit the loop
                        stream_video_url = vid.streamURL()
                        have_valid_url = True
                        break
                    except:
                        unplayable_media_file = True
                else:
                    # Let the user choose a video
                    video_nr = 0
                    video_urls_list = []
                    video_urls_title_list = []
                    for vid in video_urls:
                        video_nr += 1
                        video_urls_list.append(vid)
                        video_urls_title_list.append(LANGUAGE(30509) + str(video_nr))

                    result = xbmcgui.Dialog().select(LANGUAGE(30508), video_urls_title_list)
                    if result == -1:
                        # Let's choose the second video
                        video_urls_index = video_urls_index + 1
                        video_url = video_urls[video_urls_index]['src']
                    else:
                        video_url = video_urls_list[result]['src']

                    # eventually fix video-url
                    video_url = str(video_url)
                    if video_url.startswith("http"):
                        pass
                    elif video_url.startswith("//"):
                        video_url = "http:" + video_url
                    elif video_url.startswith("/"):
                        video_url = "http:/" + video_url
                    else:
                        video_url = "http://" + video_url

                    xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                            ADDON, VERSION, DATE, "video_url", str(video_url)), xbmc.LOGDEBUG)
                    try:
                        vid = YDStreamExtractor.getVideoInfo(video_url, quality=int(
                            self.VIDEO))  # quality is 0=SD, 1=720p, 2=1080p and is a maximum
                        # found a working video! (champagne for everybody!), exit the loop
                        stream_video_url = vid.streamURL()
                        have_valid_url = True
                        break
                    except:
                        unplayable_media_file = True
        else:
            video_url = self.video_page_url
            try:
                vid = YDStreamExtractor.getVideoInfo(video_url, quality=int(
                    self.VIDEO))  # quality is 0=SD, 1=720p, 2=1080p and is a maximum
                stream_video_url = vid.streamURL()
                have_valid_url = True
            except:
                unplayable_media_file = True

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "have_valid_url", str(have_valid_url)), xbmc.LOGDEBUG)
        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "video_url", str(video_url)), xbmc.LOGDEBUG)

        if have_valid_url:
            video_url = stream_video_url
            list_item = xbmcgui.ListItem(path=video_url)
            xbmcplugin.setResolvedUrl(self.plugin_handle, True, list_item)

        #
        # Alert user
        #
        elif no_url_found:
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30505))
        elif unplayable_media_file:
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30506))
