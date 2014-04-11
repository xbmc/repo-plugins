# -*- coding: utf-8 -*-
#TODO Integrate WatchPlayer & ResumePlayer
#TODO Search

import sys
import os
import re
import time

from subprocess import Popen, PIPE, STDOUT

if sys.version_info >=  (2, 7):
    import json as _json
else:
    import simplejson as _json 
    
import codecs

from BeautifulSoup import BeautifulSoup
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
from resumeplayer import ResumePlayer

urlRoot = u"http://m.channel4.com"
rootMenu = u"http://m.channel4.com/4od/tags"
searchUrl = u"http://www.channel4.com/search/predictive/?q=%s"
categoryUrl = u"http://m.channel4.com/4od/tags/%s%s%s" # % (categoryId, /order?, /page-X? )
showUrl = u"http://m.channel4.com/4od/%s%s" # (showId, /series-1 )
swfDefault = u"http://m.channel4.com/swf/mobileplayer-10.2.0-1.43.swf"
javascriptUrl = u"http://m.channel4.com/js/script.js"
aisUrl = u"http://ais.channel4.com/asset/%s"

class FourODProvider(Provider):

    def __init__(self):
        super(FourODProvider, self).__init__()
        self.userAgent = ''
        
    def GetProviderId(self):
        return u"4oD"

    def ExecuteCommand(self, mycgi):
        return super(FourODProvider, self).ExecuteCommand(mycgi)
    
    def SetSubtitlePaths(self, subtitleFilePath, noSubtitleFilePath):
        self.subtitleFilePath = subtitleFilePath
        self.noSubtitleFilePath = noSubtitleFilePath
        
    def GetHeaders(self):
        headers = {
                   u'User-Agent' : 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Trident/6.0)',
                   u'DNT' : u'1'
                   }
        return headers

    def ShowRootMenu(self):
        self.log(u"", xbmc.LOGDEBUG)
        """
          <section id="categories" class="clearfix">

            <aside class="catNav clearfix">
                <nav>
                    <h2>Most popular</h2>
                    <ul>
                    
                        <li class="active">
                            <span class="chevron"></span>
                            <a href="/4od/tags/comedy">Comedy (100)</a>
                        </li>
                    </ul>

                    <h2>More categories</h2>

                    <ul>
                        <li>
                            <span class="chevron"></span>
                            <a href="/4od/tags/animals">Animals (4)</a>
                        </li>
                           
        """
        try:
            html = None
            html = self.httpManager.GetWebPage(rootMenu, 338)
    
            soup = BeautifulSoup(html)
            categoriesSection = soup.find('section', id="categories")
            entries = categoriesSection.find('nav').findAll('a')
            
            contextMenuItems = []
            contextMenuItems.append((u'Clear HTTP Cache', u"XBMC.RunPlugin(%s?clearcache=1)" % sys.argv[0] ))

            listItems = []
            
            pattern = u'/4od/tags/(.+)'
            for entry in entries:
                
                href = entry['href']
                match = re.search(pattern, href, re.DOTALL | re.IGNORECASE)
                
                categoryId = match.group(1)
                label = unicode(entry.text).replace('\r\n', '')
                label = re.sub(' +', ' ', label)
                newListItem = xbmcgui.ListItem( label=label )
                newListItem.addContextMenuItems( contextMenuItems )
                
                url = self.GetURLStart() + u'&category=' + mycgi.URLEscape(categoryId) + u'&title=' + mycgi.URLEscape(label) + u'&order=' + mycgi.URLEscape(u'/latest') + u'&page=1'
                
                listItems.append( (url,newListItem,True) )
            
            xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
            xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
            
            return True
        except (Exception) as exception:
            exception = LoggingException.fromException(exception)

            if html is not None:
                msg = u"html:\n\n%s\n\n" % html
                exception.addLogMessage(msg)
                
            # Error processing categories
            exception.addLogMessage(self.language(30795))
            exception.process(self.language(30765), self.language(30795), severity = xbmc.LOGWARNING)
    
            return False
    

    def ParseCommand(self, mycgi):
        self.log(u"", xbmc.LOGDEBUG)

        (category, showId, episodeId, title, search, order, page, season, thumbnail, premiereDate, resume) = mycgi.Params( u'category', u'show', u'episodeId', u'title', u'search', u'order', u'page', u'season', u'thumbnail', u'premiereDate', u'resume' )

        if ( showId <> u'' and episodeId == u''):
            return self.ShowEpisodes( showId, title, season )
        elif ( category <> u'' ):
            return self.ShowCategory( category, title, order, page )
        elif ( episodeId <> u'' ):
            resumeFlag = False
            if resume <> u'':
                resumeFlag = True

            (episodeNumber, seriesNumber) = mycgi.Params( u'episodeNumber', u'seriesNumber' )
            return self.PlayVideoWithDialog(self.PlayEpisode, (showId, seriesNumber, episodeNumber, episodeId, title, thumbnail, premiereDate, resumeFlag))


    #==============================================================================
    # AddExtraLinks
    #
    # Add links to 'Most Popular'. 'Latest', etc to programme listings
    #==============================================================================
    
    def AddExtraLinks(self, category, label, order, listItems):
        if order == u'/atoz':
            newOrder = "/latest" # Default order, latest
            newLabel = u' [' + u'Latest' + u' ' + label + u']'
            thumbnail = u'latest'
        else:
            newOrder = u'/atoz' # Alphanumerical
            newLabel = u' [' + 'A - Z' + u' ' + label + u']'
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
    
    def AddPageLink(self, category, categoryLabel, order, previous, page, listItems):
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
    
        url = self.GetURLStart() + u'&category=' + mycgi.URLEscape(category) + u'&title=' + mycgi.URLEscape(categoryLabel) + u'&order=' + mycgi.URLEscape(order) + u'&page=' + mycgi.URLEscape(page)
        listItems.append( (url,newListItem,True) )
    
    
    #==============================================================================
    # AddPageToListItems
    #
    # Add the shows from a particular page to the listItem array
    #==============================================================================
    
    def AddPageToListItems( self, category, label, order, page, listItems ):
        """
        {"count":50,"results":[
            {    "title":"The Function Room",
                 "url":"/4od/the-function-room",
                 "img":"http://cache.channel4.com/assets/programmes/images/the-function-room/7d5d701c-f7f8-4357-a128-67cac7896f95_200x113.jpg"
            },...        
        """
        try:
            jsonText = None
            pageInt = int(page)
        
            url = categoryUrl % (category, order, u'/page-%s' % page)
                
            jsonText = self.httpManager.GetWebPage(url, 963)
    
            jsonData = _json.loads(jsonText)
            
            results = jsonData[u'results']

            for entry in results:
                id = entry[u'url']
                pattern = u'/4od/(.+)'
                match = re.search(pattern, id, re.DOTALL | re.IGNORECASE)
                
                showId = match.group(1)
                thumbnail = entry[u'img']
                progTitle = unicode(entry[u'title'])
                progTitle = progTitle.replace( u'&amp;', u'&' )
                progTitle = progTitle.replace( u'&pound;', u'£' )
                
                newListItem = xbmcgui.ListItem( progTitle )
                newListItem.setThumbnailImage(thumbnail)
                newListItem.setInfo(u'video', {u'Title': progTitle})
                url = self.GetURLStart() + u'&category=' + category + u'&show=' + mycgi.URLEscape(showId) + u'&title=' + mycgi.URLEscape(progTitle)
                listItems.append( (url,newListItem,True) )

            nextPageCount = jsonData[u'nextPageCount']                 
            if nextPageCount == 0:
                return False

            return True
        
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
            
        if pageInt == 1 and (count is None or count > 10):
            try:
                self.AddExtraLinks(category, label, order, listItems)
            except (Exception) as exception:
                exception = LoggingException.fromException(exception)
            
                # 'Error processing web page', 'Cannot show Category'
                exception.addLogMessage(self.language(30785))
                exception.process(self.language(30780), self.language(30785), severity = xbmc.LOGWARNING)
    
        if pageInt > 1:
            self.AddPageLink(category, label, order, True, unicode(pageInt - 1), listItems)

        try:
            moreShows = self.AddPageToListItems( category, label, order, page, listItems )
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
        
            # 'Error processing web page', 'Cannot show Most Popular/A-Z/Latest'
            exception.addLogMessage(self.language(30780))
            exception.process(self.language(30785), self.language(30780), severity = xbmc.LOGWARNING)
        
            return False    


        if moreShows:
            nextPage = unicode(pageInt + 1)
            self.AddPageLink(category, label, order, False, nextPage, listItems)
        
        xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
        xbmcplugin.setContent(handle=self.pluginHandle, content=u'tvshows')
        xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
    
        return True
    
    #==============================================================================
    
    def ShowEpisodes( self, showId, showTitle, season ):
        self.log(unicode(( showId, showTitle )), xbmc.LOGDEBUG)
        
        episodeList = EpisodeList(self.GetURLStart(), showUrl, self.httpManager, self.watchedEnabled)
            
        try:
           episodeList.initialise(showId, showTitle, season, self.dataFolder)
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
        
            # 'Error processing web page', 'Cannot show Most Popular/A-Z/Latest'
            exception.addLogMessage(self.language(30740))
            exception.process(self.language(30735), self.language(30740), severity = self.logLevel(xbmc.LOGERROR))
        
            return False    
    
        listItems = episodeList.createListItems(mycgi, self.resumeEnabled, self)
    
        xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
        xbmcplugin.setContent(handle=self.pluginHandle, content=u'episodes')
        xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
    
        return True

    #==============================================================================
    def GetAuthentication(self, uriData):
        token = uriData.find(u'token').string
        cdn = uriData.find(u'cdn').string
        
        self.log(u"cdn: %s" % cdn, xbmc.LOGDEBUG)
        self.log(u"token: %s" % token, xbmc.LOGDEBUG)
        
        """
        x = fourOD_token_decoder.X()
        filename = x.decrypt(740, -401)
        nm = x.decrypt(738, -403)
        c2 = x.decrypt(736, -397)
        c2b = x.decrypt(737, -402)
        c1 = x.decrypt(732, -393)
        c3 = x.decrypt(735, -396)
        c4 = x.decrypt(734, -399)
        """
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
            exception.addLogMessage(self.language(30504) + swfDefault)
            exception.process(u'', u'', severity = xbmc.LOGDEBUG)
            raise exception

        
        
    
    #==============================================================================
    def GetSwfPlayer(self):
        try:
            jsHtml = None
            jsHtml = self.httpManager.GetWebPage(javascriptUrl, 30001)
           
            pattern = u"options.swfPath = \"(/swf/mobileplayer-10.2.0-1.43.swf)\";"
            match = re.search(pattern, jsHtml, re.DOTALL | re.IGNORECASE)
            
            swfPlayer = urlRoot + match.group(1)
            
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
        
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
        playPath = re.search(u'(mp4:.*)', streamUri).group(1)
        if "ll."  not in streamUri: 
            app = app + u"?ovpfv=1.1&" + auth
        else:
            playPath += "?" + auth

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
    
    #==============================================================================
    def getRTMPUrl(self, showId, episodeId):
        playUrl = None

        try:    
            assetUrl = aisUrl % episodeId
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
    
    
    def PlayEpisode( self, showId, seriesNumber, episodeNumber, episodeId, title, thumbnail, premiereDate, resumeFlag ):
        self.log (u'PlayEpisode showId: ' + showId, xbmc.LOGDEBUG)
        self.log (u'PlayEpisode episodeId: ' + episodeId, xbmc.LOGDEBUG)
        self.log (u'PlayEpisode title: ' + title, xbmc.LOGDEBUG)
        self.log (u'PlayEpisode , resumeFlag: ' + unicode(resumeFlag), xbmc.LOGDEBUG)
    
        self.episodeId = episodeId
        try:
            # "Getting video stream url"
            self.dialog.update(10, self.language(30700))
            (playUrl, rtmpVar) = self.getRTMPUrl(showId.lower(), episodeId)
        except (LoggingException) as exception:
            # Error getting RTMP url
            exception.addLogMessage(self.language(30965))
            exception.process(u"", u"", severity = self.logLevel(xbmc.LOGERROR))
            
            self.dialog.close()
            return False
    
        if self.dialog.iscanceled():
            return False
        # "Getting episode information"
        self.dialog.update(30, self.language(30710))
        self.log (u'rtmpVar: %s' % unicode(rtmpVar))
    
        # If we can't get rtmp then don't do anything
        # TODO Error message
        if rtmpVar is None:
            return False

        """
        episodeList = EpisodeList(self.GetURLStart(), showUrl, self.httpManager)
        episodeList.initialise(showId, title, season = '')
        episodeDetail = episodeList.GetEpisodeDetail(episodeId)
        
        (infoLabels, thumbnail) = episodeList.getInfolabelsAndLogo(episodeDetail)
        """
        infoLabels = {
                        u'Title': title, 
                        u'Premiered': premiereDate
                    }
                    
        try:    
            infoLabels[u'Season'] = int(seriesNumber)
        except:
            pass

        try:    
            infoLabels[u'Episode'] = int(episodeNumber)
        except:
            pass

        self.AddSocksToRTMP(rtmpVar)
        defaultFilename = self.getDefaultFilename(showId, seriesNumber, episodeNumber)

        subtitles = None
        if self.addon.getSetting( u'subtitles' ) == u'true':
            subtitles = Subtitle_4oD(self.httpManager, self.log, self.subtitleFilePath, self.noSubtitleFilePath)
            subtitles.SetEpisodeId(episodeId)
            #subtitles.SetHasSubtitle(episodeDetail.hasSubtitles)

        return self.PlayOrDownloadEpisode(infoLabels, thumbnail, rtmpVar, defaultFilename, subtitles = subtitles, resumeKey = episodeId, resumeFlag = resumeFlag)

    def GetPlayer(self, pid, live, playerName):
        if self.watchedEnabled:
            player = WatchedPlayer()
            player.initialise(live, playerName, self.GetWatchedPercent(), pid, self.resumeEnabled, self.log)
            return player
        elif self.resumeEnabled:
            player = ResumePlayer()
            player.init(pid, live, self.GetProviderId())
            return player
        else:
            return super(FourODProvider, self).GetPlayer(pid, live, playerName)
        

class Subtitle_4oD(Subtitle):
    
    def __init__(self, httpManager, log, noSubtitleFilePath, subtitleFilePath):
        self.log = log
        self.httpManager = httpManager
        self.subtitleFilePath = subtitleFilePath
        self.noSubtitleFilePath = noSubtitleFilePath
    
    def SetEpisodeId(self, episodeId):
        self.episodeId = episodeId
    
    def SetHasSubtitle(self, hasSubtitles):
        self.hasSubtitles = hasSubtitles
    
    def GetSubtitleFile(self, filename = None):
        subtitle = None 
        subtitle = self.httpManager.GetWebPage( u"http://ais.channel4.com/subtitles/%s" % self.episodeId, 40000 )
        
        self.log(u'Subtitle code: ' + unicode(self.httpManager.GetLastCode()), xbmc.LOGDEBUG )
        self.log(u'Subtitle filename: ' + unicode(filename), xbmc.LOGDEBUG)
    
        if subtitle is not None:
            self.log(u'Subtitle file length: ' + unicode(len(subtitle)), xbmc.LOGDEBUG)
    
        self.log(u'httpManager.GetLastCode(): ' + unicode(self.httpManager.GetLastCode()), xbmc.LOGDEBUG)
    
        if (subtitle is None or self.httpManager.GetLastCode() == 404 or len(subtitle) == 0):
            if self.hasSubtitles is True:
                self.log(u'No subtitles available', xbmc.LOGWARNING )
            subtitleFile = self.noSubtitleFilePath
        else:
            if filename is None:
                subtitleFile = self.subtitleFilePath
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
    
