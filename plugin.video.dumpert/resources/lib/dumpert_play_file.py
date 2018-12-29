#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import object
import sys
import urllib.request, urllib.error, urllib.parse
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
        self.file = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['file'][0]

        log("self.file",self.file)

        #
        # Play video...
        #
        self.playVideo()

    #
    # Play video...
    #
    def playVideo(self):
        list_item = xbmcgui.ListItem(path=self.file)
        xbmcplugin.setResolvedUrl(self.plugin_handle, True, list_item)