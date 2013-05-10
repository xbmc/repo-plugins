#
# Imports
#
from BeautifulSoup import BeautifulSoup
from teamhww_const import __addon__, __settings__, __language__, __images_path__, __date__, __version__
from teamhww_utils import HTTPCommunicator
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
        parameters = {"action" : "list", "plugin_category" : __language__(30000), "url" : "http://www.teamhww.nl/category/videos/page/001/", "next_page_possible": "True"}
        url = sys.argv[0] + '?' + urllib.urlencode(parameters)
        listitem = xbmcgui.ListItem( __language__(30000), iconImage="DefaultFolder.png" )
        folder = True
        xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)
        
        # Disable sorting
        xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
		
        # End of list
        xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )