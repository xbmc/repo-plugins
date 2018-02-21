#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import object
import ast
import base64
import re
import requests
import sys
import urllib.request, urllib.error, urllib.parse
import xbmc
import xbmcgui
import xbmcplugin

from dumpert_const import LANGUAGE, SETTINGS, convertToUnicodeString, log, getSoup


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
        # Try and get the title.
        # When starting a video with a browser (f.e. in chrome the 'send to kodi'-extension) the url will be
        # something like this:
        # plugin://plugin.video.dumpert/?action=play&video_page_url=http%3A%2F%2Fwww.dumpert.nl%2Fmediabase%2F7095997%2F1f72985c%2Fmevrouw_heeft_internetje_thuis.html
        # and there won't be a title available.
        try:
            self.title = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['title'][0]
            self.title = str(self.title)
        except KeyError:
            self.title = ""

        log("self.video_page_url",self.video_page_url)

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
        # title = convertToUnicodeString(xbmc.getInfoLabel("list_item.Title"))
        thumbnail_url = convertToUnicodeString(xbmc.getInfoImage("list_item.Thumb"))
        # studio = convertToUnicodeString(xbmc.getInfoLabel("list_item.Studio"))
        # plot = convertToUnicodeString(xbmc.getInfoLabel("list_item.Plot"))
        # genre = convertToUnicodeString(xbmc.getInfoLabel("list_item.Genre"))

        #
        # Show wait dialog while parsing data...
        #
        dialog_wait = xbmcgui.DialogProgress()
        dialog_wait.create(LANGUAGE(30504), self.title)
        # wait 1 second
        xbmc.sleep(1000)

        try:
            if SETTINGS.getSetting('nsfw') == 'true':
                response = requests.get(self.video_page_url, cookies={'nsfw': '1'})
            else:
                response = requests.get(self.video_page_url)

            html_source = response.text
            html_source = convertToUnicodeString(html_source)
        except urllib.error.HTTPError as error:

            log('HTTPError', error)

            dialog_wait.close()
            del dialog_wait
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30507) % (str(error)))
            exit(1)

        # Parse response
        soup = getSoup(html_source)

        video_url = ''
        # <div class="videoplayer" id="video1" data-files="eyJmbHYiOiJodHRwOlwvXC9tZWRpYS5kdW1wZXJ0Lm5sXC9mbHZcLzI4OTE2NWRhXzEwMjU1NzUyXzYzODMxODA4OTU1NDc2MV84MTk0MzU3MDVfbi5tcDQuZmx2IiwidGFibGV0IjoiaHR0cDpcL1wvbWVkaWEuZHVtcGVydC5ubFwvdGFibGV0XC8yODkxNjVkYV8xMDI1NTc1Ml82MzgzMTgwODk1NTQ3NjFfODE5NDM1NzA1X24ubXA0Lm1wNCIsIm1vYmlsZSI6Imh0dHA6XC9cL21lZGlhLmR1bXBlcnQubmxcL21vYmlsZVwvMjg5MTY1ZGFfMTAyNTU3NTJfNjM4MzE4MDg5NTU0NzYxXzgxOTQzNTcwNV9uLm1wNC5tcDQiLCJzdGlsbCI6Imh0dHA6XC9cL3N0YXRpYy5kdW1wZXJ0Lm5sXC9zdGlsbHNcLzY1OTM1MjRfMjg5MTY1ZGEuanBnIn0="></div></div>
        video_urls = soup.findAll('div', attrs={'class': re.compile("video")}, limit=1)
        if len(video_urls) == 0:
            # maybe it's a youtube url
            # <iframe class='yt-iframe' style='width: 100%' src='https://www.youtube.com/embed/9L0iOZmdS6s?showInfo=0&rel=0' frameborder='0' allow='autoplay; encrypted-media' allowfullscreen></iframe>
            video_urls = soup.findAll('iframe', attrs={'src': re.compile("^http")}, limit=1)
            if len(video_urls) == 0:
                no_url_found = True
            else:
                url = video_urls[0]['src']
                start_pos_youtube_id = str(url).rfind("/") + len("/")
                end_pos_youtube_id = str(url).find("?", start_pos_youtube_id)
                youtube_id = url[start_pos_youtube_id:end_pos_youtube_id]
                youtube_url = 'plugin://plugin.video.youtube/play/?video_id=%s' % youtube_id
                video_url = youtube_url
                have_valid_url = True

                log("video_url1", video_url)

        else:
            video_url_enc = video_urls[0]['data-files']
            # base64 decode
            video_url_dec = convertToUnicodeString(base64.b64decode(video_url_enc))
            # {"flv":"http:\/\/media.dumpert.nl\/flv\/5770e490_Jumbo_KOOP_DAN__Remix.avi.flv","tablet":"http:\/\/media.dumpert.nl\/tablet\/5770e490_Jumbo_KOOP_DAN__Remix.avi.mp4","mobile":"http:\/\/media.dumpert.nl\/mobile\/5770e490_Jumbo_KOOP_DAN__Remix.avi.mp4","720p":"http:\/\/media.dumpert.nl\/720p\/5770e490_Jumbo_KOOP_DAN__Remix.avi.mp4","still":"http:\/\/static.dumpert.nl\/stills\/6593503_5770e490.jpg"}
            # or
            # {"embed":"youtube:U89fl5fZETE","still":"http:\/\/static.dumpert.nl\/stills\/6650228_24eed546.jpg"}

            log("video_url_dec", video_url_dec)

            # convert string to dictionary
            video_url_dec_dict = ast.literal_eval(video_url_dec)

            try:
                video_url_embed = convertToUnicodeString(video_url_dec_dict['embed'])
                embed_found = True
            except KeyError:
                embed_found = False

            if embed_found:
                # make youtube plugin url
                youtube_id = video_url_embed.replace("youtube:", "")
                youtube_url = 'plugin://plugin.video.youtube/play/?video_id=%s' % youtube_id
                video_url = youtube_url
                have_valid_url = True

                log("video_url2", video_url)

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

                    log("video_url3", video_url)

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