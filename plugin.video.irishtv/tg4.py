# -*- coding: utf-8 -*-
import sys
import re
from time import strftime,strptime,mktime

import time, random
if sys.version_info >=  (2, 7):
    import json as _json
else:
    import simplejson as _json 
    
from datetime import timedelta
from datetime import date
from datetime import datetime
from urlparse import urljoin


import xbmc
import xbmcgui
import xbmcplugin

import mycgi
import utils
from loggingexception import LoggingException
import rtmp

import HTMLParser
from BeautifulSoup import BeautifulSoup
from BeautifulSoup import BeautifulStoneSoup

from provider import Provider
from brightcove import BrightCoveProvider

"""
'swfUrl' String 'http://admin.brightcove.com/viewer/us20130212.1339/federatedVideoUI/BrightcovePlayer.swf?uid=1360751436519'
'tcUrl' String 'rtmp://cp156323.edgefcs.net:1935/ondemand?videoId=2160442511001&lineUpId=&pubId=1290862567001&playerId=1364138050001&affiliateId='
'pageUrl' String 'http://www.tg4.ie'

Live
'swfUrl' String 'http://admin.brightcove.com/viewer/us20130212.1339/federatedVideoUI/BrightcovePlayer.swf?uid=1361558059116'
'tcUrl' String 'rtmp://cp101680.live.edgefcs.net:1935/live/stream-name:?videoId=1890376997001&lineUpId=&pubId=1290862567001&playerId=1364138050001&affiliateId='
'pageUrl' String 'http://www.tg4.ie'

"""
appNormal = u"ondemand?videoId=%s&lineUpId=&pubId=%s&playerId=%s&affiliateId="
appLive = 'live/stream-name:?videoId=%s&lineUpId=&pubId=%s&playerId=%s&affiliateId='

urlRoot     = u"http://www.tg4.ie"

mainCategories = u"http://www.tg4.ie/tg4-player/main_cats_%s.xml"
searchCategory = u"http://www.tg4.ie/TG4-Player/php/searchCat.php?categoryType=%s"
searchUrl = "http://www.tg4.ie/TG4-Player/php/search.php?searchTerm=%s"
recentUrl = u"http://www.tg4.ie/TG4-Player/php/getRecent.php"
popularUrl = u"http://www.tg4.ie/TG4-Player/php/mostPopular.php"
dateUrl = u"http://www.tg4.ie/TG4-Player/php/dateSearch.php?searchDate=%s"
liveScheduleUrl = u"http://www.tg4.ie/assets/snippets/tg4/Player_schedule_ie.php"

defaultLinkUrl = u"http://www.tg4.ie/%s/tg4-player/tg4-player.html?id=%s&title=%s"
playerFunctionsUrl = u'http://www.tg4.ie/TG4-player/script/player-functions2.js'
defaultLiveVideoId = u'1890376997001'
defaultLiveProgTitle = u"TG4 Beo Ireland"

class TG4Provider(BrightCoveProvider):

    def __init__(self):
        super(TG4Provider, self).__init__()

    def GetProviderId(self):
        return u"TG4"

    def ExecuteCommand(self, mycgi):
        self.log(u"Language: " + self.addon.getSetting( u'TG4_language' ))
        # 30018 = "Gaeilge"
        if self.addon.getSetting( u'TG4_language' ) != self.language(30018):
            self.languageCode = u"en"
        else:
            self.languageCode = u"ie"

        self.log(u"languageCode: " + self.languageCode)
        return super(TG4Provider, self).ExecuteCommand(mycgi)

    def ShowRootMenu(self):
        self.log(u"", xbmc.LOGDEBUG)
        try:
            listItems = []
            liveItemTuple = None
            searchItemTuple = None

            self.AddMenuItem(listItems, u"Search", u'Cuardaigh', u'&search=1')
            self.AddMenuItem(listItems, u"Latest", u"Is Déanaí", u'&latest=1')
            self.AddMenuItem(listItems, u"Categories", u'Catag\u00f3ir\u00ed', u'&categories=1')
            self.AddMenuItem(listItems, u"Popular", u"Is Coitianta", u'&popular=1')

            self.AddLiveMenuItem(listItems, u"Live", u"Beo", u'&live=1')

            xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
            xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
            
            return True
        
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            if xml is not None:
                msg = u"xml:\n\n%s\n\n" % xml
                exception.addLogMessage(msg)
            
            # Cannot show root menu
            exception.addLogMessage(self.language(30010))
            exception.process(severity = self.logLevel(xbmc.LOGERROR))
            return False


    def GetLiveSchedule(self):
        try:
            defaultSchedule = "Now: Unknown, Next: Unknown"
            html = None
            html = self.httpManager.GetWebPage(liveScheduleUrl, 300)

            soup = BeautifulSoup(html)
            holder=soup.find(id='plyr_Holder')
            cell2List=holder.findAll(attrs={'class':'plyr_Cell2'})
            
            found = None
            for cell in cell2List:
                if cell.b.string == u'Unavailable':
                    continue
                found = cell
                break

            if found is None:
                return defaultSchedule
            
            # "Now: Unknown, Next: "
            # E.g. "Now: Unknown, Next: 19:00 Nuacht TG4"
            return self.language(30024) + found.previousSibling.text + " " + found.contents[0]
        
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            if html is not None:
                msg = u"html:\n\n%s\n\n" % html
                exception.addLogMessage(msg)
            
            # Error getting live schedule
            exception.addLogMessage(self.language(30035))
            exception.process(severity = xbmc.LOGWARNING)
            return defaultSchedule


    def ParseCommand(self, mycgi):
        (categories, category, search, date, episodeId, series, latest, popular, live) = mycgi.Params( u'categories', u'category', u'search', u'date', u'episodeId', u'series', u'latest', u'popular', u'live') 

        category = category.decode(u'latin1')
        episodeId = episodeId.decode(u'latin1')
        series = series.decode(u'latin1')
       
        self.log(u"(category: %s, episodeId: %s, series: %s)" % (type(category), type(episodeId), type(series)), xbmc.LOGDEBUG)
        
        if search <> u'':
            return self.DoSearch()
        
        if categories != '':
            return self.ShowCategories()

        if category != '':
            return self.ShowCategory(category)

        if latest != '':
            return self.ListLatest()
        
        if date <> u'':
            return self.ListByDate(date)
            
        if popular != '':
            return self.ListEpisodes(popularUrl, True)
        
        if episodeId != '' and series != '':
            return self.PlayVideoWithDialog(self.ShowEpisode, (episodeId, series, appNormal))
        
        if live != '':
            return self.PlayVideoWithDialog(self.PlayLiveTV, ())
            
        return False

    def CreateCategoryItem(self, category):
        # First letter should be uppercase
        newLabel = category.text
        newLabel = newLabel[0].upper() + newLabel[1:]

        categoryId = category[u'id'].replace(u'music', u'Ceol')
        thumbnailPath = self.GetThumbnailPath(newLabel)
        newListItem = xbmcgui.ListItem( label=newLabel )
        newListItem.setThumbnailImage(thumbnailPath)
        url = self.GetURLStart() + u'&category=' + mycgi.URLEscape(categoryId)

        return (url, newListItem, True)

    def ShowCategories(self):
        listItems = []
        
        categoryId = u"Cursai Reatha"
        urlFragment = u'&category=' + mycgi.URLEscape(categoryId)
        self.AddMenuItem(listItems, u"News", u"Nuacht", urlFragment)

        """
        GET /tg4-player/main_cats_ie.xml HTTP/1.1
        <portfolio>
            <categories>
                <category id="drama">Drámaíocht</category>
                <category id="sport">Spórt</category>
                <category id="music">Ceol</category>
                <category id="cula4">Cúla4</category>
                <category id="faisneis">Faisnéis</category>
                <category id="siamsaiocht">siamsaíocht</category>
                <category id="live">Beo</category>
                <category id="search">Toradh</category>
            </categories>
        </portfolio>
        """        

        try:
            xml = None
            xml = self.httpManager.GetWebPage(mainCategories % self.languageCode , 20000)
    
            soup = BeautifulStoneSoup(xml)
            categories = soup.portfolio.findAll(u'category')
            
            for category in categories:
                if category[u'id'] == u'live' or category[u'id'] == u'search' or category[u'id'] == u'news':
                    continue
                
                listItems.append( self.CreateCategoryItem(category) )
                # Replace "Results" with "Search"

            xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
            xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
            
            return True
        
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            if xml is not None:
                msg = u"xml:\n\n%s\n\n" % xml
                exception.addLogMessage(msg)
            
            # Cannot show root menu
            exception.addLogMessage(self.language(30010))
            exception.process(severity = self.logLevel(xbmc.LOGERROR))
            return False

    def AddMenuItem(self, listItems, labelEN, labelIE, urlFragment):
        try:
            if self.languageCode == u'en':
                newLabel = labelEN
            else:
                newLabel = labelIE
            
            thumbnailPath = self.GetThumbnailPath(newLabel)
            newListItem = xbmcgui.ListItem( label=newLabel )
            newListItem.setThumbnailImage(thumbnailPath)
            url = self.GetURLStart() + urlFragment
                
            listItems.append( (url, newListItem, True) )
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            # Not fatal, just means that we don't have the news option
            exception.process(severity = xbmc.LOGWARNING)

    def AddLiveMenuItem(self, listItems, labelEN, labelIE, urlFragment):
        try:
            if self.languageCode == u'en':
                newLabel = labelEN
            else:
                newLabel = labelIE
            
            thumbnailPath = self.GetThumbnailPath(newLabel)

            schedule = self.GetLiveSchedule()
            newLabel = newLabel + "  [" + schedule + "]"
            newListItem = xbmcgui.ListItem( label=newLabel )
            newListItem.setThumbnailImage(thumbnailPath)
            newListItem.setProperty("Video", "true")
            #newListItem.setProperty('IsPlayable', 'true')

            url = self.GetURLStart() + urlFragment
                
            listItems.append( (url, newListItem, False) )
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            # Not fatal, just means that we don't have the news option
            exception.process(severity = xbmc.LOGWARNING)



    def ShowCategory(self, category):
        self.log(u"", xbmc.LOGDEBUG)
        url = searchCategory % mycgi.URLEscape(category)
    
        self.ListEpisodes(url, True)

    def GetLiveVideoParams(self, js):
        self.log(u"", xbmc.LOGDEBUG)

        try:
            pattern = u"function (getLivePlayer.+?)^}"
            match=re.search(pattern, js, re.MULTILINE | re.DOTALL)
            getLivePlayer = match.group(1)
            
            pattern = u'} else {\s+id\s*=\s*[\'"](\d+?)[\'"]'
            videoId = re.search(pattern, getLivePlayer, re.DOTALL).group(1)
            
            pattern='progTitle\s*=\s*"(.+?)"'
            progTitle = re.search(pattern, getLivePlayer, re.DOTALL).group(1)
            
            return (videoId, progTitle)
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
            
            if playerFunctionsJs is not None:
                msg = u"playerFunctionsJs:\n\n%s\n\n" % playerFunctionsJs
                exception.addLogMessage(msg)
                
            # Unable to determine live video parameters. Using default values.
            exception.addLogMessage(self.language(30022))
            exception.process(severity = xbmc.LOGWARNING)

            return (defaultLiveVideoId, defaultLiveProgTitle)
            # "Error creating calendar list"

    def ListLatest(self):
        self.log(u"", xbmc.LOGDEBUG)
        
        listItems = []
        
        try:
            today = date.today() 
            newLabel = u"Today"
            newListItem = xbmcgui.ListItem( label=newLabel )
            url = self.GetURLStart() + u'&date=' + today.strftime(u"%d.%m.%y")
            listItems.append( (url,newListItem,True) )
            
                # Yesterday
            newLabel = u"Yesterday"
            newListItem = xbmcgui.ListItem( label=newLabel )
            url = self.GetURLStart() + u'&date=' + (today - timedelta(1)).strftime(u"%d.%m.%y")
            listItems.append( (url,newListItem,True) )
            
            # Weekday
            newLabel = (today - timedelta(2)).strftime(u"%A")
            newListItem = xbmcgui.ListItem( label=newLabel )
            url = self.GetURLStart() + u'&date=' + (today - timedelta(2)).strftime(u"%d.%m.%y")
            listItems.append( (url,newListItem,True) )
            
            # Weekday
            newLabel = (today - timedelta(3)).strftime(u"%A")
            newListItem = xbmcgui.ListItem( label=newLabel )
            url = self.GetURLStart() + u'&date=' + (today - timedelta(3)).strftime(u"%d.%m.%y")
            listItems.append( (url,newListItem,True) )
    
            currentDate = today - timedelta(4)
            #TODO Get minus 35 dynamically
            sentinelDate = today - timedelta(36)
            while currentDate > sentinelDate:
                newLabel = currentDate.strftime(u"%A, %d %B %Y")
                newListItem = xbmcgui.ListItem( label=newLabel )
                url = self.GetURLStart() + u'&date=' + currentDate.strftime(u"%d.%m.%y")
                listItems.append( (url,newListItem,True) )
    
                currentDate = currentDate - timedelta(1) 
        
            xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
            xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
            
            return True
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
            
            if html is not None:
                msg = u"html:\n\n%s\n\n" % html
                exception.addLogMessage(msg)
                
            # "Error creating calendar list"
            message = self.language(30064)
            details = utils.valueIfDefined(minDateString, u'minDateString') + u", "
            details = details + utils.valueIfDefined(maxDateString, u'maxDateString') + u", "
            
            if utils.variableDefined( currentDate ):
                details = details + u"currentDate: " + unicode(currentDate) + u", "
            else:
                details = details + u"currentDate: Not defined"
                
            details = details + utils.valueIfDefined(url, u'url')
            
            exception.addLogMessage(logMessage = message + u"\n" + details)
            # "Error creating calendar list"
            exception.process(message, "", self.logLevel(xbmc.LOGERROR))
            return False
    
    def ListByDate(self, date):
        self.log(u"", xbmc.LOGDEBUG)

        return self.ListEpisodes( dateUrl % date )

    def GetAirDate(self, dateString):
        # 13/12/11 or 13.12.2011, etc
        pattern = u"\d\d(.)\d\d(.)(\d{2,4})"
        match = re.search(pattern, dateString, re.DOTALL)
        
        if match == None or len(match.group(3)) == 3:
            # Error processing date string: 
            self.log(self.language(30083) + dateString, xbmc.LOGWARNING)
            return None
        
        if len(match.group(3)) == 2:
            yearPattern = u"%y"
        else:
            yearPattern = u"%Y"

        separator1 = match.group(1)
        separator2 = match.group(2)

        datePattern = u"%d" + separator1 + u"%m" + separator2 + yearPattern
        
        airDate = date.fromtimestamp(mktime(strptime(dateString, datePattern)))
        
        return airDate

    def ListEpisodes(self, url, showDate = False):
        self.log(u"", xbmc.LOGDEBUG)
        
        """
        [{
            "id":"2160442511001",
            "name":"Nuacht TG4 16-43 (P1)",
            "shortDescription":"The day\u2019s main news stories from a regional, national and international perspective.",
            "creationDate":"1360700199450",
            "videoStillURL":"http:\/\/tgfour.brightcove.com.edgesuite.net\/pd\/1290862567001\/1290862567001_2160571128001_vs-511aa327e4b04ce8a4582520-672293875001.jpg?pubId=1290862567001",
            "thumbnailURL":"http:\/\/tgfour.brightcove.com.edgesuite.net\/pd\/1290862567001\/1290862567001_2160571130001_th-511aa327e4b04ce8a4582520-672293875001.jpg?pubId=1290862567001",
            "length":1047777,
            "customFields":{
                "title":"Nuacht TG4",
                "longdescgaeilge":"M\u00f3rimeachta\u00ed an lae \u00f3 Aonad Nuachta TG4.",
                "seriestitle":"Nuacht TG4",
                "date":"12.02.13"
            }
        }
        """
        
        try:
            jsonData = None
            item = None
            
            headers = {
                       'Content-Type' : 'application/x-www-form-urlencoded',
                       'X-Requested-With' : 'XMLHttpRequest'
                       }
            
            jsonData = self.httpManager.GetWebPage (url, 300, headers = headers)
            
            jsonObject = _json.loads(jsonData)
            
            listItems = []
            
            for item in jsonObject:
                try:
                    title = item[u'customFields'][u'title']
                    
                    # Exclude Live TV
                    if title.startswith("TG4 Beo"):
                        continue
                    
                    self.log(u"Title: " + title)
                    
                    if self.languageCode == u'ie':
                        description = item[u'shortDescription']
                    else:
                        description = item[u'customFields'][u'longdescgaeilge']
                    
                    dateString = item[u'customFields'][u'date']
                    airDate = self.GetAirDate(dateString)
                    
                    self.log(u"airDate: " + repr(airDate), xbmc.LOGDEBUG)
                    self.log(u"showDate: " + repr(showDate), xbmc.LOGDEBUG)
                    if showDate and airDate is not None:
                        title = title + "  [" + airDate.strftime(u"%A, %d %B %Y") + "]"

                    infoLabels = {
                                  u'Title': title, 
                                  u'Plot': description, 
                                  u'PlotOutline':  description,
                                  u'Date': airDate.strftime(u"%d.%m.%Y"),
                                  u'PremiereDate': airDate.strftime(u"%d.%m.%Y")                                  
                                  }
        
                    id = item['id']
                    thumbnail = item[u'videoStillURL']
                    
                    if u'name' in item:
                        newLabel = item[u'name']
                        if showDate:
                            newLabel = newLabel + "  [" + airDate.strftime(u"%A, %d %B %Y") + "]"
                    else:
                        newLabel = title

                    newListItem = xbmcgui.ListItem( label=newLabel)
                    newListItem.setThumbnailImage(thumbnail)

                    newListItem.setInfo(u'video', infoLabels)
                    newListItem.setProperty("Video", "true")
                    #newListItem.setProperty('IsPlayable', 'true')
                    
                    url = self.GetURLStart() + u'&episodeId=' + mycgi.URLEscape(id) + u'&series=' + mycgi.URLEscape(item['customFields']['seriestitle'])
     
                    listItems.append( (url, newListItem, False) )
                except (Exception) as exception:
                    if not isinstance(exception, LoggingException):
                        exception = LoggingException.fromException(exception)
        
                    if item is not None:
                        msg = u"item:\n\n%s\n\n" % repr(item)
                        exception.addLogMessage(msg)
                    
                    if item is not None and u'customFields' in item and u'title' in item[u'customFields'] :
                        programme = item[u'customFields'][u'title']
                    else:
                        programme = u"programme"

                    exception.addLogMessage((self.language(30063) % programme))
                    exception.process(self.language(30063) % programme, "", xbmc.LOGWARNING)

            xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
            xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
            
            return True
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            if jsonData is not None:
                msg = u"jsonData:\n\n%s\n\n" % jsonData
                exception.addLogMessage(msg)
            
            if item is not None:
                msg = u"item:\n\n%s\n\n" % jsonData
                exception.addLogMessage(msg)

            # Error preparing or playing stream
            exception.addLogMessage(self.language(40340))
            exception.process(severity = self.logLevel(xbmc.LOGERROR))
            return False
            

        
    def PlayLiveTV(self):
        self.log(u"", xbmc.LOGDEBUG)
        
        try:
            playerFunctionsJs = None
            playerFunctionsJs = self.httpManager.GetWebPage(playerFunctionsUrl, 20000)

            (videoId, progTitle) = self.GetLiveVideoParams(playerFunctionsJs)
            
            return self.ShowEpisode(videoId, progTitle, appLive, live = True)

        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            if playerFunctionsJs is not None:
                msg = u"playerFunctionsJs:\n\n%s\n\n" % playerFunctionsJs
                exception.addLogMessage(msg)

            # Error playing or downloading episode %s
            exception.addLogMessage(self.language(30051) % (videoId + ", " + progTitle))
            # Error playing or downloading episode %s
            exception.process(self.language(30051) % ' ' , '', self.logLevel(xbmc.LOGERROR))
            return False
        
    def AddSegments(self, playList):
        self.log("", xbmc.LOGDEBUG)
        self.amfResponse = None
        if self.totalParts < 2:
            return

        title = self.addon.getAddonInfo('name')
        icon = self.addon.getAddonInfo('icon')
        msg = self.language(30097) # Adding more parts
        xbmc.executebuiltin('XBMC.Notification(%s, %s, 5000, %s)' % (title, msg, icon))
        partsMinus1 = self.totalParts - 1
        parts = [None] * partsMinus1

        partsFound = 0
        getTotalCount = False
        pageSize = 12
        pageNumber = 0
        maxPages = 10

        
        self.log("Find related videos for refence Id %s" % self.referenceId, xbmc.LOGDEBUG)
        while pageNumber < maxPages and partsFound < partsMinus1: 
        
            try:
                self.log("Getting page %d of related videos" % pageNumber, xbmc.LOGDEBUG)
                self.amfResponse = None
                candidateId = None 
                self.amfResponse = self.FindRelatedVideos(self.playerKey, self.playerId, self.publisherId, self.episodeId, pageSize, pageNumber, getTotalCount)

                for mediaDTO in self.amfResponse[u'items']:
                    candidateId = mediaDTO[u'referenceId']
                    
                    pattern = u"%s[-_](\d+)" % self.referenceId 
                    match = re.search(pattern, candidateId, re.DOTALL)
    
                    self.log("Check candidate refence Id %s" % candidateId, xbmc.LOGDEBUG)
                    if match is not None:
                        partNumber = int(match.group(1))
                        
                        index = partNumber - 2
                        
                        if parts[index] is None:                        
                            partsFound = partsFound + 1
                            parts[index] = mediaDTO
                        
                            self.log("Matching refence id, part %d" % partNumber, xbmc.LOGDEBUG)
                            if partsFound > (partsMinus1 - 1):
                                break
                        
            except (Exception) as exception:
                if not isinstance(exception, LoggingException):
                    exception = LoggingException.fromException(exception)
                    
                if self.amfResponse is not None:
                    msg = "self.amfResponse:\n\n%s\n\n" % utils.drepr(self.amfResponse)
                    exception.addLogMessage(msg)

                if candidateId is not None:
                    msg = "pageNumber: %d, candidateId: %s" % (pageNumber, candidateId)
                    exception.addLogMessage(msg)

                # Error processing FindRelatedVideos
                exception.addLogMessage(self.language(30093))

                # Error playing or downloading episode %s
                exception.process('' , '', self.logLevel(xbmc.LOGDEBUG))
                
            pageNumber = pageNumber + 1
            
        try:
            if partsFound < partsMinus1:
                if partsMinus1 == 1:
                    msg = self.language(30094) # "Part 2 of 2 is missing"
                else: 
                    missing = partsMinus1 - partsFound
                    plural = ""
                    if missing > 2:
                        plural = "(s)"
                        
                    msg = self.language(30095) % (missing, plural) # "%d part%s missing"
                    
                exception = LoggingException(msg) 
                exception.process(self.language(30096) , '', self.logLevel(xbmc.LOGWARNING))
                 
            for mediaDTO in parts:
                if mediaDTO:
                    (infoLabels, logo, rtmpVar, defaultFilename) = self.GetPlayListDetailsFromAMF(mediaDTO, appNormal, self.episodeId, live = False)
                            
                    listItem = self.CreateListItem(infoLabels, logo) 
                    url = rtmpVar.getPlayUrl()
                    
                    if self.GetPlayer(None, None).isPlaying():
                        playList.add(url, listItem)
            
            plural = " has"
            if partsFound > 1:
                plural = "s have"
                
            msg = self.language(30098) % (partsFound, plural) # %d more part%s have been added to the Playlist
            xbmc.executebuiltin('XBMC.Notification(%s, %s, 5000, %s)' % (title, msg, icon))


        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            if self.amfResponse is not None:
                msg = "self.amfResponse:\n\n%s\n\n" % utils.drepr(self.amfResponse)
                exception.addLogMessage(msg)

            exception.process('' , '', self.logLevel(xbmc.LOGERROR))

    def ShowEpisode(self, episodeId, series, appFormat, live = False):
        self.log(u"episodeId: %s, series: %s, live: %s" % (episodeId, series, live), xbmc.LOGDEBUG)

        # "Getting player functions"
        self.dialog.update(5, self.language(30092))
        try:
            playerFunctionsJs = None
            playerFunctionsJs = self.httpManager.GetWebPage(playerFunctionsUrl, 20000)

            fullLLinkUrl = self.GetFullLink(episodeId, series, playerFunctionsJs)
            playerUrl = fullLLinkUrl.split('?')[0]
            
            bitUrl = self.GetBitUrl(episodeId, series, fullLLinkUrl, playerFunctionsJs)
            qsData = self.GetQSData(episodeId, bitUrl, playerFunctionsJs)

            if self.dialog.iscanceled():
                return False
            # "Getting SWF url"
            self.dialog.update(15, self.language(30089))
            self.swfUrl = self.GetSwfUrl(qsData)

            self.playerId = qsData[u'playerId']
            self.playerKey = qsData[u'playerKey']
            
            if self.dialog.iscanceled():
                return False
            # "Getting stream url"
            self.dialog.update(30, self.language(30087))
            rtmpUrl = self.GetStreamUrl(self.playerKey, playerUrl, self.playerId, contentId = episodeId)
            
            self.publisherId = unicode(int(float(self.amfResponse[u'publisherId']))) 
            self.episodeId = episodeId
            self.totalParts = 0 

            mediaDTO = self.amfResponse[u'programmedContent'][u'videoPlayer'][u'mediaDTO']

            (infoLabels, logo, rtmpVar, defaultFilename) = self.GetPlayListDetailsFromAMF(mediaDTO, appFormat, episodeId, live)

            if live:
                return self.Play(infoLabels, logo, rtmpVar)
            else:
                return self.PlayOrDownloadEpisode(infoLabels, logo, rtmpVar, defaultFilename)

        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            if playerFunctionsJs is not None:
                msg = u"playerFunctionsJs:\n\n%s\n\n" % playerFunctionsJs
                exception.addLogMessage(msg)

            # Error playing or downloading episode %s
            exception.addLogMessage(self.language(30051) % (episodeId + ", " + series))
            # Error playing or downloading episode %s
            exception.process(self.language(30051) % ' ' , '', self.logLevel(xbmc.LOGERROR))
            return False

    def GetPlayListDetailsFromAMF(self, mediaDTO, appFormat, episodeId, live):

            # ondemand?videoId=2160442511001&lineUpId=&pubId=1290862567001&playerId=1364138050001&affiliateId=
            app = appFormat % (episodeId, self.publisherId, self.playerId)
            
            # rtmp://cp156323.edgefcs.net/ondemand/&mp4:videos/1290862567001/1290862567001_2666234305001_WCL026718-2-4.mp4
            rtmpUrl = mediaDTO['FLVFullLengthURL']
            playPathIndex = rtmpUrl.index(u'&') + 1
            playPath = rtmpUrl[playPathIndex:]
            rtmpUrl = rtmpUrl[:playPathIndex - 1]
            rtmpVar = rtmp.RTMP(rtmp = rtmpUrl, playPath = playPath, app = app, swfUrl = self.swfUrl, tcUrl = rtmpUrl, pageUrl = urlRoot, live = live)
            self.AddSocksToRTMP(rtmpVar)
            
            #partNumberTitle = ""
            #partNumberFile = ""

            if self.totalParts == 0:
                self.totalParts = int(mediaDTO[u'customFields'][u'totalparts'])

            if self.totalParts != 1:
                partNumber = int(mediaDTO[u'customFields'][u'part'])
                
                if partNumber == 1:
                    fullReferenceId = mediaDTO[u'referenceId']
                    pattern = "(.+)[-_]1"
                    match = re.search(pattern, fullReferenceId, re.DOTALL)
                    self.referenceId = match.group(1)

                #partNumberTitle = " (%d/%d)" % (partNumber, self.totalParts)


            # Set up info for "Now Playing" screen
            infoLabels = {
                          u'Title': mediaDTO[u'displayName'],
                          u'Plot': mediaDTO[u'shortDescription'],
                          u'PlotOutline': mediaDTO[u'shortDescription']
                          }
            
            logo = mediaDTO[u'videoStillURL']
            defaultFilename = mediaDTO[u'displayName']
            
            return (infoLabels, logo, rtmpVar, defaultFilename)
    #def GetPartNumber(self, mediaDTO):
        #referenceId = mediaDTO[u'referenceid']

        #partNumber = 
        

    def GetAmfClassHash(self, className):
        self.log("className: " + className, xbmc.LOGDEBUG)

	if className == "com.brightcove.experience.ExperienceRuntimeFacade":
	        return u'2f5c3d72a1593b22fcedbca64cb6ff15cd6e97fe'

	if className == "com.brightcove.player.runtime.PlayerSearchFacade":
	        return u'c575e7f0658dcbf1ea459b097c80d052bdc7c375'

    
    def GetDefaultQSData(self, vidId, bitlyUrl):
        self.log("", xbmc.LOGDEBUG)
        bc_params = {}
        bc_params[u"id"] = u"myExperience1353057758001";
        bc_params[u"bgcolor"] = "#ffffff";
        bc_params[u"width"] = 500;
        bc_params[u"height"] = 282;
        bc_params[u"scale"] = u"noborder";
        bc_params[u"wmode"] = u"transparent";
        bc_params[u"autoplay"] = True;
        bc_params[u"playerId"] = 1364138050001;
        bc_params[u"playerKey"] = u"AQ~~,AAABLI1nnlk~,0ZsOdcYbRQ-u-9SnNHg9wPQRVgfuGIdh";
        bc_params[u"@videoPlayer"] = vidId;
        bc_params[u"linkBaseURL"] = bitlyUrl;
        bc_params[u"isVid"] = True;
        bc_params[u"isUI"] = True;
        bc_params[u"dynamicStreaming"] = True;
        bc_params[u"includeAPI"] = True;
        bc_params[u"templateLoadHandler"] = u"templateLoadedHandler";
        
        return bc_params;

    def GetQSData(self, vidId, bitlyUrl, js):
        self.log("", xbmc.LOGDEBUG)
        
        try:
            pattern = u"function (createPlayerHtml.+?)^}"
            match=re.search(pattern, js, re.MULTILINE | re.DOTALL)
            createPlayerHtml = match.group(1)
            
            bc_params = {}
            pattern = u"(bc_params\s*\[.+?\]\s*=.+?);"
            paramAppends = re.findall(pattern, createPlayerHtml)
            
            for paramAppend in paramAppends:
                paramAppend = paramAppend.replace(u'true', u'True')
                paramAppend = paramAppend.replace(u'["', u'[u"')
                paramAppend = paramAppend.replace(u'= "', u'= u"')
                self.log(u"paramAppend: %s" % paramAppend, xbmc.LOGDEBUG)
                exec(paramAppend)
            
            if bc_params < 10:
                self.log(self.language(30036), xbmc.LOGWARNING)
                self.log(utils.drepr(bc_params), xbmc.LOGDEBUG)
                return self.GetDefaultQSData(vidId, bitlyUrl)
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            # Unable to determine qsdata. Using default values.
            exception.addLogMessage(self.language(40600))
            exception.process(severity = xbmc.LOGWARNING)

            return self.GetDefaultQSData(vidId, bitlyUrl)
            
        return bc_params
        
    def GetBitUrl(self, episodeId, series, longUrl, js):
        self.log("", xbmc.LOGDEBUG)
        try:
            pattern = u"function (bit_url.+?)^}"
            self.log(pattern, xbmc.LOGDEBUG)
            match=re.search(pattern, js, re.MULTILINE | re.DOTALL)
            bit_url = match.group(1)
            
            pattern = u"var\s+username\s*=\s*[\"'](.+?)[\"']"
            self.log(pattern, xbmc.LOGDEBUG)
            username = re.search(pattern, bit_url, re.DOTALL).group(1)

            pattern = u"var\s+key\s*=\s*[\"'](.+?)[\"']"
            self.log(pattern, xbmc.LOGDEBUG)
            key = re.search(pattern, bit_url, re.DOTALL).group(1)

            pattern = u"url\s*:\s*[\"'](.+?)[\"']"
            self.log(pattern, xbmc.LOGDEBUG)
            apiUrl = re.search(pattern, bit_url, re.DOTALL).group(1)

            pattern = u"dataType\s*:\s*[\"'](.+?)[\"']"
            self.log(pattern, xbmc.LOGDEBUG)
            dataType = re.search(pattern, bit_url, re.DOTALL).group(1)
            
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            if js is not None:
                msg = u"js:\n\n%s\n\n" % js
                exception.addLogMessage(msg)

            # Error getting bit.ly API parameters. Using default values.
            exception.addLogMessage(self.language(30037))
            exception.process(severity = xbmc.LOGWARNING)

            # Defaults
            apiUrl = u"http://api.bit.ly/v3/shorten"
            dataType = u"jsonp"
            username = u"tg4webmaster"
            key = u"R_0415ac9dd2067d451236b796d85d461a"
            

        bitlyUrl = self.CallBitlyApi(username, key, apiUrl, longUrl, dataType, episodeId, series)
        return bitlyUrl
    

    def CallBitlyApi(self, username, key, apiUrl, longUrl, dataType, episodeId, series ):
        self.log("longUrl: %s", xbmc.LOGDEBUG)
        try:
            values = {
                  u'callback': '%s%d' % (dataType, int(round(time.time() * 1000.0))),
                  #u'longUrl': (longUrl + u"id=%s&title=%s" % (episodeId, series)).encode(u'latin1'),
                  u'longUrl': (longUrl).encode(u'latin1'),
                  u'apiKey': key,
                  u'login': username
                  }

            jsonData = self.httpManager.GetWebPage(apiUrl, 20000, values = values)
            
            jsonText = utils.extractJSON (jsonData)
            bitlyJSON = _json.loads(jsonText)
            
            return bitlyJSON[u'data'][u'url'] 
        
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            # Error calling bit.ly API
            exception.addLogMessage(self.language(30038))
            exception.process(severity = self.logLevel(xbmc.LOGERROR))

            raise exception
        

    def GetDefaultFullLink(self, episodeId, series):
        self.log("", xbmc.LOGDEBUG)
        linkUrl = defaultLinkUrl % self.languageCode
        fullLinkUrl =  linkUrl + u"id=" + episodeId + u"&title=" + series
        
        return fullLinkUrl
        
        
    def GetFullLink(self, episodeId, series, js):
        self.log("", xbmc.LOGDEBUG)
        try:
            pattern = u"function (loadPlayer.+?)^}"
            match=re.search(pattern, js, re.MULTILINE | re.DOTALL)
            loadPlayer = match.group(1)
            
            pattern = u"linkUrl\s*=\s*[\"'](http://.+?)[\"']"
            linkUrl = re.search(pattern, loadPlayer, re.DOTALL).group(1)
            
            linkUrl.replace(u'/ie/', u'/%s/' % self.languageCode)
            
            pattern = u"(fullLinkUrl\s*=\s*linkUrl.*?);"
            fullLinkUrlCode = re.search(pattern, loadPlayer, re.DOTALL).group(1)
    
            vidId = episodeId
            progTitle = series
            
            fullLinkUrl = ""
            exec(fullLinkUrlCode)
    
            if fullLinkUrl != "":
                return fullLinkUrl
        
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            # Error getting player url. Using default.
            exception.addLogMessage(self.language(30039))
            exception.process(severity = xbmc.LOGWARNING)
            
            return self.GetDefaultFullLink(episodeId, series)

    def DoSearchQuery( self, query):
        queryUrl = searchUrl % mycgi.URLEscape(query)
             
        self.log(u"queryUrl: %s" % queryUrl, xbmc.LOGDEBUG)
        
        return self.ListEpisodes(queryUrl, showDate = True)
