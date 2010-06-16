#xbmcplugin_podcast.py
#
#
#   NRK plugin for XBMC Media center
#
# Copyright (C) 2009 Victor Vikene  contact: z0py3r@hotmail.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
#

#module imports
import xml.sax
import sys, re, os
import xbmc, xbmcgui, xbmcplugin

from podcast_parser import Podcasts
from feedparser import feedparser
from utils import Key

__settings__ = sys.modules[ "__main__" ].__settings__

class Main:
    
    #define class constants
    FEED   = 'feed'
    VIDEO  = 'video'
    AUDIO  = 'sound'
    PODICO = 'default-pod-icon.png'
    AUDIOPOD_XML = 'podcasts.xml'
    VIDEOPOD_XML = 'videocasts.xml'
    
    #define class variables
    verbose = 1
    
    #create some shortcuts
    resrspath = os.path.join( os.getcwd(), 'resources' )
    imagepath = os.path.join( os.getcwd(), 'resources', 'images' )
    cachepath = os.path.join( xbmc.translatePath("special://profile/"), 
                "addon_data", os.path.basename(os.getcwd()), "cache" )
    
    add = xbmcplugin.addDirectoryItem
    eod = xbmcplugin.endOfDirectory
    entry  = xbmcgui.ListItem
    getset = __settings__.getSetting
    
    
    def __init__(self):
    
        key = Key( sys.argv[2] )
        self.hndl = int( sys.argv[1] )
        
        self.default_image = os.path.join( self.imagepath, self.PODICO )
        self._get_settings()                   
        
        #what to do next? ask the mighty key
        if key.type == self.VIDEO and key.feed == None:
            self.get_casts(self.VIDEOPOD_XML)
            
        elif key.type == self.AUDIO and key.feed == None:
            self.get_casts(self.AUDIOPOD_XML)
            
        elif key.type == self.FEED and key.feed:
            self.parse_feed(key.feed, key.image)
        
        
        if self.verbose:
            print 'end of plugin_podcast.MAIN()'
    
    
    def _get_settings(self):
      pass
      
      
    def parse_feed(self, url, image):
        
        if self.verbose:
            print 'parse feed from %s' % url
            
        feedcount = 0
        
        #parse feed
        rss = feedparser.parse(url)
        
        for f in rss.entries:
            #iterate and add to directory
            
            link  = f.enclosures[0].href
            size  = f.enclosures[0].length
            label = f.title.encode('utf-8', 'replace')
            
            listitem = self.entry( label, thumbnailImage=image, path=link )
            
            #add to directory
            ok = self.add(
                    self.hndl, 
                    url = link, 
                    listitem = listitem, 
                    isFolder = False
                )
            
            feedcount += 1
        
        if self.verbose:
            print 'added %d feed entries' % feedcount
            print 'success: %s' % repr(feedcount > 0)
        
        #Tell end of directory listing
        if feedcount > 0:
            self.eod( self.hndl, ok, False, False ) 
        else:
             exec "xbmcgui.Dialog().ok('No podcasts received from NRK.no', '')"
    
    def get_casts(self, xml_filename):
        
        if self.verbose:
            print 'listing podcasts from xml file: %s' % xml_filename
            
        ok = True
        castcount = 0
        
        catalog = os.path.join( self.resrspath, xml_filename )
        parser  = xml.sax.make_parser( )
        folder  = Podcasts( )
        
        parser.setContentHandler( folder )
        parser.parse( catalog )

        
        for cast in folder.entries:
            #iterate and add to directory
            
            pfx = 'podcast';  type = self.FEED
            img = cast.image; link = cast.link
            lbl = cast.title.encode('utf-8', 'replace')
            
            if not img: 
                #set default thumbnail if no image
                img = self.default_image
            
            #generate key for item
            url = Key.build_url( pfx, type=type, feed=link, image=img )
            listitem = self.entry( lbl, thumbnailImage=img, path=url )
            
            #add listitem to directory
            ok = self.add(
                    self.hndl, 
                    url = url, 
                    listitem = listitem, 
                    isFolder = True
                )
                
            castcount += 1
        
        if self.verbose:
            print 'added %d feed entries' % castcount,
            print 'success: %s' % repr( ok )
        
        #Tell end of directory listing
        self.eod( self.hndl, ok, False, False )   
