# -*- coding: utf-8 -*-

import re
import sys
from time import mktime,strptime
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

from irishtvplayer import IrishTVPlayer
from provider import Provider
import HTMLParser

from BeautifulSoup import BeautifulSoup
from BeautifulSoup import BeautifulStoneSoup

urlRoot = u"http://www.rte.ie"
rootMenuUrl = u"http://www.rte.ie/player/ie/"
showUrl = u"http://www.rte.ie/player/ie/show/%s/"

flashJS = u"http://static.rasset.ie/static/player/js/flash-player.js"
configUrl = u"http://www.rte.ie/playerxl/config/config.xml"

playerJSDefault = u"http://static.rasset.ie/static/player/js/player.js?v=5"
searchUrlDefault = u"http://www.rte.ie/player/ie/search/?q="
swfDefault = u"http://www.rte.ie/player/assets/player_468.swf"
"""
swfLiveDefault = u"http://www.rte.ie/static/player/swf/osmf2_2013_06_25b.swf"
swfLiveDefault = u"http://www.rte.ie/static/player/swf/osmf2_541_2012_11_14.swf"
"""
swfLiveDefault = u"http://www.rte.ie/player/assets/player_454.swf"
defaultLiveTVPage = u"/player/ie/live/8/"

class RTEProvider(Provider):

#    def __init__(self):
#        self.cache = cache

    def GetProviderId(self):
        return u"RTE"

    def ExecuteCommand(self, mycgi):
        return super(RTEProvider, self).ExecuteCommand(mycgi)

    def ShowRootMenu(self):
        self.log(u"", xbmc.LOGDEBUG)
        
        try:
            html = None
            html = self.httpManager.GetWebPage(rootMenuUrl, 60)
    
            if html is None or html == '':
                # Error getting %s Player "Home" page
                logException = LoggingException(self.language(30001) % self.GetProviderId())
                # 'Cannot show RTE root menu', Error getting RTE Player "Home" page
                logException.process(self.language(30002) % self.GetProviderId(), self.language(30001) % self.GetProviderId(), self.logLevel(xbmc.LOGERROR))
                return False
    
            soup = BeautifulSoup(html, selfClosingTags=['img'])
            categories = soup.find(u'div', u"dropdown-programmes")
    
            if categories == None:
                # "Can't find dropdown-programmes"
                logException = LoggingException(self.language(30003))
                # 'Cannot show RTE root menu', Error parsing web page
                logException.process(self.language(30002)  % self.GetProviderId(), self.language(30780), self.logLevel(xbmc.LOGERROR))
                #raise logException
                return False
            
            listItems = []
    
            try:
                listItems.append( self.CreateSearchItem() )
            except (Exception) as exception:
                if not isinstance(exception, LoggingException):
                    exception = LoggingException.fromException(exception)

                # Not fatal, just means that we don't have the search option
                exception.process(severity = xbmc.LOGWARNING)
    
            if False == self.AddAllLinks(listItems, categories, autoThumbnails = True):
                return False
            
            newLabel = u"Live"
            thumbnailPath = self.GetThumbnailPath(newLabel)
            newListItem = xbmcgui.ListItem( label=newLabel )
            newListItem.setThumbnailImage(thumbnailPath)
            url = self.GetURLStart() + u'&live=1'
            listItems.append( (url, newListItem, True) )

            xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
            xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
            
            return True
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            if html is not None:
                msg = "html:\n\n%s\n\n" % html
                exception.addLogMessage(msg)
                
            # Cannot show root menu
            exception.addLogMessage(self.language(30010))
            exception.process(severity = self.logLevel(xbmc.LOGERROR))
            return False

    """
    listshows: If '1' list the shows on the main page, otherwise process the sidebar. The main page links to programmes or specific episodes, the sidebar links to categories or sub-categories
    episodeId: id of the show to be played, or the id of a show where more than one episode is available
    listavailable: If '1' process the specified episode as one of at least one episodes available, i.e. list all episodes available
    search: If '1' perform a search
    page: url, relative to www.rte.ie, to be processed. Not passed when an episodeId is given.
    live: If '1' show live menu
    """
    def ParseCommand(self, mycgi):
        (listshows, episodeId, listAvailable, search, page, live, resume) = mycgi.Params( u'listshows', u'episodeId', u'listavailable', u'search', u'page', u'live', u'resume'  )
        self.log(u"", xbmc.LOGDEBUG)
        self.log(u"listshows: %s, episodeId %s, listAvailable %s, search %s, page %s, resume: %s" % (str(listshows), episodeId, str(listAvailable), str(search), page, str(resume)), xbmc.LOGDEBUG)

       
        if episodeId <> '':
            resumeFlag = False
            if resume <> u'':
                resumeFlag = True
           
            #return self.PlayEpisode(episodeId)
            return self.PlayVideoWithDialog(self.PlayEpisode, (episodeId, resumeFlag))

        if search <> '':
            if page == '':
                return self.DoSearch()
            else:
                return self.DoSearchQuery( queryUrl = urlRoot + page)
                 
        if page == '':
            if live <> '':
                return self.ShowLiveMenu()
            
            # "Can't find 'page' parameter "
            logException = LoggingException(logMessage = self.language(30030))
            # 'Cannot proceed', Error processing command
            logException.process(self.language(30010), self.language(30780), self.logLevel(xbmcc.LOGERROR))
            return False

        page = page
        # TODO Test this
        self.log(u"page = %s" % page, xbmc.LOGDEBUG)
        #self.log(u"type(page): " + repr(type(page)), xbmc.LOGDEBUG)
        ##page = mycgi.URLUnescape(page)
        #self.log(u"page = %s" % page, xbmc.LOGDEBUG)
        #self.log(u"type(mycgi.URLUnescape(page)): " + repr(type(page)), xbmc.LOGDEBUG)
#        self.log(u"mycgi.URLUnescape(page) = %s" % page, xbmc.LOGDEBUG)

        if u' ' in page:
            page = page.replace(u' ', u'%20')

        try:
            self.log(u"urlRoot: " + urlRoot + u", page: " + page )
            html = None
            html = self.httpManager.GetWebPage( urlRoot + page, 1800 )
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            if html is not None:
                msg = "html:\n\n%s\n\n" % html
                exception.addLogMessage(msg)
                
            # Error getting web page
            exception.addLogMessage(self.language(30050))
            exception.process(severity = self.logLevel(xbmc.LOGERROR))
            return False

        if live <> '':
            #return self.PlayLiveTV(html)
            return self.PlayVideoWithDialog(self.PlayLiveTV, (html, None))
            
        if listshows <> u'':
            return self.ListShows(html)
        
        if listAvailable <> u'':
            
            soup = BeautifulSoup(html)
            availableLink = soup.find('a', 'button-more-episodes')
            
            if availableLink is None:
                pattern= "/player/ie/show/(.+)/"
                match=re.search(pattern, html, re.DOTALL)
                
                if match is not None:
                    episodeId = match.group(1) 
                    resumeFlag = False
                    if resume <> u'':
                        resumeFlag = True

                    return self.PlayVideoWithDialog(self.PlayEpisode, (episodeId, resumeFlag))

                
            return self.ListAvailable(html)

        return self.ListSubMenu(html)

    def GetLivePageUrl(self):
        
        try:
            html = None
            html = self.httpManager.GetWebPage(rootMenuUrl, 60)
    
            soup = BeautifulSoup(html, selfClosingTags=['img'])
            page = soup.find('ul', 'sidebar-live-list').find('a')['href']
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
        
            if html is not None:
                msg = "html:\n\n%s\n\n" % html
                exception.addLogMessage(msg)
                
            exception.addLogMessage(self.language(30520) + defaultLiveTVPage)
            exception.process('', '', severity = xbmc.LOGWARNING)

            page = defaultLiveTVPage
            
        return page

    def ShowLiveMenu(self):
        self.log(u"", xbmc.LOGDEBUG)
        listItems = []
        
        try:
            html = None
            page = self.GetLivePageUrl()
            html = self.httpManager.GetWebPage(urlRoot + page, 60)
            soup = BeautifulSoup(html, selfClosingTags=['img'])
    
            schedule = soup.find('div', 'live-schedule-strap clearfix')
            liList = schedule.findAll('li')

            for li in liList:
                logoName = li.find('span', {'class':re.compile('live-logo')})
                channel = logoName.text
                thumbnailPath = self.GetThumbnailPath((channel.replace(u'RT\xc9 ', '')).replace(' ', ''))
                page = li.a['href']

                infoList=li.findAll('span', "live-channel-info")
                programme = ""
                for info in infoList:
                    text = info.text.replace("&nbsp;", "")
                    if len(text) == 0:
                        continue
                    
                    comma = ""
                    if len(programme) == 0:
                        programme = info.text
                    else:
                        programme = programme + ", " + info.text

                programme = programme.replace('&#39;', "'")
                newListItem = xbmcgui.ListItem( label=programme )
                newListItem.setThumbnailImage(thumbnailPath)
                newListItem.setProperty("Video", "true")
                #newListItem.setProperty('IsPlayable', 'true')

                url = self.GetURLStart() + u'&live=1' + u'&page=' + mycgi.URLEscape(page)
                listItems.append( (url, newListItem, False) )
        
            xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
            xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
            
            return True
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            if html is not None:
                msg = "html:\n\n%s\n\n" % html
                exception.addLogMessage(msg)
                
            # Error getting Live TV information
            exception.addLogMessage(self.language(30047))
            exception.process(severity = self.logLevel(xbmc.LOGERROR))
            return False

    def CreateSearchItem(self, pageUrl = None):
        try:
            if pageUrl is None or len(pageUrl) == 0:
                newLabel = u"Search"
                url = self.GetURLStart() + u'&search=1'
            else:
                newLabel = u"More..."
                url = self.GetURLStart() + u'&search=1' + u'&page=' + mycgi.URLEscape(pageUrl)
  
            thumbnailPath = self.GetThumbnailPath(u"Search")
            newListItem = xbmcgui.ListItem( label=newLabel )
            newListItem.setThumbnailImage(thumbnailPath)
            
            return (url, newListItem, True)
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            # Error creating Search item
            exception.addLogMessage(self.language(30056))
            raise exception

    #==============================================================================

    def AddAllLinks(self, listItems, html, listshows = False, autoThumbnails = False):
        htmlparser = HTMLParser.HTMLParser()
        
        try:
            for link in html.findAll(u'a'):
                page = link[u'href']
                newLabel = htmlparser.unescape(link.contents[0])
                thumbnailPath = self.GetThumbnailPath(newLabel.replace(u' ', u''))
                newListItem = xbmcgui.ListItem( label=newLabel)
                newListItem.setThumbnailImage(thumbnailPath)
    
                url = self.GetURLStart() + u'&page=' + mycgi.URLEscape(page)
    
                # "Most Popular" does not need a submenu, go straight to episode listing
                if listshows or u"Popular" in newLabel:
                    url = url + u'&listshows=1'
    
                self.log(u"url: %s" % url, xbmc.LOGDEBUG)
                listItems.append( (url,newListItem,True) )

            return True
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            if html is not None:
                msg = "html:\n\n%s\n\n" % html
                exception.addLogMessage(msg)
                
            # Error adding links
            exception.addLogMessage(self.language(30047))
            exception.process(severity = self.logLevel(xbmc.LOGERROR))
            return False

    #==============================================================================

    def ListAToZ(self, atozTable):
        self.log(u"", xbmc.LOGDEBUG)
        listItems = []

        if False == self.AddAllLinks(listItems, atozTable, listshows = True):
            return False        

        xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
        xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )

        return True
        
    #==============================================================================

    def ListSubMenu(self, html):
        htmlparser = HTMLParser.HTMLParser()
        try:
            soup = BeautifulSoup(html, selfClosingTags=[u'img'])
            aside = soup.find(u'aside')
    
            if aside is None:
                return self.ListLatest(soup)
    
            atozTable = soup.find(u'table', u'a-to-z')
            
            if atozTable is not None:
                return self.ListAToZ(atozTable)
    
            listItems = []
    
            categories = aside.findAll(u'a')
            for category in categories:
                href = category[u'href']
                
                title = htmlparser.unescape(category.contents[0])
    
                newListItem = xbmcgui.ListItem( label=title )
                newListItem.setThumbnailImage(title.replace(u' ', u''))
                url = self.GetURLStart() + u'&page=' + mycgi.URLEscape(href) + u'&listshows=1'
                listItems.append( (url, newListItem, True) )
                self.log(u"url: %s" % url, xbmc.LOGDEBUG)
            
            xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
            xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
    
            return True
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            if html is not None:
                msg = "html:\n\n%s\n\n" % html
                exception.addLogMessage(msg)
                
            # Error listing submenu
            exception.addLogMessage(self.language(30048))
            exception.process(severity = self.logLevel(xbmc.LOGERROR))
            return False

    #==============================================================================
    
    def ListLatest(self, soup):
        self.log(u"", xbmc.LOGDEBUG)
        listItems = []
    
        calendar = soup.find(u'table', u'calendar')
    
        links = calendar.findAll(u'a')
        links.reverse()

        # Today
        page = links[0][u'href']
        newLabel = u"Today"
        newListItem = xbmcgui.ListItem( label=newLabel )
        match=re.search( u"/([0-9][0-9][0-9][0-9]-[0-9][0-9]?-[0-9][0-9]?)/", page)
        if match is None:
            self.log(u"No date match for page href: '%s'" % page, xbmc.LOGWARNING)
        else:
            url = self.GetURLStart() + u'&page=' + mycgi.URLEscape(page) + u'&listshows=1'
            listItems.append( (url,newListItem,True) )
            
        # Yesterday
        page = links[1][u'href']
        newLabel = u"Yesterday"
        newListItem = xbmcgui.ListItem( label=newLabel )
        match=re.search( u"/([0-9][0-9][0-9][0-9]-[0-9][0-9]?-[0-9][0-9]?)/", page)
        if match is None:
            self.log(u"No date match for page href: '%s'" % page, xbmc.LOGWARNING)
        else:
            url = self.GetURLStart() + u'&page=' + mycgi.URLEscape(page) + u'&listshows=1'
            listItems.append( (url,newListItem,True) )
        
        # Weekday
        page = links[2][u'href']
        match=re.search( u"/([0-9][0-9][0-9][0-9]-[0-9][0-9]?-[0-9][0-9]?)/", page)
        if match is None:
            self.log(u"No date match for page href: '%s'" % page, xbmc.LOGWARNING)
        else:
            linkDate = date.fromtimestamp(mktime(strptime(match.group(1), u"%Y-%m-%d")))
                
            newLabel = linkDate.strftime(u"%A")
            newListItem = xbmcgui.ListItem( label=newLabel )

            url = self.GetURLStart() + u'&page=' + mycgi.URLEscape(page) + u'&listshows=1'
            listItems.append( (url,newListItem,True) )
        
        # Weekday
        page = links[3][u'href']
        match=re.search( u"/([0-9][0-9][0-9][0-9]-[0-9][0-9]?-[0-9][0-9]?)/", page)
        if match is None:
            self.log(u"No date match for page href: '%s'" % page, xbmc.LOGWARNING)
        else:
            linkDate = date.fromtimestamp(mktime(strptime(match.group(1), u"%Y-%m-%d")))
                
            newLabel = linkDate.strftime(u"%A")
            newListItem = xbmcgui.ListItem( label=newLabel )

            url = self.GetURLStart() + u'&page=' + mycgi.URLEscape(page) + u'&listshows=1'
            listItems.append( (url,newListItem,True) )
        
        for link in links[4:]:
            page = link[u'href']
    
            match=re.search( u"/([0-9][0-9][0-9][0-9]-[0-9][0-9]?-[0-9][0-9]?)/", page)
            if match is None:
                self.log(u"No date match for page href: '%s'" % page, xbmc.LOGWARNING)
                continue;
    
            linkDate = date.fromtimestamp(mktime(strptime(match.group(1), u"%Y-%m-%d")))
            
            newLabel = linkDate.strftime(u"%A, %d %B %Y")
            newListItem = xbmcgui.ListItem( label=newLabel)
    
            url = self.GetURLStart() + u'&page=' + mycgi.URLEscape(page) + u'&listshows=1'
            listItems.append( (url,newListItem,True) )
    
        xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
        xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
        
        return True
    
    
    #==============================================================================
    
    def AddEpisodeToList(self, listItems, episode):
        self.log(u"", xbmc.LOGDEBUG)
        
        try:
            htmlparser = HTMLParser.HTMLParser()
    
            href = episode[u'href']
            title = htmlparser.unescape( episode.find(u'span', u"thumbnail-title").contents[0] )
            date = episode.find(u'span', u"thumbnail-date").contents[0]                    
            #description = ...
            thumbnail = episode.find(u'img', u'thumbnail')[u'src']
        
            newLabel = title + u", " + date
                                            
            newListItem = xbmcgui.ListItem( label=newLabel )
            newListItem.setThumbnailImage(thumbnail)
            
            if self.addon.getSetting( u'RTE_descriptions' ) == u'true':
                infoLabels = self.GetEpisodeInfo(self.GetEpisodeIdFromURL(href))
            else:
                infoLabels = {u'Title': title, u'Plot': title}
                
            newListItem.setInfo(u'video', infoLabels)
            newListItem.setProperty(u"Video", u"true")
            #newListItem.setProperty('IsPlayable', 'true')
        
            self.log(u"label == " + newLabel, xbmc.LOGDEBUG)
        
            if u"episodes available" in date:
                url = self.GetURLStart()  + u'&listavailable=1' + u'&page=' + mycgi.URLEscape(href)
                folder = True
            else:
                newListItem.setProperty("Video", "true")
                #newListItem.setProperty('IsPlayable', 'true')

                folder = False
                match = re.search( u"/player/[^/]+/show/([0-9]+)/", href )
                if match is None:
                    self.log(u"No show id found in page href: '%s'" % href, xbmc.LOGWARNING)
                    return
            
                episodeId = match.group(1)
        
                url = self.GetURLStart() + u'&episodeId=' +  mycgi.URLEscape(episodeId)
        
                if self.resumeEnabled:
                    resumeKey = episodeId
                    self.ResumeListItem(url, newLabel, newListItem, resumeKey)
                    
            listItems.append( (url, newListItem, folder) )
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            msg = u"episode:\n\n%s\n\n" % utils.drepr(episode)
            exception.addLogMessage(msg)

            # Error getting episode details
            exception.addLogMessage(self.language(30099))
            exception.process(self.logLevel(xbmc.LOGWARNING))
                   
    
    
    #==============================================================================
    
    def ListShows(self, html):
        self.log(u"", xbmc.LOGDEBUG)
        listItems = []
    
        try:
            soup = BeautifulSoup(html, selfClosingTags=[u'img'])
            episodes = soup.findAll(u'a', u"thumbnail-programme-link")

            for episode in episodes:
                self.AddEpisodeToList(listItems, episode)

            xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
            xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
    
            return True
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
    
            if html is not None:
                msg = "html:\n\n%s\n\n" % html
                exception.addLogMessage(msg)
                
            # Error getting list of shows
            exception.addLogMessage(self.language(30049))
            # Error getting list of shows
            exception.process(severity = self.logLevel(xbmc.LOGERROR))
            return False
    
    
    #==============================================================================
    def GetTextFromElement(self, element):
        textList = element.contents
        text = u""
        
        for segment in textList:
            text = text + segment.string
                
        htmlparser = HTMLParser.HTMLParser()
        return htmlparser.unescape(text)    
        
        
    def AddEpisodeToSearchList(self, listItems, article):
        """
        <article class="search-result clearfix"><a
                href="/player/ie/show/10098947/" class="thumbnail-programme-link"><span
                    class="sprite thumbnail-icon-play">Watch Now</span><img class="thumbnail" alt="Watch Now"
                    src="http://img.rasset.ie/0006d29f-261.jpg"></a>
            <h3 class="search-programme-title"><a href="/player/ie/show/10098947/">Nuacht and <span class="search-highlight">News</span> with Signing</a></h3>
            <p class="search-programme-episodes"><a href="/player/ie/show/10098947/">Sun 30 Dec 2012</a></p>
            <!-- p class="search-programme-date">30/12/2012</p -->
            <p class="search-programme-description">Nuacht and <span class="search-highlight">News</span> with Signing.</p>
            <span class="sprite logo-rte-one search-channel-icon">RTÉ 1</span>
        </article>
        """

        episodeLink = article.find(u'a', u"thumbnail-programme-link")
        href = episodeLink[u'href']
    
        title = self.GetTextFromElement( article.find(u'h3', u"search-programme-title").a )
        dateShown = article.findNextSibling(u'p', u"search-programme-episodes").a.text
        description = self.GetTextFromElement( article.findNextSibling(u'p', u"search-programme-description") )
        thumbnail = article.find('img', 'thumbnail')['src']
        
        title = title + u' [' + dateShown + u']'
    
        newLabel = title
                                        
        newListItem = xbmcgui.ListItem( label=newLabel)
        infoLabels = {u'Title': title, u'Plot': description, u'PlotOutline': description}
        newListItem.setInfo(u'video', infoLabels)
        newListItem.setThumbnailImage(thumbnail)

        match = re.search( u"/player/[^/]+/show/([0-9]+)/", href )
        if match is None:
            self.log(u"No show id found in page href: '%s'" % href, xbmc.LOGWARNING)
            return
    
        episodeId = match.group(1)
    
        url = self.GetURLStart() + u'&episodeId=' +  mycgi.URLEscape(episodeId)
    
        if self.resumeEnabled:
            resumeKey = episodeId
            self.ResumeListItem(url, newLabel, newListItem, resumeKey)
            
        listItems.append( (url, newListItem, True) )
        
    #==============================================================================
    
    def ListSearchShows(self, html):
        self.log(u"", xbmc.LOGDEBUG)
        listItems = []
        
        try:
            soup = BeautifulSoup(html, selfClosingTags=[u'img'])
            articles = soup.findAll(u"article", u"search-result clearfix")
        
            if len(articles) > 0:
                for article in articles:
                    self.AddEpisodeToSearchList(listItems, article)
    
                current = soup.find('li', 'dot-current')
                
                if current is not None:
                    moreResults = current.findNextSibling('li', 'dot')
                    
                    if moreResults is not None:
                        try:
                            listItems.append( self.CreateSearchItem(moreResults.a['href']) )
                        except (Exception) as exception:
                            if not isinstance(exception, LoggingException):
                                exception = LoggingException.fromException(exception)
            
                            # Not fatal, just means that we don't have the search option
                            exception.process(severity = self.logLevel(xbmc.LOGWARNING))
                
        
            xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
            xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
        
            return True
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
        
            if html is not None:
                msg = "html:\n\n%s\n\n" % html
                exception.addLogMessage(msg)
                
            # Error getting list of shows
            exception.addLogMessage(self.language(30049))
            exception.process(severity = self.logLevel(xbmc.LOGERROR))
            return False

    #==============================================================================
    
    def ListAvailable(self, html):
        self.log(u"", xbmc.LOGDEBUG)
        listItems = []
        
        try:        
            soup = BeautifulSoup(html, selfClosingTags=[u'img'])
            count = int(soup.find(u'meta', { u'name' : u"episodes_available"} )[u'content'])
    
            availableEpisodes = soup.findAll(u'a', u"thumbnail-programme-link")
        
            for index in range ( 0, count ):
                self.AddEpisodeToList(listItems, availableEpisodes[index])
    
            xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
            xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
    
            return True
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
    
            if html is not None:
                msg = "html:\n\n%s\n\n" % html
                exception.addLogMessage(msg)
                
            # Error getting count of available episodes
            exception.addLogMessage(self.language(30045))
            exception.process(self.language(30046), self.language(30045), self.logLevel(xbmc.LOGERROR))
            return False
    
    #==============================================================================
    
    def GetSWFPlayer(self):
        self.log(u"", xbmc.LOGDEBUG)
        
        try:
            xml = self.httpManager.GetWebPage(configUrl, 20000)
            soup = BeautifulStoneSoup(xml)
            
            swfPlayer = soup.find("player")['url']

            if swfPlayer.find('.swf') > 0:
                swfPlayer=re.search("(.*\.swf)", swfPlayer).groups()[0]
                
            if swfPlayer.find('http') == 0:
                # It's an absolute URL, do nothing.
                pass
            elif swfPlayer.find('/') == 0:
                # If it's a root URL, append it to the base URL:
                swfPlayer = urljoin(urlRoot, swfPlayer)
            else:
                # URL is relative to config.xml 
                swfPlayer = urljoin(configUrl, swfPlayer)
                
            return swfPlayer
        
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            # Unable to determine swfPlayer URL. Using default: %s
            exception.addLogMessage(self.language(30520) % swfDefault)
            exception.process(severity = self.logLevel(xbmc.LOGWARNING))
            return swfDefault

    
    def GetLiveSWFPlayer(self):
        self.log(u"", xbmc.LOGDEBUG)
    
        return swfLiveDefault

    #==============================================================================

    def GetThumbnailFromEpisode(self, episodeId, soup = None):
        self.log(u"", xbmc.LOGDEBUG)

        try:
            html = None
            if soup is None:
                html = self.httpManager.GetWebPage(showUrl % episodeId, 20000)
                soup = BeautifulSoup(html, selfClosingTags=[u'img'])
            
            image = soup.find(u'meta', { u'property' : u"og:image"} )[u'content']
            return image
        
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
            
            if html is not None:
                msg = "html:\n\n%s\n\n" % html
                exception.addLogMessage(msg)
                
            # Error processing web page
            exception.addLogMessage(self.language(30780) + ": " + (showUrl % episodeId))
            exception.process(u"Error getting thumbnail", "", self.logLevel(xbmc.LOGWARNING))
            raise exception
    

    #==============================================================================
    
    def GetEpisodeInfo(self, episodeId, soup = None):
        self.log(u"", xbmc.LOGDEBUG)
    
        try:
            html = None
            if soup is None:
                html = self.httpManager.GetWebPage(showUrl % episodeId, 20000)
                soup = BeautifulSoup(html, selfClosingTags=[u'img'])
    
            title = soup.find(u'meta', { u'name' : u"programme"} )[u'content']
            description = soup.find(u'meta', { u'name' : u"description"} )[u'content']
            categories = soup.find(u'meta', { u'name' : u"categories"} )[u'content']
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
    
            if html is not None:
                msg = "html:\n\n%s\n\n" % html
                exception.addLogMessage(msg)
                
            # Error processing web page %s
            exception.addLogMessage(self.language(30780) + ": " + (showUrl % episodeId))
            exception.process(u"Error getting episode information", "", self.logLevel(xbmc.LOGWARNING))
    
            # Initialise values in case they are None
            if title is None:
                title = 'Unknown ' + episodeId
                
            description = unicode(description)
            categories = unicode(categories)
        
        infoLabels = {u'Title': title, u'Plot': description, u'PlotOutline': description, u'Genre': categories}
    
        self.log(u"Title: %s" % title, xbmc.LOGDEBUG)
        self.log(u"infoLabels: %s" % infoLabels, xbmc.LOGDEBUG)
        return infoLabels
    
    #==============================================================================
    
    def PlayEpisode(self, episodeId, resumeFlag):
        self.log(u"%s" % episodeId, xbmc.LOGDEBUG)
        
        # "Getting SWF url"
        self.dialog.update(5, self.language(30089))
        swfPlayer = self.GetSWFPlayer()
    
        try:
            if self.dialog.iscanceled():
                return False
            # "Getting episode web page"
            self.dialog.update(15, self.language(30090))
            feedProcessStatus = 0
            html = None
            html = self.httpManager.GetWebPage(showUrl % episodeId, 20000)
    
            soup = BeautifulSoup(html, selfClosingTags=[u'img'])
            feedsPrefix = soup.find(u'meta', { u'name' : u"feeds-prefix"} )[u'content']

            if self.dialog.iscanceled():
                return False
            # "Getting episode info"
            self.dialog.update(25, self.language(30084))
            infoLabels = self.GetEpisodeInfo(episodeId, soup)
            thumbnail = self.GetThumbnailFromEpisode(episodeId, soup)
    
            urlGroups = None
            feedProcessStatus = 1

            if self.dialog.iscanceled():
                return False
            # "Getting playpath data"
            self.dialog.update(35, self.language(30091))
            urlGroups = self.GetStringFromURL(feedsPrefix + episodeId, u"\"url\": \"(/[0-9][0-9][0-9][0-9]/[0-9][0-9][0-9][0-9]/)([a-zA-Z0-9]+/)?(.+).f4m\"", 20000)
            feedProcessStatus = 2
            if urlGroups is None:
                # Log error
                self.log(u"urlGroups is None", xbmc.LOGERROR)
                return False
    
            (urlDateSegment, extraSegment, urlSegment) = urlGroups
    
            rtmpStr = u"rtmpe://fmsod.rte.ie:1935/rtevod"
            app = u"rtevod"
            swfVfy = swfPlayer
            playPath = u"mp4:%s%s/%s_512k.mp4" % (urlDateSegment, urlSegment, urlSegment)
            playURL = u"%s app=%s playpath=%s swfurl=%s swfvfy=true" % (rtmp, app, playPath, swfVfy)
    
            rtmpVar = rtmp.RTMP(rtmp = rtmpStr, app = app, swfVfy = swfVfy, playPath = playPath)
            self.AddSocksToRTMP(rtmpVar)
            defaultFilename = self.GetDefaultFilename(infoLabels[u'Title'], episodeId)
    
            self.log(u"(%s) playUrl: %s" % (episodeId, playURL), xbmc.LOGDEBUG)
            
            return self.PlayOrDownloadEpisode(infoLabels, thumbnail, rtmpVar, defaultFilename, url = None, subtitles = None, resumeKey = episodeId, resumeFlag = resumeFlag)
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
    
            if html is not None:
                msg = "html:\n\n%s\n\n" % html
                exception.addLogMessage(msg)
            
            if feedProcessStatus == 1:
                # Exception while getting data from feed
                try:
                    feedUrl = 'http://feeds.rasset.ie/rteavgen/player/playlist/?itemId=%s&type=iptv&format=xml' % episodeId
                    html = self.httpManager.GetWebPageDirect(feedUrl)
                    
                    msg = "html:\n\n%s\n\n" % html
                    exception.addLogMessage(msg)
                except:
                    exception.addLogMessage("Execption getting " + feedUrl)

                try:
                    feedUrl = 'http://feeds.rasset.ie/rteavgen/player/playlist/?itemId=%s&type=iptv1&format=xml' % episodeId
                    html = self.httpManager.GetWebPageDirect(feedUrl)
                    
                    msg = "html:\n\n%s\n\n" % html
                    exception.addLogMessage(msg)
                except:
                    exception.addLogMessage("Execption getting " + feedUrl)
            # Error playing or downloading episode %s
            exception.addLogMessage(self.language(30051) % episodeId)
            # Error playing or downloading episode %s
            exception.process(self.language(30051) % ' ' , '', self.logLevel(xbmc.LOGERROR))
            return False
    

    def PlayLiveTV(self, html, dummy):
        """
          <li class="first-live-channel selected-channel">
              <a href="/player/ie/live/8/" class="live-channel-container">
              <span class="sprite live-logo-rte-one">RTÉ One</span>
              
                  <span class="sprite live-channel-now-playing">Playing</span>
              
              <span class="live-channel-info"><span class="live-time">Now:</span>The Works</span>
              <span class="live-channel-info"><span class="live-time">Next:</span>RTÉ News: Nine O&#39;Clock and Weather (21:00)</span></a>
          </li>
          
        """
        self.log(u"", xbmc.LOGDEBUG)
        
        swfPlayer = self.GetLiveSWFPlayer()
    
        liveChannels = {
                      u'RT\xc9 One' : u'rte1',
                      u'RT\xc9 Two' : u'rte2',
                      u'RT\xc9jr': u'rtejr',
                      u'RT\xc9 News Now' : u'newsnow'
                      }
        
        try:
            soup = BeautifulSoup(html, selfClosingTags=[u'img'])
            #liveTVInfo = soup.find('span', 'sprite live-channel-now-playing').parent
            liveTVInfo = soup.find('li', 'selected-channel')
            channel = liveTVInfo.find('span').string
            programme = liveTVInfo.find('span', 'live-channel-info').next.nextSibling
            programme = self.fullDecode(programme).replace('&#39;', "'")
            
            infoLabels = {u'Title': channel + u": " + programme }
            thumbnailPath = self.GetThumbnailPath((channel.replace(u'RT\xc9 ', '')).replace(' ', ''))
            
            rtmpStr = u"rtmp://fmsod.rte.ie/live/"
            app = u"live"
            swfVfy = swfPlayer
            playPath = liveChannels[channel]
    
            rtmpVar = rtmp.RTMP(rtmp = rtmpStr, app = app, swfVfy = swfVfy, playPath = playPath, live = True)
            self.AddSocksToRTMP(rtmpVar)
            
            self.Play(infoLabels, thumbnailPath, rtmpVar)
            
            return True
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
    
            if html is not None:
                msg = "html:\n\n%s\n\n" % html
                exception.addLogMessage(msg)
                
            # Error playing live TV
            exception.addLogMessage(self.language(30053))
            exception.process(severity = self.logLevel(xbmc.LOGERROR))
            return False
    


    def GetEpisodeIdFromURL(self, url):
        segments = url.split(u"/")
        segments.reverse()
    
        for segment in segments:
            if segment <> u'':
                return segment
    
    #==============================================================================
    def GetDefaultFilename(self, title, episodeId):
        if episodeId <> u"":
            #E.g. NAME.s01e12
            return title + u"_" + episodeId
    
        return title
    
   #==============================================================================
    def GetPlayerJSURL(self, html):
        try:
            soup = BeautifulSoup(html, selfClosingTags=[u'img'])
            # E.g. <script src="http://static.rasset.ie/static/player/js/player.js?v=3"></script>
            script = soup.find(src=re.compile("player.\js\?"))
        
            playerJS = script['src']
        
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
    
            if html is not None:
                msg = "html:\n\n%s\n\n" % html
                exception.addLogMessage(msg)
                
            # Error getting player.js url: Using default %s
            exception.addLogMessage(self.language(30055) % playerJSDefault)
            exception.process(severity = self.logLevel(xbmc.LOGWARNING))
            playerJS = playerJSDefault

        return playerJS
        
        
    def GetPlayer(self, pid, live):
        if self.resumeEnabled:
            player = IrishTVPlayer()
            player.init(pid,live)
            return player
        
        return super(RTEProvider, self).GetPlayer(pid, live)

    def GetSearchURL(self):
        try:
            rootMenuHtml = None
            html = None
            rootMenuHtml = self.httpManager.GetWebPage(rootMenuUrl, 60)
            playerJSUrl = self.GetPlayerJSURL(rootMenuHtml)
            
            html = self.httpManager.GetWebPage(playerJSUrl, 20000)

            programmeSearchIndex = html.find('Programme Search')
            match=re.search("window.location.href = \'(.*?)\'", html[programmeSearchIndex:])
            searchURL = match.group(1)
        
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
    
            if rootMenuHtml is not None:
                msg = "rootMenuHtml:\n\n%s\n\n" % rootMenuHtml
                exception.addLogMessage(msg)
                
            if html is not None:
                msg = "html:\n\n%s\n\n" % html
                exception.addLogMessage(msg)
                
            # Error getting search url: Using default %s
            exception.addLogMessage(self.language(30054) + searchUrlDefault)
            exception.process(severity = self.logLevel(xbmc.LOGWARNING))
            searchURL = searchUrlDefault

        return searchURL
        
    def DoSearchQuery( self, query = None, queryUrl = None):
        if query is not None:
            queryUrl = urlRoot + self.GetSearchURL() + mycgi.URLEscape(query)
             
        self.log(u"queryUrl: %s" % queryUrl, xbmc.LOGDEBUG)
        try:
            html = None
            html = self.httpManager.GetWebPage( queryUrl, 1800 )
            if html is None or html == '':
                # Data returned from web page: %s, is: '%s'
                logException = LoggingException(logMessage = self.language(30060) % ( __SEARCH__ + mycgi.URLEscape(query), html))
    
                # Error getting web page
                logException.process(self.language(30050), u'', severity = self.logLevel(xbmc.LOGWARNING))
                return False
    
            self.ListSearchShows(html)
    
            return True
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
    
            if html is not None:
                msg = "html:\n\n%s\n\n" % html
                exception.addLogMessage(msg)
                
            # Error performing query %s
            exception.addLogMessage(self.language(30052) % query)
            exception.process(severity = self.logLevel(xbmc.LOGERROR))
            return False
        
