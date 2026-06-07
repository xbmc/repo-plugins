#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from builtins import str, object
import sys
import urllib.parse
import xbmc
import xbmcgui
import xbmcplugin

# from future import standard_library
# standard_library.install_aliases()

# Import your custom modules
from resources.lib.worldstarhiphop_const import SETTINGS, LANGUAGE, INITIAL_API_SEARCH_URL, add_video_to_listing, log

# Main class
class Main(object):
    """
    Main class for the Kodi addon.
    """
    def __init__(self):
        # Get the command line arguments
        # Get the plugin url in plugin:// notation
        self.plugin_url = sys.argv[0]
        # Get the plugin handle as an integer number
        self.plugin_handle = int(sys.argv[1])

        # Get plugin settings
        self.VIDEO = SETTINGS.getSetting('video')

        log("ARGV", repr(sys.argv))

        self.plugin_category = LANGUAGE(30000)
        self.next_page_possible = "True"
        keyboard = xbmc.Keyboard('', LANGUAGE(30103))
        keyboard.doModal()
        if keyboard.isConfirmed():
            self.search_string = keyboard.getText()
            # If the user has entered nothing, we stop
            if self.search_string == "":
                sys.exit(0)
            else:
                self.video_list_page_url = str(INITIAL_API_SEARCH_URL).replace("<search_string>", self.search_string)
        else:
            # If the user cancels the input box, we stop
            sys.exit(0)

        # Set the parameters for the list script
        parameters = {"action": "list", "plugin_category": LANGUAGE(30000), "next_page_possible": 'True', "url": self.video_list_page_url}
        sys.argv[2] = f"{self.plugin_url}?{urllib.parse.urlencode(parameters)}"

        log("sys.argv[2]", sys.argv[2])

        # Use list script to display the search results
        import resources.lib.worldstarhiphop_list as plugin

        plugin.Main()