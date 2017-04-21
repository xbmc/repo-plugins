#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
import os
import re
import requests
import sys
import urllib
import urlparse
import xbmc
import xbmcgui
import xbmcplugin
from BeautifulSoup import BeautifulSoup

from dumpert_const import ADDON, SETTINGS, LANGUAGE, IMAGES_PATH, DATE, VERSION


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
        self.DEBUG = SETTINGS.getSetting('debug')

        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % (
                ADDON, VERSION, DATE, "ARGV", repr(sys.argv), "File", str(__file__)), xbmc.LOGNOTICE)

        # Parse parameters
        # urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['url'][0]
        base = urlparse.urlparse(sys.argv[2])
        query = base.query
        args = urlparse.parse_qs(query)
        url = args['url'][0]

        if self.DEBUG == 'true':
            xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
                ADDON, VERSION, DATE, "self.video_list_page_url", str(url)),
                     xbmc.LOGNOTICE)

        # Get query
        q = ''
        keyboard = xbmc.Keyboard('', LANGUAGE(30508))
        keyboard.doModal()

        if keyboard.isConfirmed():
            q = keyboard.getText()

        url = requests.post(url, data={'q': q, 'cat': '', 'submit': 'zoek'}).url

        # Converting URL argument to proper query string like 'http://www.dumpert.nl/search/ALL/fiets/1/'
        args.update({'url': url + '1/'})
        encoded_args = urllib.urlencode(args, doseq=True)

        sys.argv[2] = urlparse.ParseResult(base.scheme, base.netloc, base.path, base.params, encoded_args,
                                           base.fragment).geturl()  # Run list on results
        import dumpert_list as plugin

        plugin.Main()
