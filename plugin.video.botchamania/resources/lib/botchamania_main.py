#
# Imports
#
from BeautifulSoup import BeautifulSoup
from botchamania_const import __addon__, __settings__, __language__, __images_path__, __date__, __version__
from botchamania_utils import HTTPCommunicator
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
#         #
#         # All Videos
#         #
#         parameters = {"action" : "list", "plugin_category" : __language__(30000), "url" : "http://botchamania.com/page/1/", "next_page_possible": "True"}
#         url = sys.argv[0] + '?' + urllib.urlencode(parameters)
#         listitem = xbmcgui.ListItem( __language__(30000), iconImage="DefaultFolder.png" )
#         folder = True
#         xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)
         
        #
        # Botchamania
        #
        parameters = {"action" : "list", "plugin_category" : __language__(30001), "url" : "http://botchamania.com/category/botchamania/page/1/", "next_page_possible": "True"}
        url = sys.argv[0] + '?' + urllib.urlencode(parameters)
        listitem = xbmcgui.ListItem( __language__(30001), iconImage="DefaultFolder.png" )
        folder = True
        xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)
        
        #
        # OSWReview
        #
        parameters = {"action" : "list", "plugin_category" : __language__(30002), "url" : "http://botchamania.com/category/oswreview/page/1/", "next_page_possible": "True"}
        url = sys.argv[0] + '?' + urllib.urlencode(parameters)
        listitem = xbmcgui.ListItem( __language__(30002), iconImage="DefaultFolder.png" )
        folder = True
        xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)
  
        #
        # NerdSlam
        #
        parameters = {"action" : "list", "plugin_category" : __language__(30003), "url" : "http://botchamania.com/category/nerdslam/page/1/", "next_page_possible": "True"}
        url = sys.argv[0] + '?' + urllib.urlencode(parameters)
        listitem = xbmcgui.ListItem( __language__(30003), iconImage="DefaultFolder.png" )
        folder = True
        xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)     

#         #
#         # AEPodcast (Audio only)
#         #
#         parameters = {"action" : "list", "plugin_category" : __language__(30004), "url" : "http://botchamania.com/category/aepodcast/page/1/", "next_page_possible": "True"}
#         url = sys.argv[0] + '?' + urllib.urlencode(parameters)
#         listitem = xbmcgui.ListItem( __language__(30004), iconImage="DefaultFolder.png" )
#         folder = True
#         xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)   
        
#         #
#         # Ruthless Aggression (Audio only)
#         #
#         parameters = {"action" : "list", "plugin_category" : __language__(30005), "url" : "http://botchamania.com/category/ruthless-aggression/page/1/", "next_page_possible": "True"}
#         url = sys.argv[0] + '?' + urllib.urlencode(parameters)
#         listitem = xbmcgui.ListItem( __language__(30005), iconImage="DefaultFolder.png" )
#         folder = True
#         xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)

#         #
#         # Blogamania (Text only)
#         #
#         parameters = {"action" : "list", "plugin_category" : __language__(30006), "url" : "http://botchamania.com/category/blogamania/page/1/", "next_page_possible": "True"}
#         url = sys.argv[0] + '?' + urllib.urlencode(parameters)
#         listitem = xbmcgui.ListItem( __language__(30006), iconImage="DefaultFolder.png" )
#         folder = True
#         xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder) 

#         #
#         # Raw Rant (Text only)
#         #
#         parameters = {"action" : "list", "plugin_category" : __language__(30007), "url" : " http://botchamania.com/category/raw-rant/page/1/", "next_page_possible": "True"}
#         url = sys.argv[0] + '?' + urllib.urlencode(parameters)
#         listitem = xbmcgui.ListItem( __language__(30007), iconImage="DefaultFolder.png" )
#         folder = True
#         xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder) 
       
        #
        #   PPV Recaps
        #
        parameters = {"action" : "list", "plugin_category" : __language__(30008), "url" : "http://botchamania.com/category/ppv-recaps/page/1/", "next_page_possible": "True"}
        url = sys.argv[0] + '?' + urllib.urlencode(parameters)
        listitem = xbmcgui.ListItem( __language__(30008), iconImage="DefaultFolder.png" )
        folder = True
        xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder) 
        
#         #
#         # Media & Press (Text only)
#         #
#         parameters = {"action" : "list", "plugin_category" : __language__(30009), "url" : "http://botchamania.com/category/media-press/page/1/", "next_page_possible": "True"}
#         url = sys.argv[0] + '?' + urllib.urlencode(parameters)
#         listitem = xbmcgui.ListItem( __language__(30009), iconImage="DefaultFolder.png" )
#         folder = True
#         xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder) 
        
#         #
#         # Misc. (Text only)
#         #
#         parameters = {"action" : "list", "plugin_category" : __language__(30010), "url" : "http://botchamania.com/category/misc/page/1/", "next_page_possible": "True"}
#         url = sys.argv[0] + '?' + urllib.urlencode(parameters)
#         listitem = xbmcgui.ListItem( __language__(30010), iconImage="DefaultFolder.png" )
#         folder = True
#         xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder) 

        #
        # Botchamania Archive   
        #
        parameters = {"action" : "list-archive", "plugin_category" : __language__(30011), "url" : "http://botchamaniaarchive.com/", "next_page_possible": "False"}
        url = sys.argv[0] + '?' + urllib.urlencode(parameters)
        listitem = xbmcgui.ListItem( __language__(30011), iconImage="DefaultFolder.png" )
        folder = True
        xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)
        
        #
        # Botchamania Archive Specials
        #
        parameters = {"action" : "list-archive-specials", "plugin_category" : __language__(30012), "url" : "http://www.botchamaniaarchive.com/category/specials/page/1/", "next_page_possible": "False"}
        url = sys.argv[0] + '?' + urllib.urlencode(parameters)
        listitem = xbmcgui.ListItem( __language__(30012), iconImage="DefaultFolder.png" )
        folder = True
        xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)

        # Disable sorting...
        xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
		
        # End of list...
        xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )