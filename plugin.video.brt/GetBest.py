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
import httplib
import config1
from BeautifulSoup import BeautifulSoup

class Obj:
    def __init__(self, id, descr, name, epcount, length, startTime, epnum, cont, imgcount):
        self.id = id
        self.descr = descr
        self.name = name
        self.epcount = epcount
        self.length = length
        self.startTime = startTime
        self.epnum = epnum
        self.cont = cont
        self.imgcount = imgcount

def GetItem(sID, d):
    Items = []
    soup = BeautifulSoup(Request(sID, d))
    d = soup("a:programguideitem")
    for i in range(len(d)):
        c = d[i]
        sup = BeautifulSoup(c.prettify())
        name = sup("a:name")[0].text.encode('utf-8')
        descr = sup("a:description")[0].text.encode('utf-8')
        descr = descr.replace('&#xD;', '')
        epcount = sup("a:episodescount")[0].text
        length = sup("a:length")[0].text
        id = sup("a:id")[0].text
        startTime = sup("a:starttime")[0].text
        epnum = sup("a:episodenum")[0].text	
        cont = sup("a:iscontainer")[0].text
        imgcount = sup("a:imagecount")[0].text
        Items.append(Obj(id, descr, name, epcount, length, startTime, epnum, cont, imgcount))	   
    return Items

def Request(sID,  d):
    if d == 1:
        tim = 'TopHundredWatchedWeek'
    elif d == 2:
        tim = 'TopHundredWatchedMonth'
    elif d == 3:
        tim = 'TopHundredWatched'
    req = \
        '<?xml version="1.0" encoding="utf-8"?>' \
        '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body><GetClientProgramGuide xmlns="http://ivsmedia.iptv-distribution.net"><sessionID>{sessionID}</sessionID><type>ArcPlus</type>' \
        '<request xmlns:d4p1="http://schemas.datacontract.org/2004/07/IVS.Content.Data" xmlns:i="http://www.w3.org/2001/XMLSchema-instance">' \
        '<d4p1:filter><d4p1:availableOnly>true</d4p1:availableOnly><d4p1:contentGenre i:nil="true" /><d4p1:contentType>ArcPlus</d4p1:contentType><d4p1:date>0001-01-01T00:00:00</d4p1:date><d4p1:dateTill>0001-01-01T00:00:00</d4p1:dateTill>' \
        '<d4p1:favoritesOnly>false</d4p1:favoritesOnly><d4p1:keyWord i:nil="true" /><d4p1:orderBy i:nil="true" /><d4p1:showItems>true</d4p1:showItems><d4p1:studioID>0</d4p1:studioID><d4p1:visibleOnly>false</d4p1:visibleOnly></d4p1:filter>' \
        '<d4p1:paging xmlns:d5p1="http://schemas.datacontract.org/2004/07/IVS.Common"><d5p1:itemsOnPage>100</d5p1:itemsOnPage><d5p1:pageNumber>1</d5p1:pageNumber><d5p1:totalItems>0</d5p1:totalItems><d5p1:totalPages>0</d5p1:totalPages>' \
        '</d4p1:paging><d4p1:sort><d4p1:contentType>ArcPlus</d4p1:contentType><d4p1:fields xmlns:d6p1="http://schemas.datacontract.org/2004/07/IVS.Common" i:nil="true" /><d4p1:orderBy i:nil="true" />' \
        '<d4p1:orderDirection>date DESC</d4p1:orderDirection></d4p1:sort><d4p1:type>ArcPlus</d4p1:type><d4p1:requestType>{Tim}</d4p1:requestType><d4p1:channelID>0</d4p1:channelID>' \
        '<d4p1:fromTime>0001-01-01T00:00:00</d4p1:fromTime><d4p1:itemCountAfter>0</d4p1:itemCountAfter><d4p1:itemCountBefore>0</d4p1:itemCountBefore><d4p1:streamZone i:nil="true" />' \
        '<d4p1:streamZoneUTCOffset>0</d4p1:streamZoneUTCOffset><d4p1:tillTime>0001-01-01T00:00:00</d4p1:tillTime><d4p1:watchingZone i:nil="true" /><d4p1:watchingZoneUTCOffset>0</d4p1:watchingZoneUTCOffset>' \
        '</request></GetClientProgramGuide></s:Body></s:Envelope>'
    req = req.replace('{sessionID}', sID).replace('{Tim}', tim)	
    conn = httplib.HTTPConnection(config1.server)
    conn.request('POST', config1.ContentService, req, {
            'SOAPAction': 'http://ivsmedia.iptv-distribution.net/ContentService/GetClientProgramGuide',
            'Content-Type': 'text/xml; charset=utf-8'
    })
    response = conn.getresponse()
    return response.read()    		