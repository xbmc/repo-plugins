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
import Content, Common, Config
import httplib, time, datetime
from BeautifulSoup import BeautifulSoup


try:
    # new XBMC 10.05 addons:
    import xbmcaddon
except ImportError:
    # old XBMC - create fake xbmcaddon module with same interface as new XBMC 10.05
    class xbmcaddon:
        """ fake xbmcaddon module """
        __version__ = "(old XBMC)"
        class Addon:
            """ fake xbmcaddon.Addon class """
            def __init__(self, id):
                self.id = id

            def getSetting(self, key):
                return xbmcplugin.getSetting(key)

            def openSettings(self):
                xbmc.openSettings()
            def setSetting(self, key, value):
                return xbmcplugin.setSetting(key, value)

addon = xbmcaddon.Addon("plugin.video.brt")


quality = ['HQ', 'SQ']
q = int(addon.getSetting('quality'))
region = ['EU_RST', 'NA_PST', 'NA_EST','AU_EST']
offset = [240,-480,-300,600]

re = int(addon.getSetting('region'))

server = ['1','7']
s = int(addon.getSetting('server'))




request = '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body>{BODY}</s:Body></s:Envelope>'
host = 'ivsmedia.iptv-distribution.net'
proxy = 'ivsmedia.iptv-distribution.net'
port = 80

def GetUTC():
    req = '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">' \
          '<s:Body>' \
          '<GetCurrentUtcTime xmlns="http://ivsmedia.iptv-distribution.net" />' \
          '</s:Body>' \
          '</s:Envelope>'
    conn = httplib.HTTPConnection(proxy, port)
    conn.request('POST', Config.MediaService, req, {
            'Host': host,                                          
            'SOAPAction': 'http://' + host + '/MediaService/GetCurrentUtcTime',
            'Content-Type': 'text/xml; charset=utf-8'
    })
    response = conn.getresponse()
    soup = BeautifulSoup(response.read())
    d = soup('getcurrentutctimeresult')[0].text
    dat = datetime.datetime.fromtimestamp(time.mktime(time.strptime(d[:19], '%Y-%m-%dT%H:%M:%S')))
    timedelta1 = datetime.timedelta(minutes=offset[re])
    dat = dat +  timedelta1
    return dat

class PlNow:
    def __init__(self,name,timed, description):
        self.name = name
        self.time = timed
        self.description = description
def NowPlay(SessionID, channelID, dat):
    datnow = dat.strftime('%Y-%m-%dT%H:%M:%S')
    timedelta = datetime.timedelta(hours=4)
    datfour = (dat - timedelta).strftime('%Y-%m-%dT%H:%M:%S')
    req = '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">' \
          '<s:Body>' \
          '<GetClientProgramGuide xmlns="http://ivsmedia.iptv-distribution.net">' \
          '<sessionID>' + SessionID + '</sessionID>' \
          '<type>AudioBooks</type>' \
          '<request xmlns:d4p1="http://schemas.datacontract.org/2004/07/IVS.Content.Data" xmlns:i="http://www.w3.org/2001/XMLSchema-instance">' \
          '<d4p1:filter>' \
          '<d4p1:availableOnly>false</d4p1:availableOnly>' \
          '<d4p1:contentGenre i:nil="true" />' \
          '<d4p1:contentType>LiveTV</d4p1:contentType>' \
          '<d4p1:date>' + datfour + '</d4p1:date>' \
          '<d4p1:dateTill>' + datnow + '</d4p1:dateTill>' \
          '<d4p1:favoritesOnly>false</d4p1:favoritesOnly>' \
          '<d4p1:keyWord i:nil="true" />' \
          '<d4p1:orderBy i:nil="true" />' \
          '<d4p1:showItems>false</d4p1:showItems>' \
          '<d4p1:studioID>0</d4p1:studioID>' \
          '<d4p1:visibleOnly>false</d4p1:visibleOnly>' \
          '</d4p1:filter>' \
          '<d4p1:paging xmlns:d5p1="http://schemas.datacontract.org/2004/07/IVS.Common" i:nil="true" />' \
          '<d4p1:sort i:nil="true" />' \
          '<d4p1:type>LiveTV</d4p1:type>' \
          '<d4p1:requestType>Today</d4p1:requestType>' \
          '<d4p1:channelID>' + channelID + '</d4p1:channelID>' \
          '<d4p1:fromTime>0001-01-01T00:00:00</d4p1:fromTime>' \
          '<d4p1:itemCountAfter>0</d4p1:itemCountAfter>' \
          '<d4p1:itemCountBefore>0</d4p1:itemCountBefore>' \
          '<d4p1:streamZone>' + region[re] + '</d4p1:streamZone>' \
          '<d4p1:streamZoneUTCOffset>0</d4p1:streamZoneUTCOffset>' \
          '<d4p1:tillTime>0001-01-01T00:00:00</d4p1:tillTime>' \
          '<d4p1:watchingZone>' + region[re] + '</d4p1:watchingZone>' \
          '<d4p1:watchingZoneUTCOffset>0</d4p1:watchingZoneUTCOffset>' \
          '</request>' \
          '</GetClientProgramGuide>' \
          '</s:Body>' \
          '</s:Envelope>'
    conn = httplib.HTTPConnection(proxy, port)
    conn.request('POST', Config.ContentService, req, {
            'Host': host,                                          
            'SOAPAction': 'http://' + host + '/ContentService/GetClientProgramGuide',
            'Content-Type': 'text/xml; charset=utf-8'
    })
    response = conn.getresponse()
    str = response.read()
    str  = str.replace('<a:description/>', '<a:description></a:description>')
    soup = BeautifulSoup(str)
    timed = ''
    name = ''
    description = ''    
    try:
     items = soup("a:programguideitem")

     for item in items:
        
        
        
        sup = BeautifulSoup(item.prettify())
        if sup('a:playingnow')[0].text == 'true':
            timed = sup('a:starttime')[0].text
            timed = timed[11:]
            timed = timed[:5].encode('utf-8')
            name = sup('a:name')[0].text.encode('utf-8')
            try:
                description = sup('a:description')[0].text.encode('utf-8')
            except: pass    
    except: pass
    return PlNow(name, timed, description)
         

def GetClientChannel(SessionID='', filAvailable = 'false', genChild = [], genCode = '', genType = 'UnknownGenreType', genId = '0', genCount = '0', genName = '', genPar = '0', filType = 'AudioBooks', filDate = '0001-01-01T00:00:00', filDateTill = '0001-01-01T00:00:00', filFavor = 'false', filKey = '', filOrder = '', filShow = 'false', filStud = '0', filVisible = 'false', pagItems = '0', pagNum = '0', pagTItems = '0', pagTPage = '0', sortType = 'AudioBooks', sortField = [], sortOBy = '', sortODir = '', type = 'AudioBooks'):
    body = '<GetClientChannels xmlns="http://ivsmedia.iptv-distribution.net"><sessionID>' + SessionID + '</sessionID>'
    req = Content.ContentRequest()
    fil = Content.ContentFilter()
    pag = Common.ItemPaging()
    sort = Content.ContentSort()
    genre = Content.ContentGenre()
    genre.childrenIDs = genChild
    genre.code = genCode
    genre.genreType = genType
    genre.id = genId
    genre.itemCount = genCount
    genre.parentID = genPar
    fil.availableOnly = filAvailable
    fil.contentGenre = genre
    fil.contentType = filType
    fil.date = filDate
    fil.dateTill = filDateTill
    fil.favoritesOnly = filFavor
    fil.keyWord = filKey
    fil.orderBy = filOrder
    fil.showItems = filShow
    fil.studioID = filStud
    fil.visibleOnly = filVisible
    pag.itemsOnPage = pagItems
    pag.pageNumber = pagNum
    pag.totalItems = pagTItems
    pag.totalPages = pagTPage
    sort.contentType = sortType
    sort.fields = sortField
    sort.orderBy = sortOBy
    sort.orderDirection = sortODir
    req.filter = fil
    req.paging = pag
    req.sort = sort
    req.type = type
    body = body + req.get() + '</GetClientChannels>'
    body = request.replace('{BODY}', body)
    return Request(body, 'GetClientChannels')


class ObjGenres:
    def __init__(self, code, type, id, count, name, parent):
        self.code = code
        self.type = type
        self.id = id
        self.count = count
        self.name = name
        self.parent = parent
  
def GetClientGenres(str, coun):    
    Items = []
    soup = BeautifulSoup(str)
    d = soup("a:contentgenre")
    for i in range(len(d)):
        if len(d[i]) == 1:
            c = d[i].contents[0]
            sup = BeautifulSoup(c.prettify())
            name = sup("a:name")[0].text.encode('utf-8')
            code = sup("a:code")[0].text
            type = sup("a:genretype")[0].text
            id = sup("a:id")[0].text
            count = sup("a:itemcount")[0].text
            parent = sup("a:parentid")[0].text
        else:
            c = d[i]
            sup = BeautifulSoup(c.prettify())
            name = sup("a:name")[0].text.encode('utf-8')
            code = sup("a:code")[0].text
            type = sup("a:genretype")[0].text
            id = sup("a:id")[0].text
            count = sup("a:itemcount")[0].text
            parent = sup("a:parentid")[0].text            
        if parent == coun:
            Items.append(ObjGenres(code, type, id, count, name, parent))       
    return Items

def GenreRequest(sID, type):
     gtype = ['ArcplusGenreType', 'VodGenreType']
     i = int(type)
     req = \
        '<?xml version="1.0" encoding="utf-8"?>' \
        '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body><GetClientContentGenres xmlns="http://ivsmedia.iptv-distribution.net"><sessionID>{sessionID}</sessionID><type>{GTYPE}</type></GetClientContentGenres></s:Body></s:Envelope>'
     req = req.replace('{sessionID}', sID).replace('{GTYPE}',gtype[i])        
     conn = httplib.HTTPConnection(proxy, port)
     conn.request('POST', Config.ContentService, req, {
            'Host': host,                                          
            'SOAPAction': 'http://' + host + '/ContentService/GetClientContentGenres',
            'Content-Type': 'text/xml; charset=utf-8'
     })
     response = conn.getresponse()
     return response.read()



def Request(str, action):
    conn = httplib.HTTPConnection(proxy, port)
    conn.request('POST', Config.ContentService, str, {
           'Host': host,
           'SOAPAction': 'http://' + host + '/ContentService/' + action,
           'Content-Type': 'text/xml; charset=utf-8'
          
           })                                            
    response = conn.getresponse()
    data = response.read()
    return data


class PrObj:
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

class PrGuideObj:
    def __init__(self, TPage, Page, Items):
        self.tpage = int(TPage)
        self.page = int(Page)
        self.items = Items

def GetClientProgramGuide(sID, ID, type, rtype="0", page=1):
    Items = []
    soup = BeautifulSoup(PrRequest(sID, ID, type, rtype, page))
    try:
        tpage = soup("b:totalpages")[0].text
    except:
        tpage = "1"
    try:    
        page = soup("b:pagenumber")[0].text
    except:
        page = "1"    
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
        Items.append(PrObj(id, descr, name, epcount, length, startTime, epnum, cont, imgcount))       
    return PrGuideObj(tpage, page, Items)

def PrRequest(sID, ID, type, rtype, page):
    gtype = ['ArcplusGenreType','VodGenreType']
    ctype = ['ArcPlus','Vod']
    reqtype = ['AllItems','TopHundredWatchedWeek','TopHundredWatchedMonth','TopHundredWatchedYear']
    t = int(type)
    r = int(rtype)    
    
    req = \
        '<?xml version="1.0" encoding="utf-8"?>' \
        '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body><GetClientProgramGuide xmlns="http://ivsmedia.iptv-distribution.net"><sessionID>{sessionID}</sessionID><type>{CTYPE}</type>' \
        '<request xmlns:d4p1="http://schemas.datacontract.org/2004/07/IVS.Content.Data" xmlns:i="http://www.w3.org/2001/XMLSchema-instance">' \
        '<d4p1:filter><d4p1:availableOnly>true</d4p1:availableOnly><d4p1:contentGenre><d4p1:childrenIDs xmlns:d7p1="http://schemas.microsoft.com/2003/10/Serialization/Arrays" />' \
        '<d4p1:code i:nil="true" /><d4p1:genreType>{GTYPE}</d4p1:genreType><d4p1:id>{ID}</d4p1:id><d4p1:itemCount>0</d4p1:itemCount><d4p1:name i:nil="true" /><d4p1:parentID>0</d4p1:parentID></d4p1:contentGenre>' \
        '<d4p1:contentType>{CTYPE}</d4p1:contentType><d4p1:date>0001-01-01T00:00:00</d4p1:date><d4p1:dateTill>0001-01-01T00:00:00</d4p1:dateTill><d4p1:favoritesOnly>false</d4p1:favoritesOnly><d4p1:keyWord i:nil="true" />' \
        '<d4p1:orderBy>name ASC</d4p1:orderBy><d4p1:showItems>false</d4p1:showItems><d4p1:studioID>0</d4p1:studioID><d4p1:visibleOnly>false</d4p1:visibleOnly></d4p1:filter>' \
        '<d4p1:paging xmlns:d5p1="http://schemas.datacontract.org/2004/07/IVS.Common"><d5p1:itemsOnPage>40</d5p1:itemsOnPage><d5p1:pageNumber>{PageNum}</d5p1:pageNumber><d5p1:totalItems>0</d5p1:totalItems><d5p1:totalPages>0</d5p1:totalPages>' \
        '</d4p1:paging><d4p1:sort><d4p1:contentType>{CTYPE}</d4p1:contentType><d4p1:fields xmlns:d6p1="http://schemas.datacontract.org/2004/07/IVS.Common" i:nil="true" /><d4p1:orderBy i:nil="true" /><d4p1:orderDirection></d4p1:orderDirection>' \
        '</d4p1:sort><d4p1:type>{CTYPE}</d4p1:type><d4p1:requestType>{RTYPE}</d4p1:requestType><d4p1:channelID>0</d4p1:channelID><d4p1:fromTime>0001-01-01T00:00:00</d4p1:fromTime><d4p1:itemCountAfter>0</d4p1:itemCountAfter>' \
        '<d4p1:itemCountBefore>0</d4p1:itemCountBefore><d4p1:streamZone>' + region[re] + '</d4p1:streamZone><d4p1:streamZoneUTCOffset>0</d4p1:streamZoneUTCOffset><d4p1:tillTime>0001-01-01T00:00:00</d4p1:tillTime><d4p1:watchingZone></d4p1:watchingZone>' \
        '<d4p1:watchingZoneUTCOffset>0</d4p1:watchingZoneUTCOffset></request></GetClientProgramGuide></s:Body></s:Envelope>'
    req = req.replace('{sessionID}', sID).replace('{ID}', ID).replace('{RTYPE}',reqtype[r]).replace('{GTYPE}',gtype[t]).replace('{CTYPE}', ctype[t]).replace('{PageNum}',str(page))    
    conn = httplib.HTTPConnection(proxy, port)
    conn.request('POST', Config.ContentService, req, {
            'Host': host,                                         
            'SOAPAction': 'http://ivsmedia.iptv-distribution.net/ContentService/GetClientProgramGuide',
            'Content-Type': 'text/xml; charset=utf-8'
     })
    response = conn.getresponse()
    return response.read()

class RelObj:
    def __init__(self, id, descr, name, length, startTime, epnum, cont, imgcount):
        self.id = id
        self.descr = descr
        self.name = name
        self.length = length
        self.startTime = startTime
        self.epnum = epnum
        self.cont = cont
        self.imgcount = imgcount

class RelGObj:
    def __init__(self, TPage, Page, Items):
        self.tpage = int(TPage)
        self.page = int(Page)
        self.items = Items

def RelRequest(sID, ID, page):
     req = '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body><GetClientRelatedProgramGuide xmlns="http://ivsmedia.iptv-distribution.net"><sessionID>{sessionID}</sessionID>' \
           '<request xmlns:d4p1="http://schemas.datacontract.org/2004/07/IVS.Content.Data" xmlns:i="http://www.w3.org/2001/XMLSchema-instance">' \
           '<d4p1:filter i:nil="true" /><d4p1:paging xmlns:d5p1="http://schemas.datacontract.org/2004/07/IVS.Common"><d5p1:itemsOnPage>100</d5p1:itemsOnPage>' \
           '<d5p1:pageNumber>' + page + '</d5p1:pageNumber><d5p1:totalItems>0</d5p1:totalItems><d5p1:totalPages>0</d5p1:totalPages></d4p1:paging><d4p1:sort i:nil="true" />' \
           '<d4p1:type>ArcPlus</d4p1:type><d4p1:id>{ID}</d4p1:id><d4p1:relatedType>children</d4p1:relatedType></request></GetClientRelatedProgramGuide></s:Body></s:Envelope>'
     req = req.replace('{sessionID}', sID).replace('{ID}', ID)             
     conn = httplib.HTTPConnection(proxy, port)
     conn.request('POST', Config.ContentService, req, {
            'Host': host,                                        
            'SOAPAction': 'http://ivsmedia.iptv-distribution.net/ContentService/GetClientRelatedProgramGuide',
            'Content-Type': 'text/xml; charset=utf-8'
     })
     response = conn.getresponse()
     return response.read()

