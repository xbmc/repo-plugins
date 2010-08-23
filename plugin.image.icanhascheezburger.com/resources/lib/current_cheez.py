__author__="brian"
__date__ ="$Aug 20, 2010 11:11:39 PM$"

# Show current LOLs. For now, only Cats are supported. Others will follow.

import os
import re
import sys
import xbmc
import xbmcgui
import xbmcplugin
import feedparser
from BeautifulSoup    import BeautifulStoneSoup
import xbmcaddon

__settings__ = xbmcaddon.Addon(id='plugin.image.icanhascheezburger.com')
__language__ = __settings__.getLocalizedString

class Main:
    #
    # Init
    #
    def __init__( self ) :
        # Constants
        self.DEBUG            = False
        self.IMAGES_PATH      = xbmc.translatePath( os.path.join( os.getcwd(), 'resources', 'images' ) )

        self.entries_per_page = 5

        if __settings__.getSetting ("entries_per_page") == "0" :
            self.entries_per_page = 5
        elif __settings__.getSetting ("entries_per_page") == "1" :
            self.entries_per_page = 10
        elif __settings__.getSetting ("entries_per_page") == "2" :
            self.entries_per_page = 20

        self.get_current_lols()

    def get_current_lols( self ) :
        #
        # Get HTML page...
        #
        self.lol_name = "LOL"
        self.current_page = 1
        self.lol_url = "URL"
        url_base = "http://feeds.feedburner.com/ICanHasCheezburger"
        feed = feedparser.parse(url_base)
        for entry in feed.entries:
            title       = entry.title
            if "VIDEO:" in title: continue
            
            content = entry.content[0].value
            images = BeautifulStoneSoup(content).findAll('img')
            full_image_url = ''

            if ".jpg" not in images[0]['src']: continue
            full_image_url = images[0]['src']
            if full_image_url == '': continue
         
            thumbnail_url = full_image_url

            # Add directory entry...
            listitem = xbmcgui.ListItem( title, iconImage="DefaultPicture.png", thumbnailImage = thumbnail_url )
            xbmcplugin.addDirectoryItem( handle=int(sys.argv[ 1 ]), url = full_image_url, listitem=listitem, isFolder=False)

        #
        # Next page entry...
        #
        #next_button_text = __language__(30403) % (self.entries_per_page, self.lol_name)
        #listitem      = xbmcgui.ListItem (next_button_text, iconImage = "DefaultFolder.png", thumbnailImage = os.path.join(self.IMAGES_PATH, 'next-page.png'))
        #next_page_url = "%s?action=list&lol_name=%s&lol_url=%s" % ( sys.argv[0], urllib.quote_plus( self.lol_name), urllib.quote_plus( self.lol_url ) )
        #next_page_url = self.lol_url
        #xbmcplugin.addDirectoryItem( handle = int(sys.argv[1]), url = next_page_url, listitem = listitem, isFolder = True)

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

