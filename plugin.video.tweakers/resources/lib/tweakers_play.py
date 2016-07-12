#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
import sys
import requests
import urllib2
import urlparse
import re
import json
import xbmc
import xbmcgui
import xbmcplugin
from BeautifulSoup import BeautifulSoup

from tweakers_const import ADDON, SETTINGS, LANGUAGE, DATE, VERSION



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
        # Get the video_page_url.
        self.video_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['video_page_url'][0]
        self.video_page_url = str(self.video_page_url)
        # Get the title.
        self.title = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['title'][0]
        self.title = str(self.title)

        # Get plugin settings
        self.MAXIMUM_VIDEO_QUALITY = SETTINGS.getSetting('maximum-video-quality')

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % (
                ADDON, VERSION, DATE, "ARGV", repr(sys.argv), "File", str(__file__)), xbmc.LOGDEBUG)

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
        dialog_wait.create(LANGUAGE(30504), self.title)
        # Wait 1 second
        xbmc.sleep(1000)

        # Video_page_url will be something like this: https://tweakers.net/video/7893/world-of-tanks-86-aankondiging.html
        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "self.video_page_url", str(self.video_page_url)), xbmc.LOGDEBUG)


        # Make the headers
        xbmc_version = xbmc.getInfoLabel("System.BuildVersion")
        user_agent = "Kodi Mediaplayer %s / Tweakers Addon %s" % (xbmc_version, VERSION)
        headers = {"User-Agent": user_agent,
                   "Accept-Encoding": "gzip",
                   "X-Cookies-Accepted": "1"}
        # Disable ssl logging (this is needed for python version < 2.7.9 (SNIMissingWarning))
        import logging
        logging.captureWarnings(True)

        html_source = ''
        try:
            response = requests.get(self.video_page_url, headers=headers)
            html_source = response.text
            html_source = html_source.encode('utf-8', 'ignore')
        except urllib2.HTTPError, error:
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "HTTPError", str(error)),
                         xbmc.LOGDEBUG)
            dialog_wait.close()
            del dialog_wait
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30507) % (str(error)))
            exit(1)

        soup = BeautifulSoup(html_source)

        # Find the real video page url
        #<div class="video-container">
        # <iframe name="s1_soc_1" id="s1_soc_1" style="border:0" frameborder="0" width="620" height="349" src="https://tweakers.net/video/player/12875/pre-alpha-gameplay-van-system-shock-remake.html?expandByResize=1&amp;width=620&amp;height=349&amp;zone=30" allowfullscreen="allowfullscreen" mozallowfullscreen="mozallowfullscreen" webkitallowfullscreen="webkitallowfullscreen"></iframe></div>
        iframes = soup.findAll('iframe', attrs={'src': re.compile("^https://tweakers.net/video")}, limit=1)
        real_video_page_url = iframes[0]['src']

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "real_video_page_url", str(real_video_page_url)),
                     xbmc.LOGDEBUG)

        html_source = ''
        try:
            response = requests.get(real_video_page_url, headers=headers)
            html_source = response.text
            html_source = html_source.encode('utf-8', 'ignore')
        except urllib2.HTTPError, error:
            xbmc.log(
                    "[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "HTTPError", str(error)),
                    xbmc.LOGDEBUG)
            dialog_wait.close()
            del dialog_wait
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30507) % (str(error)))
            exit(1)

        soup = BeautifulSoup(html_source)

        # Find the video url in the json block
        # .....})('video', {"skin": "https:\/\/tweakimg.net\/x\/video\/skin\/default\/streamone.css?1459246513", "playlist": {
        #        "items": [{"id": "gY8Cje0JOwmQ", "title": "Hyperloop One voert eerste test succesvol uit",
        #        "description": "Hyperloop One heeft in de woestijn in Nevada de eerste succesvolle test van het aandrijfsysteem uitgevoerd. De Hyperloop-slede kwam tijdens de test op de rails binnen 1,1 seconde tot een snelheid van 187km\/u.",
        #        "poster": "https:\/\/ic.tweakimg.net\/img\/account=s7JeEm\/item=gY8Cje0JOwmQ\/size=980x551\/image.jpg",
        #        "duration": 62, "locations": {"progressive": [{"label": "1080p", "height": 1080, "width": 1920,
        #                                                       "sources": [{"type": "video\/mp4",
        #                                                                    "src": "https:\/\/media.tweakers.tv\/progressive\/account=s7JeEm\/item=gY8Cje0JOwmQ\/file=nhsKnukbVci0\/account=s7JeEm\/gY8Cje0JOwmQ.mp4"}]},
        #                                                      {"label": "720p", "height": 720, "width": 1280,
        #                                                       "sources": [{"type": "video\/mp4",
        #                                                                    "src": "https:\/\/media.tweakers.tv\/progressive\/account=s7JeEm\/item=gY8Cje0JOwmQ\/file=jC0LmugZVMCU\/account=s7JeEm\/gY8Cje0JOwmQ.mp4"}]},
        #                                                      {"label": "360p", "height": 360, "width": 640,
        #                                                       "sources": [{"type": "video\/mp4",
        #                                                                    "src": "https:\/\/media.tweakers.tv\/progressive\/account=s7JeEm\/item=gY8Cje0JOwmQ\/file=lwkDiMAZOVO0\/account=s7JeEm\/gY8Cje0JOwmQ.mp4"}]},
        #                                                      {"label": "270p", "height": 270, "width": 480,
        #                                                       "sources": [{"type": "video\/mp4",
        #                                                                    "src": "http:s\/\/media.tweakers.tv\/progressive\/account=s7JeEm\/item=gY8Cje0JOwmQ\/file=BT1DiI2bOFuU\/account=s7JeEm\/gY8Cje0JOwmQ.mp4"}]}],
        #                                      "adaptive": []}, "audioonly": false, "live": false, ...

        # Find the json block containing all the video-urls
        soup_str = str(soup)
        start_pos_json_block = soup_str.find('[{"label"')
        end_pos_json_block = soup_str.find("}]}]")
        end_pos_json_block += len("}]}]")
        json_string = soup_str[start_pos_json_block:end_pos_json_block]
        parsed_json = json.loads(json_string)

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "json_string", json_string),
                 xbmc.LOGDEBUG)
        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "json_string", json_string),
                 xbmc.LOGDEBUG)

        # Determine what quality the video should be
        if self.MAXIMUM_VIDEO_QUALITY == "0":
            maximum_video_label = "270p"
        elif self.MAXIMUM_VIDEO_QUALITY == "1":
            maximum_video_label = "360p"
        elif self.MAXIMUM_VIDEO_QUALITY == "2":
            maximum_video_label = "720p"
        elif self.MAXIMUM_VIDEO_QUALITY == "3":
            maximum_video_label = "1080p"
        else:
            maximum_video_label = "1080p"

        # Find the source with the maximum video quality
        sources_index = 0
        label_found = False
        while label_found == False:
            try:
                if parsed_json[sources_index]["label"] == maximum_video_label:
                    label_found = True
                else:
                    sources_index += 1
            except:
                sources_index = 0
                break

        # Find the json block containing the video-url with the maximum video quality
        try:
            json_string = str(parsed_json[sources_index]["sources"])
        except:
            # If the maximum quality is not available, use the best available quality
            json_string = str(parsed_json[0]["sources"])
        json_string = json_string.strip("[")
        json_string = json_string.strip("]")
        json_string = json_string.replace("u'", "'")
        json_string = json_string.replace("'", '"')
        parsed_json = json.loads(json_string)
        video_url = str(parsed_json["src"])

        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, "video_url", str(video_url)), xbmc.LOGDEBUG)

        no_url_found = False
        have_valid_url = False

        if len(video_url) == 0:
            no_url_found = True
        else:
            have_valid_url = True

        # Play video
        if have_valid_url:
            list_item = xbmcgui.ListItem(path=video_url)
            xbmcplugin.setResolvedUrl(self.plugin_handle, True, listitem=list_item)
        #
        # Alert user
        #
        elif no_url_found:
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30505))
