#
# Imports
#
import os
import re
import sys
import xbmc
import xbmcgui
import xbmcplugin
import urllib
from BeautifulSoup    import SoupStrainer
from BeautifulSoup    import BeautifulSoup
from BeautifulSoup    import BeautifulStoneSoup
from xbmcplugin_utils import HTTPCommunicator

import xbmcaddon

__settings__ = xbmcaddon.Addon(id='plugin.image.icanhascheezburger.com')

__language__ = __settings__.getLocalizedString

#
# Main class
#
class Main:
    #
    # Init
    #
    def __init__( self ) :
        # Constants
        self.DEBUG            = False
        self.IMAGES_PATH      = xbmc.translatePath( os.path.join( os.getcwd(), 'resources', 'images' ) )
        
        # Parse parameters...
        params = dict(part.split('=') for part in sys.argv[ 2 ][ 1: ].split('&'))
        self.lol_name       = urllib.unquote_plus( params[ "lol_name" ] )
        self.lol_url        = urllib.unquote_plus( params[ "lol_url" ] )
        self.current_page     =                int ( params.get( "page", "1" ) )
        self.entries_per_page = 5
        # Parameters
        if __settings__.getSetting ("entries_per_page") == "0" :
            self.entries_per_page = 5
        elif __settings__.getSetting ("entries_per_page") == "1" :
            self.entries_per_page = 10
        elif __settings__.getSetting ("entries_per_page") == "2" :
            self.entries_per_page = 20

        #
        # Get picture list...
        #
        self.getPictures()
    
    #
    # Get pictures...
    #
    def getPictures( self ) :        
        #
        # Get HTML page...
        #
        httpCommunicator = HTTPCommunicator()
        htmlSource = httpCommunicator.get( self.lol_url + str(self.entries_per_page))

        #
        # Parse HTML page...
        #
        pictures = BeautifulStoneSoup(htmlSource).findAll('picture')
        for picture in pictures:
            #
            # Title (date)
            #
            title       = picture.title.string
           
            #
            # Thumbnail & full image...
            #

            full_image_url = picture.lolimageurl.string
            thumbnail_url  = picture.thumbnailimageurl.string
            
                                    
            # Add directory entry...
            listitem = xbmcgui.ListItem( title, iconImage="DefaultPicture.png", thumbnailImage = thumbnail_url )
            xbmcplugin.addDirectoryItem( handle=int(sys.argv[ 1 ]), url = full_image_url, listitem=listitem, isFolder=False)

        #
        # Next page entry...
        #
        next_button_text = __language__(30403) % (self.entries_per_page, self.lol_name)
        listitem      = xbmcgui.ListItem (next_button_text, iconImage = "DefaultFolder.png", thumbnailImage = os.path.join(self.IMAGES_PATH, 'next-page.png'))
        next_page_url = "%s?action=list&lol_name=%s&lol_url=%s" % ( sys.argv[0], urllib.quote_plus( self.lol_name), urllib.quote_plus( self.lol_url ) )
        #next_page_url = self.lol_url
        xbmcplugin.addDirectoryItem( handle = int(sys.argv[1]), url = next_page_url, listitem = listitem, isFolder = True)
        
        #    
        # Disable sorting...
        #
        xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
        
        #
        # Label (top-right)...
        #
        trlabel = "%s (%s)" % ( self.lol_name, (__language__(30402) % self.current_page))
        xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=( trlabel ) )
        
        #
        # End of directory...
        #
        xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
