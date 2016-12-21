#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
import ast
import base64
import re
import requests
import sys
import urllib2
import urlparse
import xbmc
import xbmcgui
import xbmcplugin
from BeautifulSoup import BeautifulSoup

from dumpert_const import ADDON, SETTINGS, LANGUAGE, DATE, VERSION


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
        # title = unicode(xbmc.getInfoLabel("listitem.Title"), "utf-8")
        thumbnail_url = xbmc.getInfoImage("list_item.Thumb")
        # studio = unicode(xbmc.getInfoLabel("list_item.Studio"), "utf-8")
        plot = unicode(xbmc.getInfoLabel("list_item.Plot"), "utf-8")
        genre = unicode(xbmc.getInfoLabel("list_item.Genre"), "utf-8")

        #
        # Show wait dialog while parsing data...
        #
        dialog_wait = xbmcgui.DialogProgress()
        dialog_wait.create(LANGUAGE(30504), self.title)
        # wait 1 second
        xbmc.sleep(1000)

        html_source = ''
        try:
            if SETTINGS.getSetting('nsfw') == 'true':
                response = requests.get(self.video_page_url, cookies={'nsfw': '1'})
            else:
                response = requests.get(self.video_page_url)

            html_source = response.text
        except urllib2.HTTPError, error:
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "HTTPError", str(error)), xbmc.LOGDEBUG)
            dialog_wait.close()
            del dialog_wait
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30507) % (str(error)))
            exit(1)

        soup = BeautifulSoup(html_source)

        video_url = ''
        # <div class="videoplayer" id="video1" data-files="eyJmbHYiOiJodHRwOlwvXC9tZWRpYS5kdW1wZXJ0Lm5sXC9mbHZcLzI4OTE2NWRhXzEwMjU1NzUyXzYzODMxODA4OTU1NDc2MV84MTk0MzU3MDVfbi5tcDQuZmx2IiwidGFibGV0IjoiaHR0cDpcL1wvbWVkaWEuZHVtcGVydC5ubFwvdGFibGV0XC8yODkxNjVkYV8xMDI1NTc1Ml82MzgzMTgwODk1NTQ3NjFfODE5NDM1NzA1X24ubXA0Lm1wNCIsIm1vYmlsZSI6Imh0dHA6XC9cL21lZGlhLmR1bXBlcnQubmxcL21vYmlsZVwvMjg5MTY1ZGFfMTAyNTU3NTJfNjM4MzE4MDg5NTU0NzYxXzgxOTQzNTcwNV9uLm1wNC5tcDQiLCJzdGlsbCI6Imh0dHA6XC9cL3N0YXRpYy5kdW1wZXJ0Lm5sXC9zdGlsbHNcLzY1OTM1MjRfMjg5MTY1ZGEuanBnIn0="></div></div>
        video_urls = soup.findAll('div', attrs={'class': re.compile("video")}, limit=1)
        if len(video_urls) == 0:
            no_url_found = True
        else:
            video_url_enc = video_urls[0]['data-files']
            # base64 decode
            video_url_dec = str(base64.b64decode(video_url_enc))
            # {"flv":"http:\/\/media.dumpert.nl\/flv\/5770e490_Jumbo_KOOP_DAN__Remix.avi.flv","tablet":"http:\/\/media.dumpert.nl\/tablet\/5770e490_Jumbo_KOOP_DAN__Remix.avi.mp4","mobile":"http:\/\/media.dumpert.nl\/mobile\/5770e490_Jumbo_KOOP_DAN__Remix.avi.mp4","720p":"http:\/\/media.dumpert.nl\/720p\/5770e490_Jumbo_KOOP_DAN__Remix.avi.mp4","still":"http:\/\/static.dumpert.nl\/stills\/6593503_5770e490.jpg"}
            # or
            # {"embed":"youtube:U89fl5fZETE","still":"http:\/\/static.dumpert.nl\/stills\/6650228_24eed546.jpg"}

            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                    ADDON, VERSION, DATE, "video_url_dec", str(video_url_dec)), xbmc.LOGDEBUG)

            # convert string to dictionary
            video_url_dec_dict = ast.literal_eval(video_url_dec)

            video_url_embed = ''
            try:
                video_url_embed = str(video_url_dec_dict['embed'])
                embed_found = True
            except KeyError:
                embed_found = False

            video_url = ''
            if embed_found:
                # make youtube plugin url
                youtube_id = video_url_embed.replace("youtube:", "")
                youtube_url = 'plugin://plugin.video.youtube/play/?video_id=%s' % youtube_id
                video_url = youtube_url
                have_valid_url = True
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                        ADDON, VERSION, DATE, "video_url1", str(video_url)), xbmc.LOGDEBUG)
            else:
                # matching the desired and available quality
                if self.VIDEO == '0':
                    try:
                        video_url = str(video_url_dec_dict['mobile'])
                    except KeyError:
                        no_url_found = True
                elif self.VIDEO == '1':
                    try:
                        video_url = str(video_url_dec_dict['tablet'])
                    except KeyError:
                        try:
                            video_url = str(video_url_dec_dict['mobile'])
                        except KeyError:
                            no_url_found = True
                elif self.VIDEO == '2':
                    try:
                        video_url = str(video_url_dec_dict['720p'])
                    except KeyError:
                        try:
                            video_url = str(video_url_dec_dict['tablet'])
                        except KeyError:
                            try:
                                video_url = str(video_url_dec_dict['mobile'])
                            except KeyError:
                                no_url_found = True

                if no_url_found:
                    pass
                else:
                    video_url = video_url.replace('\/', '/')
                    xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                            ADDON, VERSION, DATE, "video_url2", str(video_url)), xbmc.LOGDEBUG)

                    # The need for speed: let's guess that the video-url exists
                    have_valid_url = True

        # Play video...
        if have_valid_url:
            list_item = xbmcgui.ListItem(path=video_url)
            xbmcplugin.setResolvedUrl(self.plugin_handle, True, list_item)
        #
        # Alert user
        #
        elif no_url_found:
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30505))
        elif unplayable_media_file:
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30506))
