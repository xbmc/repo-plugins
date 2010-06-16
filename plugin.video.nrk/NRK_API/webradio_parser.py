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
 
class Channel:
    def __init__(self):
        self.title = ''
        self.logo  = ''
        self.streams = []

class Stream:
    def __init__(self):
        self.bitrate = ''
        self.format = ''
        self.link = ''
    
    def close(self):
        self.bitrate = int(self.bitrate)
        
    
class Radio(xml.sax.handler.ContentHandler):


    def __init__(self):
        self.in_title = 0
        self.in_logo = 0
        self.in_format = 0
        self.in_link = 0
        self.in_bitrate = 0
        self.radio = {}
 
 
    def startElement(self, name, attributes):
        if name == "channel":
            self.channel = Channel()
            self.cid = attributes["id"]
        elif name == "stream":
            self.stream = Stream()
        elif name == "title":
            self.in_title = 1
        elif name == "logo":
            self.in_logo = 1
        elif name == "format":  
            self.in_format = 1
        elif name == "link":  
            self.in_link = 1
        elif name == "bitrate":  
            self.in_bitrate = 1
            
            
    def characters(self, data):
        if self.in_title:
            self.channel.title += data
        elif self.in_logo:
            self.channel.logo += data
        elif self.in_format:
            self.stream.format += data
        elif self.in_link:
            self.stream.link += data
        elif self.in_bitrate:
            self.stream.bitrate += data  
            
            
    def endElement(self, name):
        if name == "channel":
            self.radio[self.cid] = self.channel
        elif name == "stream":
            self.stream.close()
            self.channel.streams.append(self.stream)
        elif name == "title":
            self.in_title = 0
        elif name == "logo":
            self.in_logo = 0
        elif name == "link":
            self.in_link = 0
        elif name == "format":
            self.in_format = 0
        elif name == "bitrate":
            self.in_bitrate = 0
            
            
            
            
            
            