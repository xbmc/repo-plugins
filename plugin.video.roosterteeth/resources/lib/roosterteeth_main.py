#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from BeautifulSoup import BeautifulSoup
from roosterteeth_const import __addon__, __settings__, __language__, __images_path__, __date__, __version__
import requests
import os
import re
import sys
import urllib, urllib2
import urlparse
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

RECENTLYADDEDURL = 'https://roosterteeth.com/episode/recently-added?page=001'
ROOSTERTEETHSHOWSURL = 'https://www.roosterteeth.com/show/'
ACHIEVEMENTHUNTERURL = 'https://achievementhunter.com/show/'
THEKNOWSHOWSURL = 'https://theknow.tv/show'
#FUNHAUSSHOWSURL = 'https://fun.haus/show'

#
# Main class
#
class Main:
    def __init__( self ):
        #
        # Recently Added Episodes
        #
        parameters = {"action" : "list-episodes", "plugin_category" : __language__(30000), "url" : RECENTLYADDEDURL, "next_page_possible": "True"}
        url = sys.argv[0] + '?' + urllib.urlencode(parameters)
        listitem = xbmcgui.ListItem( __language__(30000), iconImage="DefaultFolder.png" )
        folder = True
        xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)
        #
        # Roosterteeth
        #
        parameters = {"action" : "list-shows", "plugin_category" : __language__(30001), "url" : ROOSTERTEETHSHOWSURL, "next_page_possible": "False"}
        url = sys.argv[0] + '?' + urllib.urlencode(parameters)
        listitem = xbmcgui.ListItem( __language__(30001), iconImage="DefaultFolder.png" )
        folder = True
        xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)
        #
        # Achievement Hunter
        #
        parameters = {"action" : "list-shows", "plugin_category" : __language__(30002), "url" : ACHIEVEMENTHUNTERURL, "next_page_possible": "False"}
        url = sys.argv[0] + '?' + urllib.urlencode(parameters)
        listitem = xbmcgui.ListItem( __language__(30002), iconImage="DefaultFolder.png" )
        folder = True
        xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)
        #
        # The Know Tv
        #
        parameters = {"action" : "list-shows", "plugin_category" : __language__(30003), "url" : THEKNOWSHOWSURL, "next_page_possible": "False"}
        url = sys.argv[0] + '?' + urllib.urlencode(parameters)
        listitem = xbmcgui.ListItem( __language__(30003), iconImage="DefaultFolder.png" )
        folder = True
        xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)

# Removed because of SSL error on 16 september 2015
#         #
#         # Fun Haus
#         #
#         parameters = {"action" : "list-shows", "plugin_category" : __language__(30004), "url" : FUNHAUSSHOWSURL, "next_page_possible": "False"}
#         url = sys.argv[0] + '?' + urllib.urlencode(parameters)
#         listitem = xbmcgui.ListItem( __language__(30004), iconImage="DefaultFolder.png" )
#         folder = True
#         xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)                        
           
        # Disable sorting...
        xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
        
        # End of list...
        xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )