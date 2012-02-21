# coding=utf-8
#
# <BestRussianTV plugin for XBMC>
# Copyright (C) <2011>  <BestRussianTV>
#
#       This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import httplib, urllib, urllib2, re
import xml.parsers.expat
import config1

class Parser:
    streams = []
    url = None
    
    def parseUrl(self, url):
        asx = urllib2.urlopen(url)
        data = asx.read()
        return self.parseString(data)
    
    def parseString(self, data):
        p = xml.parsers.expat.ParserCreate()
        p.StartElementHandler = self.start_element
        p.EndElementHandler = self.end_element

        p.Parse(str(data))
        return self.streams
        
    def start_element(self, name, attrs):
        if name == 'Ref' or name == 'REF':
            href = None
            if 'HREF' in attrs:
                href = attrs['HREF']
            if 'href' in attrs:
                href = attrs['href']
            if href != None and (href.startswith('mms://') or href.startswith('rtsp://')):
                self.url = href
    
    def end_element(self, name):
        if name == 'Ref' or name == 'REF':
            if self.url != None:
                self.streams.append(self.url)
            
