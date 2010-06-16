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
import xml.sax
from xbmcplugin import addDirectoryItem, endOfDirectory
from xbmcgui import ListItem
from utils import Key
from webradio_parser import Radio

class Main:
    
    f_def = {
            'wma': 'Windows Media',
            'mp3': 'Mp3',
            'ogg': 'Ogg/Vorbis'
        }
        
    def __init__(self):
        
        self.handle = int(sys.argv[1])
        key = Key(sys.argv[2])
        
        catalog = os.path.join(os.getcwd(), 'resources', 'webradio.xml')
        self.parser = xml.sax.make_parser()
        self.folder = Radio()
        self.parser.setContentHandler(self.folder)
        self.parser.parse(catalog)

        if not key.id:
            self.parse_channels()
        else:
            self.parse_streams(key.id, key.image)
    
    
    def parse_streams(self, sid, image):
        dir = self.folder.radio
        for e in dir[sid].streams:
            label = '%s %d kbps' % (self.f_def[e.format], e.bitrate)
            ok = self.add(label, e.link, image, isdir=False)
        self.end(ok)
        
    
    def parse_channels(self):
    
        pathy = os.path.join
        channels = self.folder.radio
        rpath = pathy(os.getcwd(), 'resources', 'images')
        
        for cid in channels:
            label = channels[cid].title
            image = pathy(rpath, channels[cid].logo)
            print image
            ok = self.add(label, image=image, ident=cid)
        self.end(ok)
        
            
    def add(self, label, url=None, image='', ident=None, isdir=True):
        if ident and not url:
            url = Key.build_url('webradio', id=ident, image=image)
        li = ListItem(label, thumbnailImage=image)
        ok = addDirectoryItem(self.handle, url=url, listitem=li, isFolder=isdir)
        return ok
        
        
    def end(self, ok=False):
        #tell end of directory
        if ok:
            endOfDirectory(self.handle)
               
            
            