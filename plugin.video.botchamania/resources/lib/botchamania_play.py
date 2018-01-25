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
import urllib.request, urllib.parse, urllib.error
import requests
import sys
import xbmc
import xbmcgui
import xbmcplugin

from botchamania_const import LANGUAGE, SETTINGS, convertToUnicodeString, log, getSoup

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
        # Get the title.
        self.title = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['title'][0]
        self.title = str(self.title)

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
        no_url_found = False
        unplayable_media_file = False
        have_valid_url = False
        dialog_wait = xbmcgui.DialogProgress()

        #
        # Get current list item details...
        #
        # title = convertToUnicodeString(xbmc.getInfoLabel("list_item.Title"))
        thumbnail_url = convertToUnicodeString(xbmc.getInfoImage("list_item.Thumb"))
        # studio = convertToUnicodeString(xbmc.getInfoLabel("list_item.Studio"))
        plot = convertToUnicodeString(xbmc.getInfoLabel("list_item.Plot"))
        genre = convertToUnicodeString(xbmc.getInfoLabel("list_item.Genre"))

        stream_video_url = ''
        # We still need to find out the video-url
        if str(self.video_page_url).startswith("http://botchamania.com/") or str(self.video_page_url).startswith(
                "http://www.botchamaniaarchive.com/"):

            #
            # Get HTML page
            #
            try:
                response = requests.get(self.video_page_url)
            except urllib.error.HTTPError as error:

                log("first HTTPError", error)

                # Retry to (hopefully) get rid of a time-out http error
                try:
                    response = requests.get(self.video_page_url)
                except urllib.error.HTTPError as error:

                    log("second HTTPError", error)

                    dialog_wait.close()
                    del dialog_wait
                    xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30507) % (str(error)))
                    exit(1)

            html_source = response.text
            html_source = convertToUnicodeString(html_source)

            # Parse response
            soup = getSoup(html_source)

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

                    log("video_url1", video_url)

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

                    log("video_url2", video_url)

                    try:
                        vid = YDStreamExtractor.getVideoInfo(video_url, quality=2)
                        # vid = YDStreamExtractor.getVideoInfo(video_url, quality=int(
                        #     self.VIDEO))  # quality is 0=SD, 1=720p, 2=1080p and is a maximum
                        # found a working video! (champagne for everybody!), exit the loop
                        stream_video_url = vid.streamURL()
                        have_valid_url = True
                        break
                    except:
                        unplayable_media_file = True
        else:
            video_url = self.video_page_url

            log("video_url3", video_url)

            try:
                vid = YDStreamExtractor.getVideoInfo(video_url, quality=int(
                    self.VIDEO))  # quality is 0=SD, 1=720p, 2=1080p and is a maximum
                stream_video_url = vid.streamURL()
                have_valid_url = True
            except:
                unplayable_media_file = True

        log("have_valid_url", have_valid_url)

        log("video_url", video_url)

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