#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
import sys
import urllib2
import urlparse
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
        # wait 1 second
        xbmc.sleep(1000)

        # video_page_url will be something like this: http://tweakers.net/video/7893/world-of-tanks-86-aankondiging.html
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

        # from the mobile site
        # <a class="fancyButton grey" href=" http://content.tweakers.tv/stream/account=s7JeEm/item=Qq4LN6rD3YAE/file=UCpDMoLTlkAA/Qq4LN6rD3YAE_2TwrcupbKsuA.mp4">720p</a>
        # http://content.tweakers.tv/stream/account=s7JeEm/item=Qq4LN6rD3YAE/file=UCpDMoLTlkAA/Qq4LN6rD3YAE_2TwrcupbKsuA.mp4
        video_div = soup.find("div", {"class": "videoQuality"})
        video_url = video_div.findAll('a', href=True)[-1]

        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "video_url", str(video_url)),
                     xbmc.LOGNOTICE)

        video_url = str(video_url['href'])
        video_url = video_url.replace(" ", "")

        if self.DEBUG == 'true':
            xbmc.log(
                "[ADDON] %s v%s (%s) debug mode, %s = %s" % (ADDON, VERSION, DATE, "altered video_url", str(video_url)),
                xbmc.LOGNOTICE)

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
