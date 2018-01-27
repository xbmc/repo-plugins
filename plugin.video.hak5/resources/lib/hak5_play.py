#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import object
import requests
import sys
import urllib.parse
import xbmc
import xbmcgui
import xbmcplugin

from .hak5_const import LANGUAGE, HEADERS, convertToUnicodeString, log, getSoup

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

        log("ARGV", repr(sys.argv))

        # Parse parameters...
        self.video_page_url = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['video_page_url'][0]

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
        dialog_wait = xbmcgui.DialogProgress()

        #
        # Get current list item details...
        #
        # title = unicode(xbmc.getInfoLabel("listitem.Title"), "utf-8")
        thumbnail_url = xbmc.getInfoImage("list_item.Thumb")
        # studio = unicode(xbmc.getInfoLabel("list_item.Studio"), "utf-8")
        plot = xbmc.getInfoLabel("list_item.Plot")
        genre = xbmc.getInfoLabel("list_item.Genre")

        reply = ''
        session = ''

        # requests is sooooo nice, respect!
        session = requests.Session()

        # get the page that contains the video
        self.video_page_url = str(self.video_page_url).replace('https','http')

        #
        # Get HTML page
        #
        response = requests.get(self.video_page_url, headers=HEADERS)

        html_source = response.text
        html_source = convertToUnicodeString(html_source)

        # Parse response
        soup = getSoup(html_source)

        # log("html_source", html_source)

        video_url = ''
        no_url_found = True
        have_valid_url = False

        #<iframe width="900" height="506" src="https://www.youtube.com/embed/fYdFNFTSoy4?feature=oembed&#038;wmode=opaque&#038;rel=0&#038;showinfo=0&#038;modestbranding=0"
        # frameborder="0" gesture="media" allowfullscreen></iframe>

        # let's extract the youtube-id
        html_source = str(html_source)
        start_pos_youtube_embed = html_source.find('youtube.com/embed/')
        if start_pos_youtube_embed > 0:
            start_pos_youtube_id = start_pos_youtube_embed + len('youtube.com/embed/')
            search_for_string = '?'
            end_pos_youtube_id = html_source.find(search_for_string, start_pos_youtube_id)
            if end_pos_youtube_id > 0:
                youtube_id = html_source[start_pos_youtube_id:end_pos_youtube_id]

                log("youtube_id", youtube_id)

                video_url = makeYouTubePluginUrl(youtube_id)
                no_url_found = False
                have_valid_url = True

                log("video_url", video_url)

        # Play video...
        if have_valid_url:
            list_item = xbmcgui.ListItem(path=video_url)
            xbmcplugin.setResolvedUrl(self.plugin_handle, True, list_item)
        #
        # Alert user
        #
        elif no_url_found:
            xbmcgui.Dialog().ok(LANGUAGE(30000), LANGUAGE(30107))


def makeYouTubePluginUrl(youtube_id):
    return 'plugin://plugin.video.youtube/play/?video_id=%s' % youtube_id