def GetRelProgram(sID, ID, page):
    Items = []
    try:
        tpage = soup("b:totalpages")[0].text
    except:
        tpage = "1"
    try:    
        page = soup("b:pagenumber")[0].text
    except:
        page = "1"    
    soup = BeautifulSoup(RelRequest(sID, ID, page))
    d = soup("a:programguideitem")
    for i in range(len(d)):
        c = d[i]
        sup = BeautifulSoup(c.prettify())
        name = sup("a:name")[0].text.encode('utf-8')
        descr = sup("a:description")[0].text.encode('utf-8')
        descr = descr.replace('&#xD;', '')
        length = sup("a:length")[0].text
        id = sup("a:id")[0].text
        startTime = sup("a:starttime")[0].text
        epnum = sup("a:episodenum")[0].text    
        cont = sup("a:iscontainer")[0].text
        imgcount = sup("a:imagecount")[0].text
        Items.append(RelObj(id, descr, name, length, startTime, epnum, cont, imgcount))       
    return RelGObj(tpage, page, Items)


class SObj:
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

class SGObj:
    def __init__(self, TPage, Page, Items):
        self.tpage = int(TPage)
        self.page = int(Page)
        self.items = Items

def Search(sID, type, page=1, keyword="", date="0001-01-01", id="0"):
    Items = []
    soup = BeautifulSoup(SRequest(sID, type, page, keyword, date, id))
    try:
        tpage = soup("b:totalpages")[0].text
    except:
        tpage = "1"
    try:    
        page = soup("b:pagenumber")[0].text
    except:
        page = "1"    
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
        Items.append(SObj(id, descr, name, epcount, length, startTime, epnum, cont, imgcount))       
    return SGObj(tpage, page, Items)

def SRequest(sID, type, page, keyword, date, id ):
    ctype = ['ArcPlus','VOD','DVR']
    t = int(type)
    
    #keyword = "Маша"
    #keyword = keyword.decode('utf-8')
    #keyword = keyword.encode('cp1251')
    #req = '<?xml version="1.0" encoding="utf-8"?>' \
          #'<s:Envelope '

    k = [keyword,""]
    req = \
        '<?xml version="1.0" encoding="utf-8"?>' \
        '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body><GetClientProgramGuide xmlns="http://ivsmedia.iptv-distribution.net"><sessionID>' + sID + '</sessionID><type>'+ctype[t] +'</type>' \
        '<request xmlns:d4p1="http://schemas.datacontract.org/2004/07/IVS.Content.Data" xmlns:i="http://www.w3.org/2001/XMLSchema-instance">' \
        '<d4p1:filter><d4p1:availableOnly>true</d4p1:availableOnly><d4p1:contentGenre i:nil="true" />' \
        '<d4p1:contentType>'+ctype[t]+'</d4p1:contentType><d4p1:date>' + date + 'T23:59:59</d4p1:date><d4p1:dateTill>' + date +'T00:00:00</d4p1:dateTill><d4p1:favoritesOnly>false</d4p1:favoritesOnly><d4p1:keyWord>' + keyword.decode('utf-8') + '</d4p1:keyWord>' \
        '<d4p1:orderBy i:nil="true" /><d4p1:showItems>true</d4p1:showItems><d4p1:studioID>' + id + '</d4p1:studioID><d4p1:visibleOnly>false</d4p1:visibleOnly></d4p1:filter>' \
        '<d4p1:paging xmlns:d5p1="http://schemas.datacontract.org/2004/07/IVS.Common"><d5p1:itemsOnPage>40</d5p1:itemsOnPage><d5p1:pageNumber>'+str(page)+'</d5p1:pageNumber><d5p1:totalItems>0</d5p1:totalItems><d5p1:totalPages>0</d5p1:totalPages>' \
        '</d4p1:paging><d4p1:sort i:nil="true" />' \
        '<d4p1:type>'+ ctype[t] +'</d4p1:type><d4p1:requestType>SearchByName</d4p1:requestType><d4p1:channelID>0</d4p1:channelID><d4p1:fromTime>0001-01-01T00:00:00</d4p1:fromTime><d4p1:itemCountAfter>0</d4p1:itemCountAfter>' \
        '<d4p1:itemCountBefore>0</d4p1:itemCountBefore><d4p1:streamZone>' + region[re] + '</d4p1:streamZone><d4p1:streamZoneUTCOffset>0</d4p1:streamZoneUTCOffset><d4p1:tillTime>0001-01-01T00:00:00</d4p1:tillTime><d4p1:watchingZone></d4p1:watchingZone>' \
        '<d4p1:watchingZoneUTCOffset>0</d4p1:watchingZoneUTCOffset></request></GetClientProgramGuide></s:Body></s:Envelope>' 
    #req =  unicode(req, 'utf8') 
        
    #req = req % k[0]
    req = req.encode('utf-8')    
    #req = req.replace('{sessionID}', sID).replace('{ID}', id).replace('{CTYPE}', ctype[t]).replace('{PageNum}',str(page)).replace('{DATE}',date)
    
    
    
           
    conn = httplib.HTTPConnection(proxy, port)
    conn.request('POST', Config.ContentService, req, {
            'Host': host,                                           
            'SOAPAction': 'http://ivsmedia.iptv-distribution.net/ContentService/GetClientProgramGuide',
            'Content-Type': 'text/xml; charset=utf-8'
     })
    response = conn.getresponse()
    return response.read() 

class RObj:
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

class RGObj:
    def __init__(self, TPage, Page, Items):
        self.tpage = int(TPage)
        self.page = int(Page)
        self.items = Items

def GetRelVod(sID, id="0", page="1"):
    Items = []
    soup = BeautifulSoup(RelVodReq(sID, id,page))
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
        startTime = sup("a:item_date")[0].text
        epnum = sup("a:episodenum")[0].text    
        cont = sup("a:iscontainer")[0].text
        imgcount = sup("a:imagecount")[0].text
        Items.append(RObj(id, descr, name, epcount, length, startTime, epnum, cont, imgcount))       
    return RGObj(tpage, page, Items)




def RelVodReq (sessionID, id, page):
    req = '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">' \
      '<s:Body>' \
      '<GetClientRelatedOnDemandContent xmlns="http://ivsmedia.iptv-distribution.net">' \
      '<sessionID>' + sessionID + '</sessionID>' \
      '<request xmlns:d4p1="http://schemas.datacontract.org/2004/07/IVS.Content.Data" xmlns:i="http://www.w3.org/2001/XMLSchema-instance">' \
      '<d4p1:filter i:nil="true" />' \
      '<d4p1:paging xmlns:d5p1="http://schemas.datacontract.org/2004/07/IVS.Common">' \
      '<d5p1:itemsOnPage>40</d5p1:itemsOnPage>' \
      '<d5p1:pageNumber>' + page + '</d5p1:pageNumber>' \
      '<d5p1:totalItems>0</d5p1:totalItems>' \
      '<d5p1:totalPages>0</d5p1:totalPages>' \
      '</d4p1:paging>' \
      '<d4p1:sort i:nil="true" />' \
      '<d4p1:type>VOD</d4p1:type>' \
      '<d4p1:id>' + id + '</d4p1:id>' \
      '<d4p1:relatedType>children</d4p1:relatedType>' \
      '</request>' \
      '</GetClientRelatedOnDemandContent>' \
      '</s:Body>' \
      '</s:Envelope>'
    conn = httplib.HTTPConnection(proxy, port)
    conn.request('POST', Config.ContentService, req, {
            'Host': host,                                           
            'SOAPAction': 'http://ivsmedia.iptv-distribution.net/ContentService/GetClientRelatedOnDemandContent',
            'Content-Type': 'text/xml; charset=utf-8'
     })
    response = conn.getresponse()
    return response.read()



    