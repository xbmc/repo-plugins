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

import xml.sax.handler


#container class for podcasts
class Cast:
    def __init__(self):
        self.title = ''
        self.link  = ''
        self.desc  = ''
        self.image = None
      

      
class Podcasts(xml.sax.handler.ContentHandler):
    
    def __init__(self):
        self.in_cast = 0
        self.entries = []
        
        
    def startElement(self, name, attributes):
        if name == "podcast":
        
            #no need for it if there's no link
            if not attributes.has_key('link'):
                return
            
            self.in_cast = 1
            
            self.cast = Cast()
            self.cast.link = attributes['link']
            
            if attributes.has_key('image'):
                self.cast.image = attributes['image']
                
            if attributes.has_key('description'):
                self.cast.desc = attributes['description']
    
    
    def characters(self, data):
        if self.in_cast:
            self.cast.title += data
            
    
    def endElement(self, name):
        if name == "podcast":
            self.entries.append(self.cast)
            self.in_cast = 0
            