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

class GetVODAddedLastWeekByUser:
    req = \
        '<?xml version="1.0" encoding="utf-8"?>' \
        '<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">' \
        '<soap:Body>' \
        '<GetVODAddedLastWeekByUser xmlns="http://www.iptv-distribution.com/ucas/">' \
        '<nDay>{Day}</nDay>' \
        '<sUserLogin>{Username}</sUserLogin>' \
        '</GetVODAddedLastWeekByUser>' \
        '</soap:Body>' \
        '</soap:Envelope>'

    programs = []
    id = None
    name = None
    description = None
    icon = None
    element = None
    day = None

    def __init__(self, Username, Password, Day):
        self.req = self.req.replace('{SiteId}', config1.siteId).replace('{AppName}', config1.appName) \
        .replace('{Username}', Username).replace('{Password}', Password).replace('{Day}', Day)
        self.day = Day

    def Request(self):
        conn = httplib.HTTPConnection('iptv-distribution.net')
        conn.request('POST', config1.vodService, self.req, {
            'SOAPAction': 'http://www.iptv-distribution.com/ucas/GetVODAddedLastWeekByUser',
            'Content-Type': 'text/xml; charset=utf-8'
        })
        response = conn.getresponse()
        data = response.read()
        
        p = xml.parsers.expat.ParserCreate()

        p.StartElementHandler = self.start_element
        p.EndElementHandler = self.end_element
        
        p.Parse(str(data))
        return self.programs

    def start_element(self, name, attrs):
        if name == 'Series':
            self.id = attrs['ID']
            self.name = (attrs['Name'] + ' ' + attrs['RecPart']).encode('utf-8')
            self.description = attrs['description'].encode('utf-8')
        if name == 'Movies' and attrs.has_key('Image'):
            self.icon = attrs['Image']
    def end_element(self, name):
        if name == 'Series':
            
            self.programs.append((self.name, self.id, self.description, self.icon))
            self.id = None
            self.name = None
            self.description = None
            self.icon = None

class GetVODStreamURL:
    req = \
        '<?xml version="1.0" encoding="utf-8"?>' \
        '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">' \
        '<soap:Body>' \
        '<GetVODStreamURL xmlns="http://www.iptv-distribution.com/ucas/">' \
        '<nVODID>{Id}</nVODID>' \
        '<sUserLogin>{Username}</sUserLogin>' \
        '<sUserPassword>{Password}</sUserPassword>' \
        '<sVideoProtocol>{Protocol}</sVideoProtocol>' \
        '</GetVODStreamURL>' \
        '</soap:Body>' \
        '</soap:Envelope>'

    streamUrl = None

    def __init__(self, Username, Password, Id):
        self.req = self.req.replace('{AppName}', config1.appName).replace('{Protocol}', config1.protocol) \
        .replace('{Username}', Username).replace('{Password}', Password).replace('{Id}', Id)

    def Request(self):
        conn = httplib.HTTPConnection('iptv-distribution.net')
        conn.request('POST', config1.vodService, self.req, {
            'SOAPAction': 'http://www.iptv-distribution.com/ucas/GetVODStreamURL',
            'Content-Type': 'text/xml; charset=utf-8'
        })
        response = conn.getresponse()
        data = response.read()

        p = xml.parsers.expat.ParserCreate()

        p.StartElementHandler = self.start_element
        p.CharacterDataHandler = self.char_data
        
        p.Parse(str(data))
        return self.streamUrl

    element = None
    def start_element(self, name, attrs):
        if name == 'GetVODStreamURLResult':
            self.streamUrl = ""
        self.element = name
    def char_data(self, data):
        if self.element == 'GetVODStreamURLResult':
            self.streamUrl += data

class GetVODGenresByUser:
    req = \
        '<?xml version="1.0" encoding="utf-8"?>' \
        '<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">' \
        '<soap:Body>' \
        '<GetVODGenresByUser xmlns="http://www.iptv-distribution.com/ucas/">' \
        '<sUserLogin>{Username}</sUserLogin>' \
        '</GetVODGenresByUser>' \
        '</soap:Body>' \
        '</soap:Envelope>'

    programs = []
    id = None
    name = None

    def __init__(self, Username):
        self.req = self.req.replace('{SiteId}', config1.siteId).replace('{AppName}', config1.appName) \
        .replace('{Username}', Username)

    def Request(self):
        conn = httplib.HTTPConnection('iptv-distribution.net')
        conn.request('POST', config1.vodService, self.req, {
            'Host': 'iptv-distribution.net',                                             
            'SOAPAction': 'http://www.iptv-distribution.com/ucas/GetVODGenresByUser',
            'Content-Type': 'text/xml; charset=utf-8'
        })
        response = conn.getresponse()
        data = response.read()
        
        p = xml.parsers.expat.ParserCreate()

        p.StartElementHandler = self.start_element
        p.EndElementHandler = self.end_element
        
        p.Parse(str(data))
        return self.programs

    def start_element(self, name, attrs):
        if name == 'Genres':
            self.id = attrs['ID']
            self.name = attrs['Name'].encode('utf-8')
    def end_element(self, name):
        if name == 'Genres':
            self.programs.append((self.name, self.id))
            self.id = None
            self.name = None

class GetVODSubGenres:
    req = \
        '<?xml version="1.0" encoding="utf-8"?>' \
        '<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">' \
        '<soap:Body>' \
        '<GetVODSubGenres xmlns="http://www.iptv-distribution.com/ucas/">' \
        '<nGenreID>{Id}</nGenreID>' \
        '</GetVODSubGenres>' \
        '</soap:Body>' \
        '</soap:Envelope>'

    programs = []
    id = None
    name = None
    description = None

    def __init__(self, Id):
        self.req = self.req.replace('{SiteId}', config1.siteId).replace('{AppName}', config1.appName) \
        .replace('{Id}', Id)

    def Request(self):
        conn = httplib.HTTPConnection('iptv-distribution.net')
        conn.request('POST', config1.vodService, self.req, {
            'SOAPAction': 'http://www.iptv-distribution.com/ucas/GetVODSubGenres',
            'Content-Type': 'text/xml; charset=utf-8'
        })
        response = conn.getresponse()
        data = response.read()

        p = xml.parsers.expat.ParserCreate()

        p.StartElementHandler = self.start_element
        p.EndElementHandler = self.end_element
        
        p.Parse(str(data))
        return self.programs
        
    def start_element(self, name, attrs):
        if name == 'SubGenres':
            self.id = attrs['ID']
            self.name = attrs['Name'].encode('utf-8')
    def end_element(self, name):
        if name == 'SubGenres':
            self.programs.append((self.name, self.id))
            self.id = None
            self.name = None

class GetVODMoviesBySubGenreUser:
    req = \
        '<?xml version="1.0" encoding="utf-8"?>' \
        '<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">' \
        '<soap:Body>' \
        '<GetVODMoviesBySubGenreUser xmlns="http://iptv-distribution.net/ds/vod/generic">' \
        '<sApplicationName>{AppName}</sApplicationName>' \
        '<bUseStbLogin>false</bUseStbLogin>' \
        '<sUserLogin>{Username}</sUserLogin>' \
        '<sUserPassword>{Password}</sUserPassword>' \
        '<nGenreId>{Id}</nGenreId>' \
        '<nPageSize>1000</nPageSize>' \
        '<nPageNumber>1</nPageNumber>' \
        '</GetVODMoviesBySubGenreUser>' \
        '</soap:Body>' \
        '</soap:Envelope>'

    programs = []
    id = None
    name = None
    description = None
    parts = 1
    rating = 0
    length = 0
    date = ""
    def __init__(self, Username, Password, Id):
        self.req = self.req.replace('{AppName}', config1.appName) \
        .replace('{Username}', Username).replace('{Password}', Password) \
        .replace('{Id}', Id)

    def Request(self):
        conn = httplib.HTTPConnection('iptv-distribution.net')
        conn.request('POST', config1.vod2Service, self.req, {
            'Host': 'iptv-distribution.net',                                                
            'SOAPAction': 'http://iptv-distribution.net/ds/vod/generic/GetVODMoviesBySubGenreUser',
            'Content-Type': 'text/xml; charset=utf-8'
        })
        response = conn.getresponse()
        data = response.read()
        
        p = xml.parsers.expat.ParserCreate()

        p.StartElementHandler = self.start_element
        p.EndElementHandler = self.end_element
        
        p.Parse(str(data))
        return sorted(self.programs, key=lambda date: date[6], reverse=True)

    def start_element(self, name, attrs):
        if name == 'Movie':
            
            self.id = attrs['Vid']
            if int(attrs['RecParts']) > 1: 
                self.name = (attrs['Name'] + '. ' + attrs['RecParts']).encode('utf-8')
            else:
                self.name = attrs['Name'].encode('utf-8')
            if 'Description' in attrs:
                self.description = attrs['Description'].encode('utf-8')
            else:
                self.description = ""    
            self.parts = int(attrs['RecParts'])
            if 'Rating' in attrs:
                self.rating = float(attrs['Rating'])
            else:
                self.rating = float(0.1)    
            if 'MovieDate' in attrs:
                self.date = attrs['MovieDate']
            else:
                self.date = "2100-09-05T23:59:59"        
            if 'Length' in attrs:
                l = int(attrs['Length'])
                self.length = str(int(l/60)) + ':' + str(l%60)
            else:
                self.length = "0:00"    
    def end_element(self, name):
        if name == 'Movie':
            self.programs.append((self.name, self.id, self.description, self.parts, self.rating, self.length, self.date))
            self.id = None
            self.name = None
            self.description = None
            self.parts = 1
            self.rating = 0
            self.length = 0
            self.date = ""

class GetVODSeries:
    req = \
        '<?xml version="1.0" encoding="utf-8"?>' \
        '<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">' \
        '<soap:Body>' \
        '<GetVODSeries xmlns="http://iptv-distribution.net/ds/vod/generic">' \
        '<sApplicationName>{AppName}</sApplicationName>' \
        '<nMovieID>{Id}</nMovieID>' \
        '<bUseStbLogin>false</bUseStbLogin>' \
        '<sUserLogin>{Username}</sUserLogin>' \
        '<sUserPassword>{Password}</sUserPassword>' \
        '</GetVODSeries>' \
        '</soap:Body>' \
        '</soap:Envelope>'

    programs = []
    id = None
    name = None
    description = None
    parts = 1

    def __init__(self, Username, Password, Id):
        self.req = self.req.replace('{AppName}', config1.appName) \
        .replace('{Username}', Username).replace('{Password}', Password) \
        .replace('{Id}', Id)

    def Request(self):
        conn = httplib.HTTPConnection('iptv-distribution.net')
        conn.request('POST', config1.vod2Service, self.req, {
            'SOAPAction': 'http://iptv-distribution.net/ds/vod/generic/GetVODSeries',
            'Content-Type': 'text/xml; charset=utf-8'
        })
        response = conn.getresponse()
        data = response.read()

        p = xml.parsers.expat.ParserCreate()

        p.StartElementHandler = self.start_element
        p.EndElementHandler = self.end_element
        
        p.Parse(str(data))
        return self.programs

    def start_element(self, name, attrs):
        if name == 'Movie':
            self.id = attrs['Vid']
            if 'Description' in attrs:
                self.description = attrs['Description'].encode('utf-8')
            else:
                self.description = ''
            self.parts = int(attrs['RecParts'])
            if self.parts > 1:
                self.name = (attrs['Name'] + ' ' + attrs['RecParts']).encode('utf-8')
            else:
                self.name = (attrs['Name'] + ' ' + attrs['RecPart']).encode('utf-8')
    def end_element(self, name):
        if name == 'Movie':
            self.programs.append((self.name, self.id, self.description, self.parts))
            self.id = None
            self.name = None
            self.description = None
            self.parts = 1

class GetVODMoviesNewInVODByUser:
    req = \
        '<?xml version="1.0" encoding="utf-8"?>' \
        '<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">' \
        '<soap:Body>' \
        '<GetVODMoviesNewInVODByUser xmlns="http://iptv-distribution.net/ds/vod/generic">' \
        '<sApplicationName>{AppName}</sApplicationName>' \
        '<bUseStbLogin>false</bUseStbLogin>' \
        '<sUserLogin>{Username}</sUserLogin>' \
        '<sUserPassword>{Password}</sUserPassword>' \
        '<nPageSize>100</nPageSize>' \
        '<nPageNumber>1</nPageNumber>' \
        '</GetVODMoviesNewInVODByUser>' \
        '</soap:Body>' \
        '</soap:Envelope>'

    programs = []
    id = None
    name = None
    description = None
    date = ""
    def __init__(self, Username, Password):
        self.req = self.req.replace('{AppName}', config1.appName) \
        .replace('{Username}', Username).replace('{Password}', Password)

    def Request(self):
        conn = httplib.HTTPConnection('iptv-distribution.net')
        conn.request('POST', config1.vod2Service, self.req, {
            'Host': 'iptv-distribution.net',                                                
            'SOAPAction': 'http://iptv-distribution.net/ds/vod/generic/GetVODMoviesNewInVODByUser',
            'Content-Type': 'text/xml; charset=utf-8'
        })
        response = conn.getresponse()
        data = response.read()
        
        p = xml.parsers.expat.ParserCreate()

        p.StartElementHandler = self.start_element
        p.EndElementHandler = self.end_element
        
        p.Parse(str(data))
        return sorted(self.programs, key=lambda prog: prog[3], reverse=True)

    def start_element(self, name, attrs):
        if name == 'Movie':
            self.id = attrs['Vid']
            self.name = attrs['Name'].encode('utf-8')
            self.description = attrs['Description'].encode('utf-8')
            if 'MovieDate' in attrs:
                self.date = attrs['MovieDate']
            else:
                self.date = "2100-09-05T23:59:59"
    def end_element(self, name):
        if name == 'Movie':
            self.programs.append((self.name, self.id, self.description, self.date))
            self.id = None
            self.name = None
            self.description = None

class GetVODMoviesTOP100ByUser:
    req = \
        '<?xml version="1.0" encoding="utf-8"?>' \
        '<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">' \
        '<soap:Body>' \
        '<GetVODMoviesTOP100ByUser xmlns="http://iptv-distribution.net/ds/vod/generic">' \
        '<sApplicationName>{AppName}</sApplicationName>' \
        '<bUseStbLogin>false</bUseStbLogin>' \
        '<sUserLogin>{Username}</sUserLogin>' \
        '<sUserPassword>{Password}</sUserPassword>' \
        '<nPageSize>100</nPageSize>' \
        '<nPageNumber>1</nPageNumber>' \
        '</GetVODMoviesTOP100ByUser>' \
        '</soap:Body>' \
        '</soap:Envelope>'

    programs = []
    id = None
    name = None
    description = None
    rating = 0
    def __init__(self, Username, Password):
        self.req = self.req.replace('{AppName}', config1.appName) \
        .replace('{Username}', Username).replace('{Password}', Password)

    def Request(self):
        conn = httplib.HTTPConnection('iptv-distribution.net')
        conn.request('POST', config1.vod2Service, self.req, {
            'SOAPAction': 'http://iptv-distribution.net/ds/vod/generic/GetVODMoviesTOP100ByUser',
            'Content-Type': 'text/xml; charset=utf-8'
        })
        response = conn.getresponse()
        data = response.read()
        
        p = xml.parsers.expat.ParserCreate()

        p.StartElementHandler = self.start_element
        p.EndElementHandler = self.end_element
        
        p.Parse(str(data))
        return sorted(self.programs, key=lambda prog: prog[3], reverse=True)

    def start_element(self, name, attrs):
        if name == 'Movie':
            self.id = attrs['Vid']
            self.name = attrs['Name'].encode('utf-8')
            self.description = attrs['Description'].encode('utf-8')
            if 'Rating' in attrs:
                self.rating = float(attrs['Rating'])
            else:
                self.rating = float(0.1)
    def end_element(self, name):
        if name == 'Movie':
            self.programs.append((self.name, self.id, self.description, self.rating))
            self.id = None
            self.name = None
            self.description = None
            self.rating
