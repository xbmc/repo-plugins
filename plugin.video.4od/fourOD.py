# -*- coding: utf-8 -*-
import sys
import os
import re
import time

from subprocess import Popen, PIPE, STDOUT

import simplejson
import codecs

from BeautifulSoup import BeautifulStoneSoup

if hasattr(sys.modules[u"__main__"], u"xbmc"):
    xbmc = sys.modules[u"__main__"].xbmc
else:
    import xbmc
    
if hasattr(sys.modules[u"__main__"], u"xbmcgui"):
    xbmcgui = sys.modules[u"__main__"].xbmcgui
else:
    import xbmcgui

if hasattr(sys.modules[u"__main__"], u"xbmcplugin"):
    xbmcplugin = sys.modules[u"__main__"].xbmcplugin
else:
    import xbmcplugin

import mycgi
import utils
import rtmp
import fourOD_token_decoder

from loggingexception import LoggingException
from episodelist import EpisodeList
from provider import Provider, Subtitle
from watched import Watched, WatchedPlayer

urlRoot = u"http://www.channel4.com"
rootMenu = u"http://ps3.channel4.com/pmlsd/tags.json?platform=ps3&uid=%d"
searchUrl = u"http://www.channel4.com/search/predictive/?q=%s"
ps3Url = u"http://ps3.channel4.com/pmlsd/%s/4od.json?platform=ps3&uid=%d" # showId, time
ps3CategoryUrl = u"http://ps3.channel4.com/pmlsd/tags/%s/4od%s%s.json?platform=ps3" # % (categoryId, /order?, /page-X? )
ps3ShowUrl = u"http://ps3.channel4.com/pmlsd/%s.json?platform=ps3&uid=" 
ps3Root = u"http://ps3.channel4.com"
swfDefault = u"http://ps3.channel4.com/swf/ps3player-9.0.124-1.27.2.swf"

class FourODProvider(Provider):

    def GetProviderId(self):
        return u"4oD"

    def ExecuteCommand(self, mycgi):
        return super(FourODProvider, self).ExecuteCommand(mycgi)
    
    def GetHeaders(self):
        # PS3
        headers = {
                   u'User-Agent' : u"Mozilla/5.0 (PLAYSTATION 3; 3.55)",
                   u'DNT' : u'1'
                   }
        return headers

    def ShowRootMenu(self):
        self.log(u"", xbmc.LOGDEBUG)
        
        try:
            jsonText = None
            jsonText = self.httpManager.GetWebPage(rootMenu % int(time.time()*1000), 338)
    
            jsonData = simplejson.loads(jsonText)
            
            listItemsAtoZ = []
    
            if isinstance(jsonData[u'feed'][u'entry'], list):
                entries = jsonData[u'feed'][u'entry']
            else:
                # Single entry, put in a list
                entries = [ jsonData[u'feed'][u'entry'] ] 
            
            contextMenuItems = []
            contextMenuItems.append((u'Clear HTTP Cache', u"XBMC.RunPlugin(%s?clearcache=1)" % sys.argv[0] ))
            
            #TODO Error handling?
            orderedEntries = {}
            for entry in entries:
                """
                {"link":
                    {"self":"http:\/\/ps3.channel4.com\/pmlsd\/tags\/animals.json?platform=ps3",
                    "related":
                        ["http:\/\/ps3.channel4.com\/pmlsd\/tags\/animals\/title.json?platform=ps3",
                        "http:\/\/ps3.channel4.com\/pmlsd\/tags\/animals\/4od.json?platform=ps3",
                        "http:\/\/ps3.channel4.com\/pmlsd\/tags\/animals\/4od\/title.json?platform=ps3"]
                    },
                "$":"\n    \n    \n    \n    \n    \n    \n    \n    \n    \n    \n    \n  ",
                "id":"tag:ps3.channel4.com,2009:\/programmes\/categories\/animals",
                "title":"Animals",
                "summary":
                    {"@type":"html",
                    "$":"Channel 4 Animals Programmes"
                    },
                "updated":"2013-01-29T13:34:11.491Z",
                "dc:relation.CategoryType":"None",
                "dc:relation.AllProgrammeCount":5,
                "dc:relation.4oDProgrammeCount":1
                }
                """
                if entry[u'dc:relation.4oDProgrammeCount'] == 0:
                    continue
                
                id = entry[u'id']
                pattern = u'/programmes/categories/(.+)'
                match = re.search(pattern, id, re.DOTALL | re.IGNORECASE)
                
                categoryName = match.group(1)
                label = unicode(entry[u'title']) + u' (' + unicode(entry[u'dc:relation.4oDProgrammeCount']) + u')' 
                newListItem = xbmcgui.ListItem( label=label )
                newListItem.addContextMenuItems( contextMenuItems )
                
                url = self.GetURLStart() + u'&category=' + mycgi.URLEscape(categoryName) + u'&title=' + mycgi.URLEscape(label) + u'&order=' + mycgi.URLEscape(u'/title') + u'&page=1'
                
                if u'dc:relation.CategoryOrder' in entry:
                    order = entry[u'dc:relation.CategoryOrder']
                    orderedEntries[order] = (url,newListItem,True)
                else:
                    listItemsAtoZ.append( (url,newListItem,True) )
            
            # Add listItems in "category" order
            listItems = []
            
            index = 0
            while len(orderedEntries) > 0:
                if index in orderedEntries:
                    listItems.append(orderedEntries[index])
                    del orderedEntries[index]
                    
                index = index + 1
            
            listItems.extend(listItemsAtoZ)
            xbmcplugin.addDirectoryItems( handle=self.pluginhandle, items=listItems )
            xbmcplugin.endOfDirectory( handle=self.pluginhandle, succeeded=True )
            
            return True
        except (Exception) as exception:
            exception = LoggingException.fromException(exception)

            if jsonText is not None:
                msg = u"jsonText:\n\n%s\n\n" % jsonText
                exception.addLogMessage(msg)
                
            # Error processing categories
            exception.addLogMessage(self.language(30795))
            exception.process(self.language(30765), self.language(30795), severity = xbmc.LOGWARNING)
    
            return False
    

    def ParseCommand(self, mycgi):
        self.log(u"", xbmc.LOGDEBUG)

        (category, showId, episodeId, title, search, order, page, clearCache, watched, unwatched) = mycgi.Params( u'category', u'show', u'ep', u'title', u'search', u'order', u'page', u'clearcache', u'watched', u'unwatched' )

        if watched != u'':
             Watched().setWatched(episodeId)
             xbmc.executebuiltin( "Container.Refresh" )
             return True
            
        if unwatched != u'':
             Watched().clearWatched(episodeId)
             xbmc.executebuiltin( "Container.Refresh" )
             return True
            
        if clearCache != u'':
             httpManager.ClearCache()
             return True
       
        if ( showId <> u'' and episodeId == u''):
            return self.ShowEpisodes( showId, title )
        elif ( category <> u'' ):
            return self.ShowCategory( category, title, order, page )
        elif ( episodeId <> u'' ):
            (episodeNumber, seriesNumber) = mycgi.Params( u'episodeNumber', u'seriesNumber' )
            return self.PlayVideoWithDialog(self.PlayEpisode, (showId, int(seriesNumber), int(episodeNumber), episodeId, title))


    #==============================================================================
    # AddExtraLinks
    #
    # Add links to 'Most Popular'. 'Latest', etc to programme listings
    #==============================================================================
    
    def AddExtraLinks(self, category, label, order, listItems):
        if order == u'/title':
            newOrder = "" # Default order, latest
            newLabel = u' [' + u'Latest' + u' ' + label + u']'
            thumbnail = u'latest'
        else:
            newOrder = u'/title' # Alphanumerical
            newLabel = u' [' + 'Title' + u' ' + label + u']'
            thumbnail = u'title'
            
        thumbnailPath = self.GetThumbnailPath(thumbnail)
        newListItem = xbmcgui.ListItem( label=newLabel )
        newListItem.setThumbnailImage(thumbnailPath)
        url = self.GetURLStart() + u'&category=' + mycgi.URLEscape(category) + u'&title=' + mycgi.URLEscape(label) + u'&order=' + mycgi.URLEscape(newOrder) + u'&page=1'
        listItems.append( (url,newListItem,True) )

    
    #==============================================================================
    # AddPageLink
    #
    # Add Next/Previous Page links to programme listings
    #==============================================================================
    
    def AddPageLink(self, category, order, previous, page, listItems):
        thumbnail = u'next'
        arrows = u'>>'
        if previous == True:
            thumbnail = u'previous'
            arrows = u'<<'
    
        thumbnailPath = self.GetThumbnailPath(thumbnail)
        # E.g. [Page 2] >>
        label = u'[' + self.language(30510) + u' ' + page + u'] ' + arrows
    
        newListItem = xbmcgui.ListItem( label=label )
        newListItem.setThumbnailImage(thumbnailPath)
    
        url = self.GetURLStart() + u'&category=' + mycgi.URLEscape(category) + u'&title=' + mycgi.URLEscape(label) + u'&order=' + mycgi.URLEscape(order) + u'&page=' + mycgi.URLEscape(page)
        listItems.append( (url,newListItem,True) )
    
    
    #==============================================================================
    # AddPageToListItems
    #
    # Add the shows from a particular page to the listItem array
    #==============================================================================
    
    def AddPageToListItems( self, category, label, order, page, listItems ):
        """
        {"feed":
            {"link":
                {"self":"http:\/\/ps3.channel4.com\/pmlsd\/tags\/animals\/4od.json?platform=ps3",
                "up":"http:\/\/ps3.channel4.com\/pmlsd\/tags\/animals.json?platform=ps3"},
                "$":"\n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n",
                "id":"tag:ps3.channel4.com,2009:\/programmes\/tags\/animals\/4od",
                "title":"4oD Animals Programmes",
                "updated":"2013-01-29T15:12:58.105Z",
                "author":
                    {"$":"\n    \n  ",
                    "name":"Channel 4 Television"
                    },
                "logo":
                    {"@imageSource":"default",
                    "$":"http:\/\/cache.channel4.com\/static\/programmes\/images\/c4-atom-logo.gif"
                    },
                "fh:complete":"",
                "dc:relation.CategoryType":"None",
                "dc:relation.AllProgrammeCount":5,
                "dc:relation.4oDProgrammeCount":1,
                "dc:relation.platformClientVersion":1,
                "generator":{"@version":"1.43","$":"PMLSD"},
                "entry":
                    {"link":
                        {"self":"http:\/\/ps3.channel4.com\/pmlsd\/the-horse-hoarder.json?platform=ps3",
                        "related":["http:\/\/ps3.channel4.com\/pmlsd\/the-horse-hoarder\/4od.json?platform=ps3",
                        "http:\/\/ps3.channel4.com\/pmlsd\/the-horse-hoarder\/episode-guide.json?platform=ps3"]
                        },
                    "$":"\n    \n    \n    \n    \n    \n    \n    \n    \n    \n    \n    \n  ",
                    "id":"tag:ps3.channel4.com,2009:\/programmes\/the-horse-hoarder",
                    "title":"The Horse Hoarder",
                    "summary":
                        {"@type":"html",
                        "$":"Pensioner Clwyd Davies has accumulated 52 untamed horses, which he keeps at his home in Wrexham's suburbs"
                        },
                    "updated":"2013-01-07T12:30:53.872Z",
                    "dc:relation.sortLetter":"H",
                    "dc:date.TXDate":"2013-01-13T02:40:00.000Z",
                    "dc:relation.BrandWebSafeTitle":"the-horse-hoarder",
                    "content":
                        {"$":"\n      \n
                            ",
                        "thumbnail":
                            {"@url":"http:\/\/cache.channel4.com\/assets\/programmes\/images\/the-horse-hoarder\/ea8a20f0-2ba9-4648-8eec-d25a0fe35d3c_200x113.jpg",
                            "@height":"113",
                            "@width":"200",
                            "@imageSource":"own",
                            "@altText":"The Horse Hoarder"
                            }
                        }
                    }
                }
        }
        
        """
        try:
            jsonText = None
            pageInt = int(page)
        
            url = None
            if pageInt == 1:
                url = ps3CategoryUrl % (category, order, '')
            else:
                url = ps3CategoryUrl % (category, order, u'/page-%s' % page)
                
            jsonText = self.httpManager.GetWebPage(url, 963)
    
            jsonData = simplejson.loads(jsonText)
            
            if isinstance(jsonData[u'feed'][u'entry'], list):
                entries = jsonData[u'feed'][u'entry']
            else:
                # Single entry, put in a list
                entries = [ jsonData[u'feed'][u'entry'] ] 

            for entry in entries:
                id = entry[u'id']
                pattern = u'/programmes/(.+)'
                match = re.search(pattern, id, re.DOTALL | re.IGNORECASE)
                
                showId = match.group(1)
                thumbnail = entry[u'content'][u'thumbnail'][u'@url']
                progTitle = unicode(entry[u'title'])
                progTitle = progTitle.replace( u'&amp;', u'&' )
                progTitle = progTitle.replace( u'&pound;', u'£' )
                synopsis = entry[u'summary'][u'$']
                synopsis = synopsis.replace( u'&amp;', u'&' )
                synopsis = synopsis.replace( u'&pound;', u'£' )
                
                newListItem = xbmcgui.ListItem( progTitle )
                newListItem.setThumbnailImage(thumbnail)
                newListItem.setInfo(u'video', {u'Title': progTitle, u'Plot': synopsis, u'PlotOutline': synopsis})
                url = self.GetURLStart() + u'&category=' + category + u'&show=' + mycgi.URLEscape(showId) + u'&title=' + mycgi.URLEscape(progTitle)
                listItems.append( (url,newListItem,True) )
                
            if u'next' in jsonData[u'feed'][u'link']:
                nextUrl = jsonData[u'feed'][u'link'][u'next']
            else:
                nextUrl = None

            return nextUrl
        
        except (Exception) as exception:
            exception = LoggingException.fromException(exception)
        
            if jsonText is not None:
                msg = u"url: %s\n\n%s\n\n" % (unicode(url), jsonText)
                exception.addLogMessage(msg)
                
            # Error getting programme list web page
            exception.addLogMessage(self.language(30805))
            exception.process(u"", u"", severity = self.logLevel(xbmc.LOGERROR))
    
            raise exception
    
    #==============================================================================
    
    
    def ShowCategory(self, category, label, order, page ):
        self.log(unicode(( category, label, order, page)), xbmc.LOGDEBUG)
    
        pageInt = int(page)
        
        listItems = []
    
        try:
            pattern = u"\((\d+)\)"
            match = re.search(pattern, label, re.DOTALL | re.IGNORECASE)
            count = int(match.group(1))
        except:
            count = None
            
        if pageInt == 1 and count is None or count > 10:
            try:
                self.AddExtraLinks(category, label, order, listItems)
            except (Exception) as exception:
                exception = LoggingException.fromException(exception)
            
                # 'Error processing web page', 'Cannot show Category'
                exception.addLogMessage(self.language(30785))
                exception.process(self.language(30780), self.language(30785), severity = xbmc.LOGWARNING)
    
        paging = self.addon.getSetting( u'paging' )
    
        ###
        #paging = 'false'
        ###
        if (paging == u'true'):
            if pageInt > 1:
                self.AddPageLink(category, order, True, unicode(pageInt - 1), listItems)
    
            try:
                nextUrl = self.AddPageToListItems( category, label, order, page, listItems )
            except (Exception) as exception:
                if not isinstance(exception, LoggingException):
                    exception = LoggingException.fromException(exception)
            
                # 'Error processing web page', 'Cannot show Most Popular/A-Z/Latest'
                exception.addLogMessage(self.language(30780))
                exception.process(self.language(30785), self.language(30780), severity = xbmc.LOGWARNING)
            
                return False    

            if nextUrl is not None:
                nextPage = unicode(pageInt + 1)
                self.AddPageLink(category, order, False, nextPage, listItems)
        
        else:
            nextUrl = ''
            while len(listItems) < 500 and nextUrl is not None:
                try:
                    nextUrl = self.AddPageToListItems( category, label, order, page, listItems )
                    pageInt = pageInt + 1
                    page = unicode(pageInt)
                
                except (Exception) as exception:
                    if not isinstance(exception, LoggingException):
                        exception = LoggingException.fromException(exception)
            
                    # 'Cannot show category', 'Error processing web page'
                    exception.addLogMessage(self.language(30780))
                    exception.process(self.language(30785), self.language(30780), severity = self.logLevel(xbmc.LOGERROR))
                    return False
        
    
        xbmcplugin.addDirectoryItems( handle=self.pluginhandle, items=listItems )
        xbmcplugin.setContent(handle=self.pluginhandle, content=u'tvshows')
        xbmcplugin.endOfDirectory( handle=self.pluginhandle, succeeded=True )
    
        return None
    
    #==============================================================================
    
    def ShowEpisodes( self, showId, showTitle ):
        self.log(unicode(( showId, showTitle )), xbmc.LOGDEBUG)
        
        
        showWatched = self.addon.getSetting( u'show_watched' )
    
        if (showWatched == u'true'):
            episodeList = EpisodeList(self.GetURLStart(), self.httpManager, True)
        else:
            episodeList = EpisodeList(self.GetURLStart(), self.httpManager)
            
        try:
           episodeList.initialise(showId, showTitle)
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
        
            # 'Error processing web page', 'Cannot show Most Popular/A-Z/Latest'
            exception.addLogMessage(self.language(30740))
            exception.process(self.language(30735), self.language(30740), severity = self.logLevel(xbmc.LOGERROR))
        
            return False    
    
        listItems = episodeList.createListItems(mycgi)
    
        xbmcplugin.addDirectoryItems( handle=self.pluginhandle, items=listItems )
        xbmcplugin.setContent(handle=self.pluginhandle, content=u'episodes')
        xbmcplugin.endOfDirectory( handle=self.pluginhandle, succeeded=True )
    
        return True

    #==============================================================================
    def GetAuthentication(self, uriData):
        token = uriData.find(u'token').string
        cdn = uriData.find(u'cdn').string
        
        self.log(u"cdn: %s" % cdn, xbmc.LOGDEBUG)
        self.log(u"token: %s" % token, xbmc.LOGDEBUG)
        decodedToken = fourOD_token_decoder.Decode4odToken(token)
    
        if ( cdn ==  u"ll" ):
            ip = uriData.find(u'ip')
            e = uriData.find(u'e')
            if (ip):
                self.log(u"ip: %s" % ip.string, xbmc.LOGDEBUG)
                auth = u"e=%s&ip=%s&h=%s" % (e.string, ip.string, decodedToken)
            else:
                auth = u"e=%s&h=%s" % (e.string, decodedToken)
                
        else:
                fingerprint = uriData.find(u'fingerprint').string
                slist = uriData.find(u'slist').string
                
                auth = u"auth=%s&aifp=%s&slist=%s" % (decodedToken, fingerprint, slist)
    
        self.log(u"auth: %s" % auth, xbmc.LOGDEBUG)
    
        return auth
    
    #==============================================================================
    
    def GetStreamInfo(self, assetUrl):
        try:
            xml = None
            xml = self.httpManager.GetWebPageDirect( assetUrl )
            
            self.log(u"assetUrl: %s\n\n%s\n\n" % (assetUrl, xml), xbmc.LOGDEBUG)

            soup = BeautifulStoneSoup(xml)

            uriData = soup.find(u'uridata')
            streamURI = uriData.find(u'streamuri').text

            auth =  self.GetAuthentication(uriData)
        
            return (streamURI, auth)
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
        
            if xml is not None:
                msg = u"xml:\n\n%s\n\n" % xml
                exception.addLogMessage(msg)
                
            # Error processing asset data 
            exception.addLogMessage(self.language(51040) + swfDefault)
            raise exception

        
        
    
    #==============================================================================
    def GetSwfPlayer(self):
        try:
            rootHtml = None
            jsHtml = None
            rootHtml = self.httpManager.GetWebPage(ps3Root, 20000)

            soup = BeautifulStoneSoup(rootHtml)
            script = soup.find(u'script', src=re.compile(u'.+com.channel4.aggregated.+', re.DOTALL | re.IGNORECASE))
            jsUrl = script[u'src']
            
            jsHtml = self.httpManager.GetWebPage(ps3Root + u'/' + jsUrl, 20000)
            
            pattern = u"getPlayerSwf[^\"]+\"([^\"]+)\""
            match = re.search(pattern, jsHtml, re.DOTALL | re.IGNORECASE)
            
            swfPlayer = ps3Root + '/' + match.group(1)
            
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
        
            if rootHtml is not None:
                msg = u"rootHtml:\n\n%s\n\n" % rootHtml
                exception.addLogMessage(msg)
                
            if jsHtml is not None:
                msg = u"jsHtml:\n\n%s\n\n" % jsHtml
                exception.addLogMessage(msg)
                
            # Unable to determine swfPlayer URL. Using default: 
            exception.addLogMessage(self.language(30520) % swfDefault)
            exception.process(u'', u'', severity = xbmc.LOGWARNING)

            swfPlayer = swfDefault
        
        return swfPlayer



    def InitialiseRTMP(self, assetUrl):
        self.log(u'assetUrl: %s' % assetUrl, xbmc.LOGDEBUG)
    
        # Get the stream info
        (streamUri, auth) = self.GetStreamInfo(assetUrl)
        self.log(u'streamUri: %s' % streamUri, xbmc.LOGDEBUG)

        url = re.search(u'(.*?)mp4:', streamUri).group(1)
        app = re.search(u'.com/(.*?)mp4:', streamUri).group(1)
        playPath = re.search(u'(mp4:.*)', streamUri).group(1) + "?" + auth
        if "ll."  not in streamUri: 
            url = url + u"?ovpfv=1.1&" + auth
            app = app + u"?ovpfv=1.1&" + auth
        
        self.log(u'url: %s' % url, xbmc.LOGDEBUG)
        swfPlayer = self.GetSwfPlayer()
        
        port = None
        if self.addon.getSetting('rtmp_port_alt') == "true":
            port = 443
            
        rtmpvar = rtmp.RTMP(rtmp = url, app = app, swfVfy = swfPlayer, playPath = playPath, pageUrl = urlRoot, port = port)
        return rtmpvar
    
    #==============================================================================
    
    def getDefaultFilename(self, showId, seriesNumber, episodeNumber):
        if ( seriesNumber <> "" and episodeNumber <> "" ):
            #E.g. NAME.s01e12
            return showId + u".s%0.2ie%0.3i" % (int(seriesNumber), int(episodeNumber))
        
        return showId
    
    def GetSeriesAndEpisode(self, entry):
        if u'dc:relation.SeriesNumber' in entry and u'dc:relation.EpisodeNumber' in entry:
            return (entry[u'dc:relation.SeriesNumber'], entry[u'dc:relation.EpisodeNumber'])
        
        pattern = u'series-([0-9]+)(\\\)?/episode-([0-9]+)'
        seasonAndEpisodeMatch = re.search( pattern, entry[u'link'][u'related'], re.DOTALL | re.IGNORECASE )

        self.log(u"Searching for season and episode numbers in url: %s" % entry[u'link'][u'related'], xbmc.LOGDEBUG)
        if seasonAndEpisodeMatch is not None:
            seriesNum = int(seasonAndEpisodeMatch.group(1))
            epNum = int(seasonAndEpisodeMatch.group(3))
            
            return (seriesNum, epNum)
        
        return None, None
        
    def GetWatchedPercent(self):
         watched_values = [.7, .8, .9]
         return watched_values[int(self.addon.getSetting('watched-percent'))]
    

    def GetPS3AssetUrl(self, showId, seriesNumber, episodeNumber):

        headers = {}
        headers[u'DNT'] = u'1'
        headers[u'Referer'] = u'http://ps3.channel4.com'  
        headers[u'User-Agent'] = u'Mozilla/5.0 (PLAYSTATION 3; 3.55)' 

        try:
            data = None        
            url = ps3Url % (showId, int(time.time()*1000))
            data = self.httpManager.GetWebPage(url, 933)
            
            self.log(u"ps3Url: %s\n\n%s\n\n" % (url, data), xbmc.LOGDEBUG)
            
            jsonData = simplejson.loads(data)
    
            if isinstance(jsonData[u'feed'][u'entry'], list):
                entries = jsonData[u'feed'][u'entry']
            else:
                # Single entry, put in a list
                entries = [ jsonData[u'feed'][u'entry'] ] 
    
            for entry in entries:
                (entrySeriesNum, entryEpNum) = self.GetSeriesAndEpisode(entry)
                if entrySeriesNum is None or entryEpNum is None:
                    self.log(u"Error determining season and episode numbers for this episide: \n\n%s\n\n" % entry, xbmc.LOGWARNING)
                    continue
                
                if entrySeriesNum == seriesNumber and entryEpNum == episodeNumber:
                    return entry[u'group'][u'player'][u'@url']
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
        
            exception.addLogMessage("showId:%s, seriesNumber:%s, episodeNumber:%s" % (showId, seriesNumber, episodeNumber))        
            if data is not None:
                msg = u"data:\n\n%s\n\n" % data
                exception.addLogMessage(msg)
                
            # Error processing data for show
            exception.addLogMessage(self.language(31030))
            exception.process(u'', u'', severity = xbmc.LOGWARNING)

        return None

    #==============================================================================
    def getRTMPUrl(self, showId, seriesNumber, episodeNumber, episodeId):
        playUrl = None

        try:    
            assetUrl = self.GetPS3AssetUrl(showId, seriesNumber, episodeNumber)
            rtmpvar = self.InitialiseRTMP(assetUrl)
            playUrl = rtmpvar.getPlayUrl()    

            return (playUrl, rtmpvar)
    
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
        
            exception.addLogMessage(self.language(30810))
            # "Error parsing html", "Error getting stream info xml"
            exception.process(self.language(30735), self.language(30810), severity = self.logLevel(xbmc.LOGERROR))

            raise exception
    
    
    def PlayEpisode( self, showId, seriesNumber, episodeNumber, episodeId, title ):
        self.log (u'PlayEpisode showId: ' + showId, xbmc.LOGDEBUG)
        self.log (u'PlayEpisode episodeId: ' + episodeId, xbmc.LOGDEBUG)
        self.log (u'PlayEpisode title: ' + title, xbmc.LOGDEBUG)
    
        self.episodeId = episodeId
        try:
            # "Getting video stream url"
            self.dialog.update(10, self.language(32700))
            (playUrl, rtmpVar) = self.getRTMPUrl(showId.lower(), seriesNumber, episodeNumber, episodeId)
        except (LoggingException) as exception:
            # Error getting RTMP url
            exception.addLogMessage(self.language(30965))
            exception.process(u"", u"", severity = self.logLevel(xbmc.LOGERROR))
            
            self.dialog.close()
            return False
    
        if self.dialog.iscanceled():
            return False
        # "Getting episode information"
        self.dialog.update(30, self.language(32710))
        self.log (u'rtmpVar: %s' % unicode(rtmpVar))
    
        # If we can't get rtmp then don't do anything
        # TODO Error message
        if rtmpVar is None:
            return False

        episodeList = EpisodeList(self.GetURLStart(), self.httpManager)
        episodeList.initialise(showId, title)
        episodeDetail = episodeList.GetEpisodeDetail(episodeId)
        
        (infoLabels, thumbnail) = episodeList.getInfolabelsAndLogo(episodeDetail)
        #infoLabels['episodeId'] = episodeId # Add for monitoring watched percentage
        
        self.AddSocksToRTMP(rtmpVar)
        defaultFilename = self.getDefaultFilename(showId, seriesNumber, episodeNumber)

        subtitles = None
        if self.addon.getSetting( u'subtitles' ) == u'true':
            subtitles = Subtitle_4oD(self.httpManager, self.log)
            subtitles.SetEpisodeId(episodeId)
            subtitles.SetHasSubtitle(episodeDetail.hasSubtitles)

        return self.PlayOrDownloadEpisode(infoLabels, thumbnail, rtmpVar, defaultFilename, subtitles = subtitles)

    def GetPlayer(self):
        showWatched = self.addon.getSetting( u'show_watched' )
    
        if (showWatched == u'true'):
            player = WatchedPlayer(xbmc.PLAYER_CORE_AUTO)
            player.initialise(self.GetWatchedPercent(), self.episodeId, self.log)
            return player
        else:
            return super(FourODProvider, self).GetPlayer()
        

class Subtitle_4oD(Subtitle):
    
    def __init__(self, httpManager, log):
        self.log = log
        self.httpManager = httpManager
    
    def SetEpisodeId(self, episodeId):
        self.episodeId = episodeId
    
    def SetHasSubtitle(self, hasSubtitles):
        self.hasSubtitles = hasSubtitles
    
    def GetSubtitleFile(self, filename = None):
        subtitle = None 
        if self.hasSubtitles:
            subtitle = self.httpManager.GetWebPage( u"http://ais.channel4.com/subtitles/%s" % self.episodeId, 40000 )
        
        self.log(u'Subtitle code: ' + unicode(self.httpManager.GetLastCode()), xbmc.LOGDEBUG )
        self.log(u'Subtitle filename: ' + unicode(filename), xbmc.LOGDEBUG)
    
        if subtitle is not None:
            self.log(u'Subtitle file length: ' + unicode(len(subtitle)), xbmc.LOGDEBUG)
    
        self.log(u'httpManager.GetLastCode(): ' + unicode(self.httpManager.GetLastCode()), xbmc.LOGDEBUG)
    
        if (subtitle is None or self.httpManager.GetLastCode() == 404 or len(subtitle) == 0):
            if self.hasSubtitles is True:
                self.log(u'No subtitles available', xbmc.LOGWARNING )
            subtitleFile = sys.modules[u"__main__"].NO_SUBTITLE_FILE
        else:
            if filename is None:
                subtitleFile = sys.modules[u"__main__"].SUBTITLE_FILE
            else:
                subtitleFile = filename
    
            quotedSyncMatch = re.compile(u'<Sync Start="(.*?)">', re.IGNORECASE)
            subtitle = quotedSyncMatch.sub(u'<Sync Start=\g<1>>', subtitle)
            subtitle = subtitle.replace( u'&quot;', u'"')
            subtitle = subtitle.replace( u'&apos;', u"'")
            subtitle = subtitle.replace( u'&amp;', u'&' )
            subtitle = subtitle.replace( u'&pound;', u'£' )
            subtitle = subtitle.replace( u'&lt;', u'<' )
            subtitle = subtitle.replace( u'&gt;', u'>' )
    
            filesub=codecs.open(subtitleFile, u'w', u'utf-8')
            filesub.write(subtitle)
            filesub.close()
    
        return subtitleFile
    
