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
import xbmc
import urllib.parse

from resources.lib.dumpert_const import SEARCH_URL_PART_2, SEARCH_URL_PART_3, INITIAL_PAGE_NUMBER, LANGUAGE, \
    log, convertToUnicodeString


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

        # Get search term from user
        keyboard = xbmc.Keyboard('', LANGUAGE(30508))
        keyboard.doModal()

        if keyboard.isConfirmed():
            search_term = keyboard.getText()
            # If the user has entered nothing, we stop
            if search_term == "":
                sys.exit(0)
        else:
            # If the user cancels the input box, we stop
            sys.exit(0)

        #log("sys.argv[2]-1", sys.argv[2])

        # Constructing last part of search url in the parameters, i.e. the part after the parameters in sys.argv[2]
        # so after this: ?action=search&next_page_possible=True&plugin_category=Search&url=https%3a%2f%2fpost.dumpert.nl%2fapi%2fv1.0%2fsearch%2f
        # an url decoded search url should look like this: 
        # https://post.dumpert.nl/api/v1.0/search/<user entered search term>/0/?order=date&media_type=all&app=www.dumpert.nl"
        urldecoded_last_part_search_url = search_term + SEARCH_URL_PART_2 + INITIAL_PAGE_NUMBER + SEARCH_URL_PART_3
        
        #log("urldecoded_last_part_search_url", urldecoded_last_part_search_url)
        
        # Url encode the url string
        urlencoded_last_part_search_url = urllib.parse.quote(urldecoded_last_part_search_url, safe='')

        #log("urlencoded_last_part_search_url", urlencoded_last_part_search_url)
        
        sys.argv[2] = sys.argv[2] + urlencoded_last_part_search_url

        #log("sys.argv[2]-2", sys.argv[2])

        import resources.lib.dumpert_json as plugin

        plugin.Main()