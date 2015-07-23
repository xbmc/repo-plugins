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

reload(sys)  
sys.setdefaultencoding('utf8')

BASEURL = 'http://www.roosterteeth.com/show/'

#
# Main class
#
class Main:
    def __init__( self ):
        #
        # Init
        #
        self.DEBUG     = __settings__.getSetting('debug')
        
        # 
        # Get HTML page...
        #
        response = requests.get(BASEURL)
        html_source = response.text
        html_source = html_source.encode('utf-8', 'ignore')

#       <li>
#         <a href="http://www.roosterteeth.com/show/red-vs-blue">
#             <div class="block-container">
#                 <div class="image-container">
#                     <img src="//s3.amazonaws.com/cdn.roosterteeth.com/uploads/images/9a888611-5b17-49ab-ad49-ca0ad6a86ee1/sm/rvb600.jpg" alt="Red vs. Blue">
#                 </div>
#             </div>
#             <p class="name">Red vs. Blue</p>
#             <p class="post-stamp">13 seasons | 377 episodes</p>
#         </a>
#       </li>
        # Parse response...
        soup = BeautifulSoup( html_source )
        
        shows = soup.findAll('li')
        
        if (self.DEBUG) == 'true':
            xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "len(shows)", str(len(shows)) ), xbmc.LOGNOTICE )
        
        for show in shows:
            #skip show if it doesn't contain BASEURL
            if str(show.a).find(BASEURL) < 0:
                continue
            
            url = show.a['href']
            
            try:
                thumbnail_url =  "https:" + show.img['src']
            except:    
                thumbnail_url = ''
            
            title = show.a.text
            if title == '':
                try:
                    title = show.img['alt']
                except:
                    title = 'Unknown Show Name'
            
            # Add to list...
            parameters = {"action" : "list", "show_name" : title, "show_url" : url, "next_page_possible": "False"}
            url = sys.argv[0] + '?' + urllib.urlencode(parameters)
            listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail_url )
            listitem.setInfo( "video", { "Title" : title, "Studio" : "roosterteeth" } )
            folder = True
            xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)
           
        # Disable sorting...
        xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
        
        # End of list...
        xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )