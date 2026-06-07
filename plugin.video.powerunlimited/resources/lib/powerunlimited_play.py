#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from future import standard_library
standard_library.install_aliases()
from builtins import object
import sys
import urllib.request, urllib.parse, urllib.error
import xbmcgui
import xbmcplugin

from resources.lib.powerunlimited_const import log


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

        # Parse parameters
        self.video_page_url = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['video_page_url'][0]

        log("self.video_page_url", self.video_page_url)

        #
        # Play video
        #
        self.playVideo()

    #
    # Play video...
    #
    def playVideo(self):
        video_url = self.video_page_url
        list_item = xbmcgui.ListItem(path=video_url)
        xbmcplugin.setResolvedUrl(self.plugin_handle, True, list_item)