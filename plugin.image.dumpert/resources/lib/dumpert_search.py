#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from future import standard_library
standard_library.install_aliases()
from builtins import object
import sys
import xbmc
import urllib.parse

from resources.lib.dumpert_const import SEARCH_URL_PART_1, SEARCH_URL_PART_2, SEARCH_URL_PART_3, \
    INITIAL_PAGE_NUMBER, LANGUAGE, log


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

        # We are going to update the value of the key 'url' the system parameters, ie after 'url=' and before next key
        # ?action=search&next_page_possible=True&plugin_category=Search&url=https%3a%2f%2fapi-live.dumpert.nl%2fmobile_api%2fjson%2fsearch%2f
        # An url decoded search url should look like this:
        # https://api-live.dumpert.nl/mobile_api/json/search/<search-term>/<page-number>/"

        log("sys.argv[2]-1", sys.argv[2])

        # Convert the parameter string to a dictionary
        parameter_dictionary = urllib.parse.parse_qs(sys.argv[2])

        #log("parameter_dictionary-1", parameter_dictionary)

        # Update value of key 'url', remove '/' from search term to prevent decoding errors
        parameter_dictionary['url'] = [SEARCH_URL_PART_1 + urllib.parse.quote(search_term.replace('/','')) + SEARCH_URL_PART_2 + INITIAL_PAGE_NUMBER + SEARCH_URL_PART_3]

        #log("parameter_dictionary-2", parameter_dictionary)

        # Convert to a flat dictionary with first item from each list
        flat_parameter_dictionary = {k: v[0] for k, v in parameter_dictionary.items()}

        #log("flat_parameter_dictionary", flat_parameter_dictionary)

        # Encode the URL parameters
        sys.argv[2] = urllib.parse.urlencode(flat_parameter_dictionary, safe='?')

        log("sys.argv[2]-2", sys.argv[2])

        import resources.lib.dumpert_json as plugin

        plugin.Main()