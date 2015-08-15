#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from BeautifulSoup import BeautifulSoup
from gamekings_const import __addon__, __settings__, __language__, __images_path__, __date__, __version__
from gamekings_utils import HTTPCommunicator
import os
import re
import sys
import urllib, urllib2
import urlparse
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

#
# Main class
#
class Main:
    def __init__( self ):
        #
        # Videos
        #
        parameters = {"action" : "list", "plugin_category" : __language__(30000), "url" : "http://www.gamekings.tv/category/videos/page/001/", "next_page_possible": "True"}
        url = sys.argv[0] + '?' + urllib.urlencode(parameters)
        listitem = xbmcgui.ListItem( __language__(30000), iconImage="DefaultFolder.png" )
        folder = True
        xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)
        
        #
        # Afleveringen
        #
        parameters = {"action" : "list", "plugin_category" : __language__(30001), "url" : "http://www.gamekings.tv/category/tv-afleveringen/page/001/", "next_page_possible": "True"}
        url = sys.argv[0] + '?' + urllib.urlencode(parameters)
        listitem = xbmcgui.ListItem( __language__(30001), iconImage="DefaultFolder.png" )
        folder = True
        xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)

        #
        # Gamekings Extra
        #
        parameters = {"action" : "list", "plugin_category" : __language__(30002), "url" : "http://www.gamekings.tv/category/nieuws/page/001/", "next_page_possible": "True"}
        url = sys.argv[0] + '?' + urllib.urlencode(parameters)
        listitem = xbmcgui.ListItem( __language__(30002), iconImage="DefaultFolder.png" )
        folder = True
        xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)
        
        #
        # Trailers
        #
        parameters = {"action" : "list", "plugin_category" : __language__(30003), "url" : "http://www.gamekings.tv/tag/Trailer/page/001/", "next_page_possible": "True"}
        url = sys.argv[0] + '?' + urllib.urlencode(parameters)
        listitem = xbmcgui.ListItem( __language__(30003), iconImage="DefaultFolder.png" )
        folder = True
        xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)    

        #
        # E3 2015
        #
        parameters = {"action" : "list", "plugin_category" : __language__(30004), "url" : "http://www.gamekings.tv/tag/E3-2015/page/001/", "next_page_possible": "True"}
        url = sys.argv[0] + '?' + urllib.urlencode(parameters)
        listitem = xbmcgui.ListItem( __language__(30004), iconImage="DefaultFolder.png" )
        folder = True
        xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)                

        # Disable sorting
        xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
		
        # End of list
        xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )