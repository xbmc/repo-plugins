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
import Media, Common
from BeautifulSoup import BeautifulSoup


class Application:
    ClientAppSettings = (object)
    AppSettings = (object)
    def __init__(self):
        self.ClientAppSettings = ClientAppSettings()
        self.AppSettings = AppSettings()



class ClientAppSettings:
    req = ''
    appSettings = (object)    
    clientCredential = (object)
    def __init__(self):
        self.req = '<cc xmlns:d4p1="http://schemas.datacontract.org/2004/07/IVS.Content.Application" xmlns:i="http://www.w3.org/2001/XMLSchema-instance">' 
        self.appSettings = AppSettings()
        self.clientCredential = Media.Client().AccessCredentials
    def get(self):
        set = ''
        self.req = self.req + self.appSettings.get() + self.clientCredential.get() + '</cc>'
        return self.req
        

class AppSettings:
    req = ''
    appName = ''
    settings = []
    siteID = 0
    def get(self):
        set = ''
        id = ''
        if self.appName == '' and len(self.settings) == 0 and self.siteID == 0:
            req = '<d4p1:appSettings i:nil="true" />'
        else:
            if self.appName != '':
                self.appName = '<d4p1:appName>' + self.appName + '</d4p1:appName>'
            else:
                self.appName = '<d4p1:appName i:nil="true" />'
            if len(self.settings) == 0:
                set = '<d4p1:settings xmlns:d6p1="http://schemas.datacontract.org/2004/07/IVS.Common" />'
            id = '<d4p1:siteID>' + str(self.siteID) + '</d4p1:siteID>'
            self.req = '<d4p1:appSettings>' + self.appName + set + id + '</d4p1:appSettings>'
        return self.req


class Data:
    ContentRequest = (object)
    ContentFilter = (object)
    ContentSort = (object)
    def __init__(self):
        self.ContentRequest = ContentRequest()
        self.ContentFilter = ContentFilter()
        self.ContentSort = ContentSort()


class ContentRequest:
    filter = (object)
    paging = (object)
    sort = (object)
    type = 'AudioBooks'
    def __init__(self):
        self.filter = ContentFilter()
        self.paging = Common.ItemPaging()
        self.sort = ContentSort()
    def get(self):
        self.type = '<d4p1:type>' + self.type + '</d4p1:type>'
        req = '<request xmlns:d4p1="http://schemas.datacontract.org/2004/07/IVS.Content.Data" xmlns:i="http://www.w3.org/2001/XMLSchema-instance">'
        req = req + self.filter.get() + self.paging.get() + self.sort.get() + self.type + '</request>'
        return req
    
    
class ContentFilter:
    availableOnly = 'false'
    contentGenre = (object)
    contentType = 'AudioBooks'
    date = '0001-01-01T00:00:00'
    dateTill = '0001-01-01T00:00:00'
    favoritesOnly = 'false'
    keyWord = ''
    orderBy = ''
    showItems = 'false'
    studioID = '0'
    visibleOnly = 'false'
    def __init__(self):
        contentGenre = ContentGenre()
    def get(self):
        req = ''
        if self.availableOnly == 'false' and self.contentType == 'AudioBooks' and self.date == '0001-01-01T00:00:00' and self.dateTill == '0001-01-01T00:00:00' and self.favoritesOnly == 'false' and self.keyWord == '' and self.orderBy == '' and self.showItems == '' and self.studioID == '0' and self.visibleOnly == 'false':
            req = '<d4p1:filter i:nil="true" />'
        else:
            req = '<d4p1:filter>'
            self.availableOnly = '<d4p1:availableOnly>' + self.availableOnly + '</d4p1:availableOnly>'
            self.contentType =   '<d4p1:contentType>' + self.contentType +  '</d4p1:contentType>'
            self.date = '<d4p1:date>' + self.date + '</d4p1:date>'
            self.dateTill = '<d4p1:dateTill>' + self.dateTill + '</d4p1:dateTill>'
            self.favoritesOnly = '<d4p1:favoritesOnly>' + self.favoritesOnly + '</d4p1:favoritesOnly>'
            if self.keyWord == '':
                self.keyWord = '<d4p1:keyWord i:nil="true" />'
            else:
                self.keyWord = '<d4p1:keyWord>' + self.keyWord + '</d4p1:keyWord>'
            if self.orderBy == '':
                self.orderBy = '<d4p1:orderBy i:nil="true" />'
            else:
                self.orderBy = '<d4p1:orderBy>' + self.orderBy + '</d4p1:orderBy>'
            self.showItems = '<d4p1:showItems>' + self.showItems + '</d4p1:showItems>'
            self.studioID = '<d4p1:studioID>' + self.studioID + '</d4p1:studioID>'
            self.visibleOnly = '<d4p1:visibleOnly>' + self.visibleOnly + '</d4p1:visibleOnly>'
            req = req + self.availableOnly + self.contentGenre.get() + self.contentType + self.date + self.dateTill + self.favoritesOnly + self.keyWord + self.orderBy + self.showItems + self.studioID + self.visibleOnly + '</d4p1:filter>'
        return req
            

class ContentGenre:
    childrenIDs = []
    code = ''
    genreType = 'UnknownGenreType'
    id = '0'
    itemCount = '0'
    name = ''
    parentID = '0'
    def get(self):
        req = ''
        if len(self.childrenIDs) == 0 and self.code == '' and self.genreType == 'UnknownGenreType' and self.id == '0' and self.itemCount == '0' and self.name == '' and self.parentID == '0':
            req = '<d4p1:contentGenre i:nil="true" />'
        else:
            child = ''
            req = '<d4p1:contentGenre>'
            if len(self.childrenIDs) == 0:
                child = '<d4p1:childrenIDs xmlns:d7p1="http://schemas.microsoft.com/2003/10/Serialization/Arrays" />'
            if self.code == '':
                self.code = '<d4p1:code i:nil="true" />'
            else:
                self.code = '<d4p1:code>' + self.code + '</d4p1:code>'
            self.genreType = '<d4p1:contentType>' + self.genreType + '</d4p1:contentType>'
            self.id = '<d4p1:id>' + self.id + '</d4p1:id>'
            self.itemCount = '<d4p1:itemCount>' + self.itemCount + '</d4p1:itemCount>'
            if self.name == '':
                self.name = '<d4p1:name i:nil="true" />'
            else:
                self.name = '<d4p1:name>' + self.name + '</d4p1:name>'
            self.parentID = '<d4p1:parentID>' + self.parentID + '</d4p1:parentID>'
            req = req + child + self.code + self.genreType + self.id + self.itemCount + self.name + self.parentID + '</d4p1:contentGenre>'
        return req
            
                                
class ContentSort:
    contentType = 'AudioBooks'
    fields = []
    orderBy = ''
    orderDirection = ''
    def get(self):
        req = ''
        if self.contentType == 'AudioBooks' and len(self.fields) == 0 and self.orderBy == '' and self.orderDirection == '':
            req = '<d4p1:sort i:nil="true" />'
        else:
            field = ''
            req = '<d4p1:sort>'
            self.contentType = '<d4p1:contentType>' + self.contentType + '</d4p1:contentType>'
            if len(self.fields) == 0:
                field = '<d4p1:fields xmlns:d6p1="http://schemas.datacontract.org/2004/07/IVS.Common" />'
            if self.orderBy == '':
                self.orderBy = '<d4p1:orderBy i:nil="true" />'
            else:
                self.orderBy = '<d4p1:orderBy>' + self.orderBy + '</d4p1:orderBy>'
            if self.orderDirection == '':
                self.orderDirection = '<d4p1:orderDirection i:nil="true" />'
            else:    
                self.orderDirection = '<d4p1:orderDirection>' + self.orderDirection + '</d4p1:orderDirection>'
            req = req + self.contentType + field + self.orderBy + self.orderDirection + '</d4p1:sort>'
        return req


class Channels:
    items = []
    filter = (object)
    TPage = ''
    
    sort = (object)
    type = ''
    def Invoke(self,str):
        soup = BeautifulSoup(str)
        try:
            self.TPage = soup('b:totalpages')[0].text
            chn = soup('a:channel')
            for i in chn:
                sup = BeautifulSoup(i.prettify())
                c = Channel()
                c.contentType = sup('a:contenttype')[0].text
                c.id = sup('a:id')[0].text
                c.advisory = sup('a:advisory')[0].text
                c.bookmarked = sup('a:bookmarked')[0].text
                c.containerID = sup('a:containerid')[0].text
                c.description = sup('a:description')[0].text.encode('utf-8')
                c.episodeNum = sup('a:episodenum')[0].text
                c.imageCount = sup('a:imagecount')[0].text
                c.isContainer = sup('a:iscontainer')[0].text
                c.item_date = sup('a:item_date')[0].text
                c.name = sup('a:name')[0].text.encode('utf-8')
                c.rating = sup('a:rating')[0].text
                c.status = sup('a:status')[0].text
                c.orderNum = sup('a:ordernum')[0].text
                c.originalLiveUtcOffset = sup('a:originalliveutcoffset')[0].text
                c.readyForDvr = sup('a:readyfordvr')[0].text
                c.visible = sup('a:visible')[0].text
                self.items.append(c)
        except:
            pass        
                

class Channel:
  def __init__(self):  
    self.contentType = ''
    self.id = ''
    self.advisory = ''
    self.availableFormats = []
    self.bookmarked = ''
    self.children = []
    self.containerID = ''
    self.contentGenres = []
    self.description = ''
    self.episodeNum = ''
    self.imageCount = ''
    self.isContainer = ''
    self.item_date = ''
    self.name = ''
    self.rating = ''
    self.status = ''
    self.suggestedItems  = []
    self.channelGroups = []
    self.orderNum = ''
    self.originalLiveUtcOffset = ''
    self.readyForDvr = ''
    self.visible = ''                            
                
         
                
        
    
          
              
    