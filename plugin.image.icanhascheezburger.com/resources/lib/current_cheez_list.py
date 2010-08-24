__author__="brian"
__date__ ="$Aug 20, 2010 11:11:39 PM$"

# Show current LOLs. For now, only Cats are supported. Others will follow.

import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import feedparser
import urllib
from BeautifulSoup    import BeautifulStoneSoup
import xbmcaddon

__settings__ = xbmcaddon.Addon(id='plugin.image.icanhascheezburger.com')
__language__ = __settings__.getLocalizedString

class Main:
    #
    # Init
    #
    def __init__(self, url) :
        # Constants
        self.DEBUG            = False
        self.IMAGES_PATH      = xbmc.translatePath( os.path.join( os.getcwd(), 'resources', 'images' ) )
        #params = dict(part.split('=') for part in sys.argv[ 2 ][ 1: ].split('&'))
        #self.lol_name       = urllib.unquote_plus( params[ "lol_name" ] )
        #self.lol_url        = urllib.unquote_plus( params[ "lol_url" ] )
        self.url = url
        xbmc.log('URL: %s' % self.url)
        self.get_current_lols()

        
    def get_current_lols( self ) :
        #
        # Get HTML page...
        #
        feed = feedparser.parse(self.url)
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
        if __settings__.getSetting("home_page") == "1":
            # The default start page is this page, so add a Home Page item
            next_button_text = __language__(30211)
            listitem = xbmcgui.ListItem(next_button_text, iconImage = "DefaultFolder.png", thumbnailImage="DefaultFolder.png")
            url = "%s?action=forcemain" % sys.argv[0]
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=True)
        #
        # Disable sorting...
        #
        xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

        #
        # Label (top-right)...
        #
        #trlabel = "%s" % self.lol_name
        #xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=( trlabel ) )

        #
        # End of directory...
        #
        xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )

