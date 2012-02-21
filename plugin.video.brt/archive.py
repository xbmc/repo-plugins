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

class GetChannels:
    req = \
        '<?xml version="1.0" encoding="utf-8"?>' \
        '<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">' \
        '<soap:Body>' \
        '<GetPVRChannels xmlns="http://iptv-distribution.net/ds/epg">' \
        '<sApplicationName>{AppName}</sApplicationName>' \
        '<sUserLogin>{Username}</sUserLogin>' \
        '<sUserPassword>{Password}</sUserPassword>' \
        '</GetPVRChannels>' \
        '</soap:Body>' \
        '</soap:Envelope>'

    channels = []
    id = ""
    name = ""
    icon = ""
    element = None

    def __init__(self, Username, Password):
        self.req = self.req.replace('{SiteId}', config1.siteId).replace('{AppName}', config1.appName) \
        .replace('{Username}', Username).replace('{Password}', Password)

    def Request(self):
        conn = httplib.HTTPConnection('iptv-distribution.net')
        conn.request('POST', config1.epgService, self.req, {
                                                        
            'SOAPAction': 'http://iptv-distribution.net/ds/epg/GetPVRChannels',
            'Content-Type': 'text/xml; charset=utf-8'
        })
        response = conn.getresponse()
        data = response.read()

        p = xml.parsers.expat.ParserCreate()

        p.StartElementHandler = self.start_element
        p.EndElementHandler = self.end_element
        p.CharacterDataHandler = self.char_data
        
        p.Parse(str(data))
        return self.channels

    def start_element(self, name, attrs):
        #print 'Start element:', name, attrs
        if name == 'TVChannelData':
            self.id = ""
            self.name = ""
            self.icon = ""
        self.element = name
    def end_element(self, name):
        if name == 'TVChannelData':
            temp = str(len(self.channels) + 1).zfill(2) + '. ' + self.name
            #temp = temp.encode('utf-8')
            self.channels.append((temp, self.id, self.icon))
            self.id = None
            self.name = None
    def char_data(self, data):
        if data.strip():
            data = data.encode('utf-8')
            if self.element == 'ID':
                self.id += data
            elif self.element == 'Name':
                self.name += data
            elif self.element == 'IconURL':
                self.icon += data

class GetPVREPG:
    req = \
        '<?xml version="1.0" encoding="utf-8"?>' \
        '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">' \
        '<soap:Body>' \
        '<GetPVREPG xmlns="http://iptv-distribution.net/ds/epg">' \
        '<sApplicationName>{AppName}</sApplicationName>' \
        '<dtStart>{Date}</dtStart>' \
        '<nPeriod>1440</nPeriod>' \
        '<nChannelID>{Channel}</nChannelID>' \
        '<sUserLogin>{Username}</sUserLogin>' \
        '<sUserPassword>{Password}</sUserPassword>' \
        '</GetPVREPG>' \
        '</soap:Body>' \
        '</soap:Envelope>'

    programs = []
    start = None
    id = None
    name = None
    description = None
    isWatchable = None
    element = None
    
    def __init__(self, Username, Password, Channel, Date):
        self.req = self.req.replace('{AppName}', config1.appName) \
        .replace('{Username}', Username).replace('{Password}', Password) \
        .replace('{Channel}', Channel).replace('{Date}', Date)				

    def Request(self):
        conn = httplib.HTTPConnection('iptv-distribution.net', 80)
        conn.request('POST', config1.epgService, self.req, {
            'Host' : 'iptv-distribution.net',                                                
            'SOAPAction': 'http://iptv-distribution.net/ds/epg/GetPVREPG',
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
        if name == 'TVProgramData':
            self.id = attrs['TvGuideID']
            self.name = attrs['TvProgramName']
            # description is not returned by the service
            self.description = ""
            #self.description = attrs['Description']#.encode('utf-8')
            self.start = attrs['Date'][11:16].encode('utf-8')
            self.isWatchable = attrs['IsWatchable']
    def end_element(self, name): 
        if name == 'TVProgramData' and self.isWatchable != 'false':
            test = self.start + ' ' + self.name
            test = test.encode('utf-8')
            self.programs.append((test, self.id, self.description))
            self.id = None
            self.start = None
            self.name = None
            self.description = None

class GetArchStream:
    req = \
        '<?xml version="1.0" encoding="utf-8"?>' \
        '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">' \
        '<soap:Body>' \
        '<GetPVRStreamURL xmlns="http://www.iptv-distribution.com/ucas/">' \
        '<nPVRID>{Program}</nPVRID>' \
        '<sUserLogin>{Username}</sUserLogin>' \
        '<sUserPassword>{Password}</sUserPassword>' \
        '<sVideoProtocol>{Protocol}</sVideoProtocol>' \
        '</GetPVRStreamURL>' \
        '</soap:Body>' \
        '</soap:Envelope>'

    streamUrl = None

    def __init__(self, Username, Password, Program):
        self.req = self.req.replace('{AppName}', config1.appName).replace('{Protocol}', config1.protocol) \
        .replace('{Username}', Username).replace('{Password}', Password).replace('{Program}', Program)

    def Request(self):
        conn = httplib.HTTPConnection('iptv-distribution.net', 80)
        conn.request('POST', config1.vodService, self.req, {
            'Host': 'iptv-distribution.net',
            'SOAPAction': 'http://www.iptv-distribution.com/ucas/GetPVRStreamURL',
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
        if name == 'GetPVRStreamURLResult':
            self.streamUrl = ""
        self.element = name
    def char_data(self, data):
        if self.element == 'GetPVRStreamURLResult':
            self.streamUrl += data

class GetPvrPlaylist:
    req = \
        '<?xml version="1.0" encoding="utf-8"?>' \
        '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">' \
        '<soap:Body>' \
        '<GetPvrPlaylist xmlns="http://iptv-distribution.net/ds/cas/streams/generic">' \
        '<sApplicationName>{AppName}</sApplicationName>' \
        '<nPvrID>{Program}</nPvrID>' \
        '<bUseStbLogin>false</bUseStbLogin>' \
        '<sUserLogin>{Username}</sUserLogin>' \
        '<sUserPassword>{Password}</sUserPassword>' \
        '<nStartOffset>0</nStartOffset>' \
        '<StreamProtocol>{Protocol}</StreamProtocol>' \
        '</GetPvrPlaylist>' \
        '</soap:Body>' \
        '</soap:Envelope>'

    streamUrl = None

    def __init__(self, Username, Password, Program):
        self.req = self.req.replace('{AppName}', config1.appName).replace('{Protocol}', config1.protocol) \
        .replace('{Username}', Username).replace('{Password}', Password).replace('{Program}', Program)

    def Request(self):
        conn = httplib.HTTPConnection(config1.server)
        conn.request('POST', config1.streamService, self.req, {
            'SOAPAction': 'http://iptv-distribution.net/ds/cas/streams/generic/GetPvrPlaylist',
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
        if name == 'GetPvrPlaylistResult':
            self.streamUrl = ""
        self.element = name
    def char_data(self, data):
        if self.element == 'GetPvrPlaylistResult':
            self.streamUrl += data
