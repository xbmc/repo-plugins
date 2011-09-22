
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
import config

class GetChannels:
    req = \
        '<?xml version="1.0" encoding="utf-8"?>' \
        '<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">' \
        '<soap:Body>' \
        '<GetChannels xmlns="http://iptv-distribution.net/ds/epg">' \
        '<sApplicationName>{AppName}</sApplicationName>' \
        '<TVChannelRequest>' \
        '<IconTypeID>1</IconTypeID>' \
        '<ClientCredentials>' \
        '<SiteID>{SiteId}</SiteID>' \
        '<UseStbLogin>false</UseStbLogin>' \
        '<UserLogin>{Username}</UserLogin>' \
        '<UserPassword>{Password}</UserPassword>' \
        '</ClientCredentials>' \
        '</TVChannelRequest>' \
        '</GetChannels>' \
        '</soap:Body>' \
        '</soap:Envelope>'

    channels = []
    id = ""
    name = ""
    icon = ""
    element = None

    def __init__(self, Username, Password):
        self.req = self.req.replace('{SiteId}', config.siteId).replace('{AppName}', config.appName) \
        .replace('{Username}', Username).replace('{Password}', Password)

    def Request(self):
        conn = httplib.HTTPConnection(config.server)
        conn.request('POST', config.epgService, self.req, {
            'SOAPAction': 'http://iptv-distribution.net/ds/epg/GetChannels',
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
        if name == 'TVChannelResponse':
            self.id = ""
            self.name = ""
            self.icon = ""
        self.element = name
    def end_element(self, name):
        if name == 'TVChannelResponse':
            self.channels.append((str(len(self.channels) + 1).zfill(2) + '. ' + self.name, self.id, self.icon))
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

class GetLiveStream:
    req = \
        '<?xml version="1.0" encoding="utf-8"?>' \
        '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">' \
        '<soap:Body>' \
        '<GetTVStream xmlns="http://iptv-distribution.net/ds/cas/streams/generic">' \
        '<sApplicationName>{AppName}</sApplicationName>' \
        '<nChannelID>{Channel}</nChannelID>' \
        '<bUseStbLogin>false</bUseStbLogin>' \
        '<sUserLogin>{Username}</sUserLogin>' \
        '<sUserPassword>{Password}</sUserPassword>' \
        '<StreamProtocol>{Protocol}</StreamProtocol>' \
        '</GetTVStream>' \
        '</soap:Body>' \
        '</soap:Envelope>'

    streamUrl = None

    def __init__(self, Username, Password, Channel):
        self.req = self.req.replace('{AppName}', config.appName).replace('{Protocol}', config.protocol) \
        .replace('{Username}', Username).replace('{Password}', Password).replace('{Channel}', Channel)

    def Request(self):
        conn = httplib.HTTPConnection(config.server)
        conn.request('POST', config.streamService, self.req, {
            'SOAPAction': 'http://iptv-distribution.net/ds/cas/streams/generic/GetTVStream',
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
        if name == 'GetTVStreamResult':
            self.streamUrl = ""
        self.element = name
    def char_data(self, data):
        if self.element == 'GetTVStreamResult':
            self.streamUrl += data
