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

import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
from utils import Key, PluginError, PluginHTTPError, PluginConnectionError
from feedparser import feedparser



class FeedInfo:

    base = 'http://video.nrkbeta.no/feeds/kategori/'
    info = [('TV serier', 'tv-serier'), ('Diverse', 'diverse'),
            ('Presentasjoner', 'presentasjoner'),
            ('Konferanser og messer', 'konferanser-og-messer'),
            ('Fra TV', 'fra-tv'), ('Lydfiler', 'lydfiler')]
    
    def __init__(self):
        pass
        
    def __iter__(self):
        return self.next()
        
    def next(self):
        for item in self.info:
            lbl, url = item; url = '%s%s/' % (self.base, url)
            yield lbl, url
    
    def geturl(self, index):
        return '%s%s/' % (self.base, self.info[index][1])
  

  
class Main:

    #define constants
    IMG_TAIL_TPL = '_jpg_180x94_crop_q85.jpg'
    IMG_TPL = '%s/thumbnails/%s%s'
    RSSICO = os.path.join(os.getcwd(), 'resources', 'images', 'rss-alt-icon.png')
    
    #class variables
    verbose = 1
    add = xbmcplugin.addDirectoryItem
    eod = xbmcplugin.endOfDirectory
    entry = xbmcgui.ListItem
    
    
    def __init__(self):
        
        self.hndl = int( sys.argv[1] )
        key = Key( sys.argv[2] )
        
        if key.id == None:
            self.parse_main_directory()
        else:
            self.parse_feed(key)
            
  
  
    def parse_feed(self, key):
    
        ok = True; status = 0; feedcount = 0
        url = FeedInfo().geturl(key.id)
        rss = feedparser.parse(url)
        
        if self.verbose:
            print 'parse feed from %s' % url
        
        try:
            status = rss.status
        except:
            raise PluginConnectionError(
                    'Connection Problem',
                    'Plugin could not connect',
                    'No data received. Abort directory listing..'
                )
                    
        if status not in range(200,300):
            raise PluginHTTPError(url, status)
        else:
            if self.verbose:
                print 'HTTP response code for rss: %d' % status
            
            
        for feed in rss.entries:
        
            label = feed.title; url = feed.links[1].href
            path = os.path.dirname(url)
            base = os.path.basename(url)
            image = self.IMG_TPL % ( path, base, self.IMG_TAIL_TPL )

            li = self.entry( label, thumbnailImage=image )
            
            ok = self.add( 
                    self.hndl,
                    url = url,
                    listitem = li, 
                    isFolder = False 
                )
            feedcount += 1
        
        if self.verbose:
            print 'added %d entries. success: %s' % ( feedcount, repr(ok) )
        
        if ok: #tell end of directory
            self.eod( self.hndl )

            
        
    def parse_main_directory(self):
        if self.verbose:
            print 'list main feed directory'
        
        ok = True; index = 0
        
        for lbl, id in FeedInfo():
        
            prefix, type, id = ('nrkbeta', 'feed', index)
            url = Key.build_url( prefix, type=type, id=id )
            
            li = self.entry( 
                    lbl, 
                    iconImage = self.RSSICO, 
                    thumbnailImage = self.RSSICO 
                )
                        
            ok = self.add( 
                    self.hndl,
                    url = url, 
                    listitem = li, 
                    isFolder = True 
                )               
            index += 1                       
        
        if self.verbose:
            print 'added %d entries. success: %s' % ( index, repr(ok) )
        
        if ok: #tell end of directory
            self.eod( self.hndl )