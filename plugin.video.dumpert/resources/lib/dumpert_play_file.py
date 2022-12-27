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
import xbmc
import xbmcgui
import xbmcplugin

from resources.lib.dumpert_const import LANGUAGE, SETTINGS, convertToUnicodeString, log, getSoup


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
        # Try and get the title.
        # When starting a video with a browser (f.e. in chrome the 'send to kodi'-extension) the url will be
        # something like this:
        # plugin://plugin.video.dumpert/?action=play&video_page_url=http%3A%2F%2Fwww.dumpert.nl%2Fmediabase%2F7095997%2F1f72985c%2Fmevrouw_heeft_internetje_thuis.html
        # and there won't be a title available.
        try:
            self.title = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)['title'][0]
            self.title = convertToUnicodeString(self.title)
        except KeyError:
            self.title = ""

        log("self.file",self.file)

        #
        # Show short wait dialog with title if we have a title.
        #
        if self.title == "":
            pass
        else:
            dialog_wait = xbmcgui.DialogProgress()
            dialog_wait.create(LANGUAGE(30504), self.title)
            # wait 1 second
            xbmc.sleep(1000)

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