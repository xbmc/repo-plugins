#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
import sys
import urllib2
import urlparse
import re
import json
import xbmc
import xbmcgui
import xbmcplugin
from BeautifulSoup import BeautifulSoup

from tweakers_const import ADDON, SETTINGS, LANGUAGE, DATE, VERSION
from tweakers_utils import HTTPCommunicator


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
        self.DEBUG = SETTINGS.getSetting('debug')
        self.PREFERRED_VIDEO_QUALITY = SETTINGS.getSetting('preferred-video-quality')

        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % (
                ADDON, VERSION, DATE, "ARGV", repr(sys.argv), "File", str(__file__)), xbmc.LOGNOTICE)

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

        # Video_page_url will be something like this: http://tweakers.net/video/7893/world-of-tanks-86-aankondiging.html
        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "self.video_page_url", str(self.video_page_url)), xbmc.LOGNOTICE)

        html_source = ''
        try:
            html_source = HTTPCommunicator().get(self.video_page_url)
        except urllib2.HTTPError, error:
            if self.DEBUG == 'true':
                xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "HTTPError", str(error)),
                         xbmc.LOGNOTICE)
            dialog_wait.close()
            del dialog_wait
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30507) % (str(error)))
            exit(1)

        soup = BeautifulSoup(html_source)

        # Find the real video page url
        # < iframe name = "s1_soc_1" id = "s1_soc_1" style = "border:0" frameborder = 0 width = 620 height = 349
        # src = "//tweakers.net/video/player/12193/pitch-2e-inspiratiesessie-carefree.html?expandByResize=1&amp;width=620&amp;height=349&amp;zone=30"
        # allowfullscreen mozallowfullscreen webkitallowfullscreen > < / iframe >
        iframes = soup.findAll('iframe', attrs={'src': re.compile("^//tweakers.net/video")}, limit=1)
        real_video_page_url = iframes[0]['src']
        real_video_page_url = "http:" + real_video_page_url

        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "real_video_page_url", str(real_video_page_url)),
                     xbmc.LOGNOTICE)

        html_source = ''
        try:
            html_source = HTTPCommunicator().get(real_video_page_url)
        except urllib2.HTTPError, error:
            if self.DEBUG == 'true':
                xbmc.log(
                    "[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "HTTPError", str(error)),
                    xbmc.LOGNOTICE)
            dialog_wait.close()
            del dialog_wait
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30507) % (str(error)))
            exit(1)

        soup = BeautifulSoup(html_source)

        # Find the video url in the json block
        # .....})('video', {"skin": "https:\/\/tweakimg.net\/x\/video\/skin\/default\/streamone.css?1459246513", "playlist": {
        #        "items": [{"id": "gY8Cje0JOwmQ", "title": "Hyperloop One voert eerste test succesvol uit",
        #        "description": "Hyperloop One heeft in de woestijn in Nevada de eerste succesvolle test van het aandrijfsysteem uitgevoerd. De Hyperloop-slede kwam tijdens de test op de rails binnen 1,1 seconde tot een snelheid van 187km\/u.",
        #        "poster": "http:\/\/ic.tweakimg.net\/img\/account=s7JeEm\/item=gY8Cje0JOwmQ\/size=980x551\/image.jpg",
        #        "duration": 62, "locations": {"progressive": [{"label": "1080p", "height": 1080, "width": 1920,
        #                                                       "sources": [{"type": "video\/mp4",
        #                                                                    "src": "http:\/\/media.tweakers.tv\/progressive\/account=s7JeEm\/item=gY8Cje0JOwmQ\/file=nhsKnukbVci0\/account=s7JeEm\/gY8Cje0JOwmQ.mp4"}]},
        #                                                      {"label": "720p", "height": 720, "width": 1280,
        #                                                       "sources": [{"type": "video\/mp4",
        #                                                                    "src": "http:\/\/media.tweakers.tv\/progressive\/account=s7JeEm\/item=gY8Cje0JOwmQ\/file=jC0LmugZVMCU\/account=s7JeEm\/gY8Cje0JOwmQ.mp4"}]},
        #                                                      {"label": "360p", "height": 360, "width": 640,
        #                                                       "sources": [{"type": "video\/mp4",
        #                                                                    "src": "http:\/\/media.tweakers.tv\/progressive\/account=s7JeEm\/item=gY8Cje0JOwmQ\/file=lwkDiMAZOVO0\/account=s7JeEm\/gY8Cje0JOwmQ.mp4"}]},
        #                                                      {"label": "270p", "height": 270, "width": 480,
        #                                                       "sources": [{"type": "video\/mp4",
        #                                                                    "src": "http:\/\/media.tweakers.tv\/progressive\/account=s7JeEm\/item=gY8Cje0JOwmQ\/file=BT1DiI2bOFuU\/account=s7JeEm\/gY8Cje0JOwmQ.mp4"}]}],
        #                                      "adaptive": []}, "audioonly": false, "live": false, ...

        # Find the json block containing all the video-urls
        soup_str = str(soup)
        start_pos_json_block = soup_str.find('[{"label"')
        end_pos_json_block = soup_str.find("}]}]")
        end_pos_json_block += len("}]}]")
        json_string = soup_str[start_pos_json_block:end_pos_json_block]
        parsed_json = json.loads(json_string)

        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "json_string", json_string),
                 xbmc.LOGNOTICE)
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "json_string", json_string),
                 xbmc.LOGNOTICE)

        # Determine what quality the video should be
        if self.PREFERRED_VIDEO_QUALITY == "0":
            preferred_video_label = "270p"
        elif self.PREFERRED_VIDEO_QUALITY == "1":
            preferred_video_label = "360p"
        elif self.PREFERRED_VIDEO_QUALITY == "2":
            preferred_video_label = "720p"
        elif self.PREFERRED_VIDEO_QUALITY == "3":
            preferred_video_label = "1080p"
        else:
            preferred_video_label = "1080p"

        # Find the source with the preferred video quality
        sources_index = 0
        label_found = False
        while label_found == False:
            try:
                if parsed_json[sources_index]["label"] == preferred_video_label:
                    label_found = True
                else:
                    sources_index += 1
            except:
                sources_index = 0
                break

        # Find the json block containing the video-url with the preferred video quality
        try:
            json_string = str(parsed_json[sources_index]["sources"])
        except:
            # If the preferred quality is not available, use the best available quality
            json_string = str(parsed_json[0]["sources"])
        json_string = json_string.strip("[")
        json_string = json_string.strip("]")
        json_string = json_string.replace("u'", "'")
        json_string = json_string.replace("'", '"')
        parsed_json = json.loads(json_string)
        video_url = str(parsed_json["src"])

        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, "video_url", str(video_url)), xbmc.LOGNOTICE)

        no_url_found = False
        unplayable_media_file = False
        have_valid_url = False
        if len(video_url) == 0:
            no_url_found = True
        else:
            if HTTPCommunicator().exists(video_url):
                have_valid_url = True
            else:
                unplayable_media_file = True

        # Play video
        if have_valid_url:
            list_item = xbmcgui.ListItem(path=video_url)
            xbmcplugin.setResolvedUrl(self.plugin_handle, True, listitem=list_item)
        #
        # Alert user
        #
        elif no_url_found:
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30505))
        elif unplayable_media_file:
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30506))