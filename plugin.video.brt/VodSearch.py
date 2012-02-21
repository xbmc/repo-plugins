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
# encoding:utf-8
import httplib
import Config
from BeautifulSoup import BeautifulSoup

class Obj:
    def __init__(self, id, descr, name, epcount, length, epnum, cont, imgcount):
        self.id = id
        self.descr = descr
        self.name = name
        self.epcount = epcount
        self.length = length
        #self.startTime = startTime
        self.epnum = epnum
        self.cont = cont
        self.imgcount = imgcount

class GObj:
    def __init__(self, TPage, Page, Items):
        self.tpage = int(TPage)
        self.page = int(Page)
        self.items = Items

def GetItem(sID,  page=1, keyword=""):
    Items = []
    soup = BeautifulSoup(Request(sID, page, keyword))
    try:
        tpage = soup("b:totalpages")[0].text
    except:
        tpage = "1"
    try:    
        page = soup("b:pagenumber")[0].text
    except:
        page = "1"    
    d = soup("a:ondemanditem")
    for i in range(len(d)):
        c = d[i]
        sup = BeautifulSoup(c.prettify())
        name = sup("a:name")[0].text.encode('utf-8')
        descr = sup("a:description")[0].text.encode('utf-8')
        descr = descr.replace('&#xD;', '')
        epcount = sup("a:episodescount")[0].text
        length = sup("a:length")[0].text
        id = sup("a:id")[0].text
#        startTime = sup("a:item_date")[0].text
        epnum = sup("a:episodenum")[0].text    
        cont = sup("a:iscontainer")[0].text
        imgcount = sup("a:imagecount")[0].text
        Items.append(Obj(id, descr, name, epcount, length, epnum, cont, imgcount))       
    return GObj(tpage, page, Items)

def Request(sID,page, keyword):
    req = '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">' \
          '<s:Body>' \
          '<GetClientOnDemandContent xmlns="http://ivsmedia.iptv-distribution.net">' \
          '<sessionID>' + sID + '</sessionID>' \
          '<request xmlns:d4p1="http://schemas.datacontract.org/2004/07/IVS.Content.Data" xmlns:i="http://www.w3.org/2001/XMLSchema-instance">' \
          '<d4p1:filter>' \
          '<d4p1:availableOnly>false</d4p1:availableOnly>' \
          '<d4p1:contentGenre i:nil="true" />' \
          '<d4p1:contentType>VOD</d4p1:contentType>' \
          '<d4p1:date>0001-01-01T00:00:00</d4p1:date>' \
          '<d4p1:dateTill>0001-01-01T00:00:00</d4p1:dateTill>' \
          '<d4p1:favoritesOnly>false</d4p1:favoritesOnly>' \
          '<d4p1:keyWord>' + keyword.decode('utf-8') + '</d4p1:keyWord>' \
          '<d4p1:orderBy i:nil="true" />' \
          '<d4p1:showItems>true</d4p1:showItems>' \
          '<d4p1:studioID>0</d4p1:studioID>' \
          '<d4p1:visibleOnly>false</d4p1:visibleOnly>' \
          '</d4p1:filter>' \
          '<d4p1:paging xmlns:d5p1="http://schemas.datacontract.org/2004/07/IVS.Common">' \
          '<d5p1:itemsOnPage>40</d5p1:itemsOnPage>' \
          '<d5p1:pageNumber>' + str(page) + '</d5p1:pageNumber>' \
          '<d5p1:totalItems>0</d5p1:totalItems>' \
          '<d5p1:totalPages>0</d5p1:totalPages>' \
          '</d4p1:paging>' \
          '<d4p1:sort i:nil="true" />' \
          '<d4p1:type>VOD</d4p1:type>' \
          '<d4p1:requestType>SearchByName</d4p1:requestType>' \
          '</request>' \
          '</GetClientOnDemandContent>' \
          '</s:Body>' \
          '</s:Envelope>'
    req = req.encode('utf-8')
    conn = httplib.HTTPConnection('ivsmedia.iptv-distribution.net')
    conn.request('POST', Config.ContentService, req, {
            'Host': 'ivsmedia.iptv-distribution.net',                                           
            'SOAPAction': 'http://ivsmedia.iptv-distribution.net/ContentService/GetClientOnDemandContent',
            'Content-Type': 'text/xml; charset=utf-8'
     })
    response = conn.getresponse()
    return response.read()
    
    
    