# -*- coding: utf-8 -*-
import re
import sys
from time import mktime,strptime
from datetime import timedelta
from datetime import date

import xbmcplugin
import xbmcgui
import xbmc

import mycgi
import utils
from loggingexception import LoggingException
import rtmp

from provider import Provider

from BeautifulSoup import BeautifulSoup, NavigableString

import HTMLParser

urlRoot     = u"http://www.tv3.ie"
rootMenuUrl = u"http://www.tv3.ie/3player"
allShowsDefaultUrl  = u"http://www.tv3.ie/3player/allshows"
searchUrl = u"http://www.tv3.ie/player/assets/php/search.php"
calendarUrl = u"http://www.tv3.ie/player/assets/php/calendar.php"
swfDefault = "http://www.tv3.ie/player/assets/flowplayer/flash/flowplayer.commercial-3.2.7.swf"

class TV3Provider(Provider):

#    def __init__(self):
#        self.cache = cache

    def GetProviderId(self):
        return u"TV3"

    def ExecuteCommand(self, mycgi):
        return super(TV3Provider, self).ExecuteCommand(mycgi)

    def ShowRootMenu(self):
        self.log(u"", xbmc.LOGDEBUG)
        try:
            html = None
            html = self.httpManager.GetWebPage(rootMenuUrl, 300)
    
            if html is None or html == '':
                # Error getting %s Player "Home" page
                logException = LoggingException(logMessage = self.language(30001) % self.GetProviderId())
                # 'Cannot show TV3 root menu', Error getting TV3 Player "Home" page
                logException.process(self.language(30002) % self.GetProviderId(), self.language(30001) % self.GetProviderId(), logLevel)
                #raise logException
                return False
    
            #soup = BeautifulSoup(html, selfClosingTags=['img'])
            categories = self.GetCategories(html)
    
            if len(categories) == 0:
                # "Can't find dropdown-programmes"
                logException = LoggingException(logMessage = self.language(30003))
                # 'Cannot show TV3 root menu', Error parsing web page
                logException.process(self.language(30002), self.language(30780), logLevel)
                #raise logException
                return False
            
            listItems = []
    
            # Search
            newLabel = self.language(30500)
            thumbnailPath = self.GetThumbnailPath(newLabel)
            newListItem = xbmcgui.ListItem( label=newLabel )
            newListItem.setThumbnailImage(thumbnailPath)
            url = self.GetURLStart() + u'&search=1'
            listItems.append( (url, newListItem, True) )
    
#            self.AddFeatured(listItems, html)        
            self.AddCategories(listItems, categories)        
    
            # All Shows - A to Z
            newLabel = self.language(30061)
            thumbnailPath = self.GetThumbnailPath(newLabel)
            newListItem = xbmcgui.ListItem( label=newLabel )
            newListItem.setThumbnailImage(thumbnailPath)
            url = self.GetURLStart() + u'&allShows=1'
            listItems.append( (url, newListItem, True) )

            # All Shows - By Date
            newLabel = self.language(30062)
            thumbnailPath = self.GetThumbnailPath(newLabel)
            newListItem = xbmcgui.ListItem( label=newLabel )
            newListItem.setThumbnailImage(thumbnailPath)
            url = self.GetURLStart() + u'&calendar=1'
            listItems.append( (url, newListItem, True) )
    
            xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
            xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
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

        
        return True

    # listshows: If '1' list the shows on the main page, otherwise process the sidebar. The main page links to programmes or specific episodes, the sidebar links to categories or sub-categories
    # episodeId: id of the show to be played, or the id of a show where more than one episode is available
    # listavailable: If '1' process the specified episode as one of at least one episodes availabe, i.e. list all episodes available
    # search: If '1' perform a search
    # page: url, relative to www.rte.ie, to be processed. Not passed when an episodeId is given.

    def ParseCommand(self, mycgi):
        (category, episodeId, search, allShows, calendar, date, page) = mycgi.Params( u'category', u'episodeId', u'search', u'allShows', u'calendar', u'date', u'page' )
        self.log(u"category: %s, episodeId: %s, search: %s, allShows: %s, calendar: %s, date: %s, page: %s" % (category, episodeId, str(search), str(allShows), calendar, date, page), xbmc.LOGDEBUG)

        if search <> u'':
            return self.DoSearch()
        
        if category <> u'':
            return self.ShowCategory(category)

        if allShows <> u'':
            if page <> u'':
                return self.ListAToZ(page)
            else:
                return self.ListAToZ()

        if calendar <> u'':
            return self.ListCalendar()
            
        if date <> u'':
            return self.ListByDate(date)
            
        if page == u'':
            # "Can't find 'page' parameter "
            logException = LoggingException(logMessage = self.language(30030))
            # 'Cannot proceed', Error processing command
            logException.process(self.language(30755), self.language(30780), logLevel)
            return False

        self.log(u"page = %s" % page, xbmc.LOGDEBUG)
        page = mycgi.URLUnescape(page)
        self.log(u"mycgi.URLUnescape(page) = %s" % page, xbmc.LOGDEBUG)

        if u' ' in page:
            page = page.replace(u' ', u'%20')

        try:
            html = None
            self.log("urlRoot: " + urlRoot + ", page: " + page )
            html = self.httpManager.GetWebPage( urlRoot + page, 1800 )
            #raise Exception("test1", "test2")
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

        try:
            #return self.PlayEpisode(page, html)
            return self.PlayVideoWithDialog(self.PlayEpisode, (page, html))
            
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
            
            # "Error playing or downloading episode %s"
            exception.addLogMessage(self.language(30051) % "")
            # "Error processing video"
            exception.process(severity = self.logLevel(xbmc.LOGERROR))
            return False

                
    def GetCategories(self, html):
        categories = []

        soup = BeautifulSoup(html)
        categoryHTMLList = soup.findAll(u'h2')
        
        htmlparser = HTMLParser.HTMLParser()

        try:        
            for categoryHTML in categoryHTMLList:
                if categoryHTML.findNextSibling(u'div', {u'id':re.compile(u'^slider')}) is not None:
                    categories.append(unicode(htmlparser.unescape(categoryHTML.text)))
        except (Exception) as exception:
            exception = LoggingException.fromException(exception)
    
            # Error processing categories
            exception.addLogMessage(self.language(30058))
            exception.process(severity = self.logLevel(xbmc.LOGWARNING))
            
        return categories
    
#    def AddFeatured(self, listItems, html):
#        soup = BeautifulSoup(html)

#        videos = soup.find('div', {'id':'acc-menu2'}).find('a', {'href':re.compile('^http://www.tv3')})
        
#        for video in videos:
#            video = 
#            newLabel = category
#            thumbnailPath = self.GetThumbnailPath(newLabel.replace(u' ', u''))
##            newListItem = xbmcgui.ListItem( label=newLabel)
#            newListItem.setThumbnailImage(thumbnailPath)

#            url = self.GetURLStart() + u'&category=' + mycgi.URLEscape(category)

#            self.log(u"url: %s" % url, xbmc.LOGDEBUG)
#            listItems.append( (url,newListItem,True) )
            

    def AddCategories(self, listItems, categories):
        for category in categories:
            newLabel = category
            thumbnailPath = self.GetThumbnailPath(newLabel.replace(u' ', u''))
            newListItem = xbmcgui.ListItem( label=newLabel)
            newListItem.setThumbnailImage(thumbnailPath)

            url = self.GetURLStart() + u'&category=' + mycgi.URLEscape(category)

            self.log(u"url: %s" % url, xbmc.LOGDEBUG)
            listItems.append( (url,newListItem,True) )

    def GetNameFromGridshow(self, gridshow):
            try:
                htmlparser = HTMLParser.HTMLParser()
                return '"' + re.search("3player\s+\|\s+(.+),\s+(\d\d/\d\d/\d\d\d\d)\.\s*(.*?)", htmlparser.unescape(gridshow.a['title'])).group(1) + '"'
            except (Exception) as exception:
                return "programme"
        
    def ShowCategory(self, category):
        self.log(u"", xbmc.LOGDEBUG)
        html = None
        html = self.httpManager.GetWebPage(rootMenuUrl, 300)
        """
        <h2>Most Talked About</h2>
        ...
        <div id="slider1" ...>
            <ul style="width: 5892px; ">
                <li style="margin-left: -982px; float: left; ">
                    <div id="gridshow">
                        <a title="3player | Snog Marry Avoid, 22/11/2012. Jenny meets blonde Danielle, gothic geisha Azelie and outrageous mother Jay" href="http://www.tv3.ie/3player/show/452/56083/1/Snog-Marry-Avoid">
                            <img alt="3player | Snog Marry Avoid, 22/11/2012. Jenny meets blonde Danielle, gothic geisha Azelie and outrageous mother Jay" src="./3player   Home_files/snog_nov22_3player_1_56083_180x102.jpg" class="shadow smallroundcorner">
                        </a>
                        <h3>
                            <a title="3player | Snog Marry Avoid, 22/11/2012. Jenny meets blonde Danielle, gothic geisha Azelie and outrageous mother Jay" href="http://www.tv3.ie/3player/show/452/56083/1/Snog-Marry-Avoid">Snog Marry Avoid</a>
                        </h3>
                        <span id="gridcaption">Jenny meets blonde Danielle, gothic geisha Azelie and out...</span>
                        <span id="griddate">22/11/2012</span>
                        <span id="gridduration">00:23:24</span>
                    </div>
                    ...
        """
        htmlparser = HTMLParser.HTMLParser()

        listItems = []
        
        soup = BeautifulSoup(html)
        gridshows = soup.find(u'h2', text=category).parent.findNextSibling('div', {'id':re.compile('^slider')}).findAll('div', {'id':'gridshow'})
        
        for gridshow in gridshows:
            try:
                infoLabels = self.GetEpisodeInfoCategory(gridshow)
                page = gridshow.a['href']
                thumbnail = gridshow.a.img['src']
                dot=gridshow.a['title'].index('.')
                newLabel=infoLabels['Title']
                
                newListItem = xbmcgui.ListItem( label=newLabel)
                newListItem.setThumbnailImage(thumbnail)
                
                newListItem.setInfo(u'video', infoLabels)
                newListItem.setProperty("Video", "true")
                #newListItem.setProperty('IsPlayable', 'true')
                
                url = self.GetURLStart() + u'&page=' + mycgi.URLEscape(page)
    
                listItems.append( (url, newListItem, False) )
            except (Exception) as exception:
                if not isinstance(exception, LoggingException):
                    exception = LoggingException.fromException(exception)
                
                programme = self.GetNameFromGridshow(gridshow)
                # "Error processing <programme>"
                exception.addLogMessage(self.language(30063) % programme + "\n" + repr(gridshow))
                exception.process(self.language(30063) % programme, "", xbmc.LOGWARNING)
            
        xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
        xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
            
        return True
    
#==============================================================================

    def GetAllShowsLink(self, soup): 
        self.log(u"", xbmc.LOGDEBUG)
        
        try:
            anchor = soup.find('div', {'id':'bottombar'}).find(lambda tag: tag.name == 'a' and tag.text == 'All Shows')
            return urlRoot + anchor['href']
        
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
            
            # Unable to determine "All Shows" URL. Using default: %s
            exception.addLogMessage(self.language(30059) % allShowsDefaultUrl)
            exception.process(severity = xbmc.LOGWARNING)
            return allShowsDefaultUrl

    def AddAllShowListItem(self, title, video, listItems, thumbnail = None):
        date = video.find('span', {'id':'griddate'}).text
        title = title + ", " + date
        
        description = self.fullDecode(video.findAll('a')[1].text)
        infoLabels = {'Title': title, 'Plot': description, 'PlotOutline': description}

        anchor = video.find('a')
        page = anchor['href']
        
        if thumbnail is None:
            thumbnail = anchor.img['src']

        newListItem = xbmcgui.ListItem( label=title)
        newListItem.setThumbnailImage(thumbnail)
        newListItem.setInfo(u'video', infoLabels)
        newListItem.setProperty("Video", "true")
        #newListItem.setProperty('IsPlayable', 'true')
        
        url = self.GetURLStart() + u'&page=' + mycgi.URLEscape(page)

        listItems.append( (url, newListItem, False) )
            
    def ListAToZ(self, page = None):
        self.log(u"", xbmc.LOGDEBUG)
        """
            <div id="g1" class="gridshow">
                <a href="javascript:void(0)">
                    <img src="./3player   All Shows_files/304_180x102.jpg" class="shadow smallroundcorner">
                </a>
                <h3>
                    <a href="http://www.tv3.ie/3player/show/304/0/0/24+Hours+To+Kill">24 Hours To Kill</a>
                </h3>
            </div>
        """

        try:
            html = None
            html = self.httpManager.GetWebPage(rootMenuUrl, 300)

            soup = BeautifulSoup(html)
            allShowsUrl = self.GetAllShowsLink(soup)
                        
            html = self.httpManager.GetWebPage(allShowsUrl, 1800)

            soup = BeautifulSoup(html)
            htmlparser = HTMLParser.HTMLParser()
            
            listItems = []
            
            if page is None:
                gridshows = soup.findAll(u'div', {u'class':re.compile(u'^gridshow')})
                for gridshow in gridshows:
                    try:
                        title = ''
                        thumbnailPath = gridshow.a.img['src']
                        tooltip = gridshow.a.img['title']
                        
                        soup = BeautifulSoup(tooltip)
                        videos = soup.findAll('div', {'id':'tooltip_showvideo'})
                        page = soup.find('a')['href']
                        slash = page.rindex('/')
                        title = page[slash+1:].replace('+',' ')
                        title = self.fullDecode(title)
                        
                        # If there's just one episode then link directly to the episode
                        if len(videos) == 1:
                            self.AddAllShowListItem(title, videos[0], listItems, thumbnailPath)
                        else:                    
                            title = title + ", " + unicode(len(videos)) + " episodes available"
                            
                            description = soup.find('div', {'id':'tooltip_showcontent'}).contents[0]
                            
                            if description is None or not isinstance(description, NavigableString):
                                description = ''
                            else:
                                description = self.fullDecode(description)
                            
                            infoLabels = {'Title': title, 'Plot': description, 'PlotOutline': description}
        
                            newListItem = xbmcgui.ListItem( label=title )
                            newListItem.setInfo('video', infoLabels)
                            newListItem.setThumbnailImage(thumbnailPath)
            
                            url = self.GetURLStart() + '&page=' + mycgi.URLEscape(thumbnailPath) + '&allShows=1'
                            listItems.append( (url,newListItem,True) )
                    except (Exception) as exception:
                        if not isinstance(exception, LoggingException):
                            exception = LoggingException.fromException(exception)
                        
                        programme = self.GetNameFromGridshow(gridshow)
                        # "Error processing <programme>"
                        exception.addLogMessage(logMessage = self.language(30063) % programme + "\n" + repr(gridshow))
                        exception.process(self.language(30063) % programme, "", xbmc.LOGWARNING)
                        
            else:
                imageTag = soup.find(src=page)
                tooltip = imageTag['title']
                
                soup = BeautifulSoup(tooltip)
                videos = soup.findAll('div', {'id':'tooltip_showvideo'})
                page = soup.find('a')['href']
                slash = page.rindex('/')
                title = page[slash+1:].replace('+',' ')
                title = self.fullDecode(title) 
                 
                for video in videos:
                    try:
                          self.AddAllShowListItem(title, video, listItems)
                    except (Exception) as exception:
                        if not isinstance(exception, LoggingException):
                            exception = LoggingException.fromException(exception)
                        
                        # "Error processing <programme>"
                        exception.addLogMessage(logMessage = self.language(30063) % title + "\n" + repr(video))
                        exception.process(self.language(30063) % title, "", xbmc.LOGWARNING)
                        

            xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
            xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            if html is not None:
                msg = "html:\n\n%s\n\n" % html
                exception.addLogMessage(msg)
                
            # Error processing "Show All" menu
            exception.addLogMessage(self.language(30023))
            exception.process(severity = self.logLevel(xbmc.LOGERROR))
            return False

        return True
        
#==============================================================================
    def AddEpisodeToSearchList(self, listItems, video):
        episodeLink = re.search('gotopage\("(.+?)"\);', video['onclick']).group(1)
        href = episodeLink

        title = video.h3.text + ', ' + video.find('span', {'id':'videosearch_date'}).text
        description = video.find('span', {'id':'videosearch_caption'}).text
        
        infoLabels = {'Title': title, 'Plot': description, 'PlotOutline': description}
        
        newLabel = title
                                        
        newListItem = xbmcgui.ListItem( label=newLabel.replace('&#39;', "'" ) )
        newListItem.setThumbnailImage(video.img['src'])
        newListItem.setInfo('video', infoLabels)
        newListItem.setProperty("Video", "true")
        #newListItem.setProperty('IsPlayable', 'true')
        
        url = self.GetURLStart() + '&page=' + mycgi.URLEscape(href)

        listItems.append( (url, newListItem, False) )
    
#==============================================================================

    def ListSearchShows(self, html):
        self.log("", xbmc.LOGDEBUG)
        listItems = []

        soup = BeautifulSoup(html)
        videos = soup.findAll('li', 'unselected_video')

        for video in videos:
            try:
                self.AddEpisodeToSearchList(listItems, video)
            except (Exception) as exception:
                if not isinstance(exception, LoggingException):
                    exception = LoggingException.fromException(exception)
            
                # "Error processing search result"
                exception.addLogMessage(logMessage = self.language(30069) + "\n" + repr(video))
                exception.process(self.language(30069), "", xbmc.LOGWARNING)
            

        xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
        xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
        

        return True

    def GetSWFPlayer(self, flowPlayerScript):
        self.log(u"", xbmc.LOGDEBUG)
        
        try:
            swfPlayer = utils.findString( u"TV3Provider::GetSWFPlayer()", "flowplayer\(\"flowPlayer\",\s+{src:\s+\"(.+?)\"", flowPlayerScript)
#            swfPlayer = soup.find('div', {'id':'flowPlayer'}).object['data']
            if swfPlayer is None:
                swfPlayer = swfDefault

            return swfPlayer
        
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
            
            # Unable to determine swfPlayer URL. Using default: %s
            exception.addLogMessage(self.language(30520) % swfDefault)
            exception.process(severity = xbmc.LOGWARNING)
            return swfDefault

#==============================================================================
    def GetEpisodeInfoCategory(self, gridshow):
        self.log("", xbmc.LOGDEBUG)

        """
        <div id="gridshow">
            <a title="3player | Snog Marry Avoid, 22/11/2012. Jenny meets blonde Danielle, gothic geisha Azelie and outrageous mother Jay" href="http://www.tv3.ie/3player/show/452/56083/1/Snog-Marry-Avoid">
                <img alt="3player | Snog Marry Avoid, 22/11/2012. Jenny meets blonde Danielle, gothic geisha Azelie and outrageous mother Jay" src="./3player   Home_files/snog_nov22_3player_1_56083_180x102.jpg" class="shadow smallroundcorner">
            </a>
            <h3>
                <a title="3player | Snog Marry Avoid, 22/11/2012. Jenny meets blonde Danielle, gothic geisha Azelie and outrageous mother Jay" href="http://www.tv3.ie/3player/show/452/56083/1/Snog-Marry-Avoid">Snog Marry Avoid</a>
            </h3>
            <span id="gridcaption">Jenny meets blonde Danielle, gothic geisha Azelie and out...</span>
            <span id="griddate">22/11/2012</span>
            <span id="gridduration">00:23:24</span>
        </div>
        """
        htmlparser = HTMLParser.HTMLParser()
        
        titleData = htmlparser.unescape(gridshow.a['title'])
        
        match=re.search("3player\s+\|\s+(.+),\s+(\d\d/\d\d/\d\d\d\d)\.\s*(.*)", titleData) 
        title=match.group(1) + ", " + match.group(2)
        description = match.group(3)

        infoLabels = {'Title': title, 'Plot': description, 'PlotOutline': description}

        self.log("infoLabels: %s" % infoLabels, xbmc.LOGDEBUG)
        return infoLabels

#==============================================================================
    #TODO Add date
    def GetEpisodeInfo(self, soup):
        self.log("", xbmc.LOGDEBUG)

        htmlparser = HTMLParser.HTMLParser()
        
        title = htmlparser.unescape(soup.find('meta', {'property' : 'og:title'})['content'])
        description = htmlparser.unescape(soup.find('meta', {'property' : 'og:description'})['content'])

        infoLabels = {'Title': title, 'Plot': description, 'PlotOutline': description}

        self.log("infoLabels: %s" % infoLabels, xbmc.LOGDEBUG)
        return infoLabels

#==============================================================================
    def InitialiseRTMP(self, soup):
        self.log("", xbmc.LOGDEBUG)

        try:
            flowPlayerScript = unicode(soup.find('div', {'id':'flowPlayer'}).findNextSibling('script').text)

            rtmpStr = utils.findString( u"TV3Provider::InitialiseRTMP()", "netConnectionUrl: \"(.+?)\"", flowPlayerScript)
            rootIndex = rtmpStr[8:].index('/') + 9
            app = rtmpStr[rootIndex:]
            swfUrl = self.GetSWFPlayer(flowPlayerScript)
            playPath = utils.findString( u"TV3Provider::InitialiseRTMP()", "playlist:\s+\[\s+{\s+url:\s+\"(.+?)\"", flowPlayerScript)
        
            rtmpVar = rtmp.RTMP(rtmp = rtmpStr, app = app, swfVfy = swfUrl, playPath = playPath)
            self.AddSocksToRTMP(rtmpVar)

            return rtmpVar
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            # Error getting RTMP data
            exception.addLogMessage(self.language(30057))
            raise exception
        
    def PlayEpisode(self, page, html):
        self.log("", xbmc.LOGDEBUG)

        soup = BeautifulSoup(html)

        ageCheck = soup.find('div', {'id':'age_check_form_row'})
        
        if ageCheck is not None:
            
            if self.dialog.iscanceled():
                return False
            # "Getting episode info"
            self.dialog.update(25, self.language(30084))
            try:
                html = None
                html = self.httpManager.GetWebPage( urlRoot + page, 1800, values = {'age_ok':'1'} )
                soup = BeautifulSoup(html)
            except (Exception) as exception:
                exception = LoggingException.fromException(exception)
    
                if html is not None:
                    msg = "html:\n\n%s\n\n" % html
                    exception.addLogMessage(msg)
                    
                # Error getting web page: %s
                exception.addLogMessage(self.language(30050) + ": " + ( urlRoot + page ) )
    
                # Error getting web page
                exception.process(self.language(30050), u'', severity = self.logLevel(xbmc.LOGERROR))
                return False
    
        rtmpVar = self.InitialiseRTMP(soup)

        infoLabels = self.GetEpisodeInfo(soup)
        thumbnail = soup.find('meta', {'property' : 'og:image'})['content']
        defaultFilename = infoLabels['Title']

        return self.PlayOrDownloadEpisode(infoLabels, thumbnail, rtmpVar, defaultFilename)

#==============================================================================
    #TODO Handle exceptions?
    def DoSearchQuery( self, query ):
        self.log("query: %s" % query, xbmc.LOGDEBUG)
        
        values = {'queryString':query, 'limit':20}
#        headers = {'DNT':'1', 'X-Requested-With':'XMLHttpRequest' }
        headers = {}
        headers['DNT'] = '1'
        headers['Referer'] = 'http://www.tv3.ie/3player/'  
        headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        
        html = self.httpManager.GetWebPage( searchUrl, 1800, values = values, headers = headers )
        if html is None or html == '':
            # Data returned from web page: %s, is: '%s'
            logException = LoggingException(logMessage = self.language(30060) % ( searchUrl, html ))

            # Error getting web page
            logException.process(self.language(30050), '', self.logLevel(xbmc.LOGERROR))
            return False

        # Fix fcuked up TV3 HTML formatting
        html = html.replace("<h3 id='search_heading'>Videos</h2>", "<h3 id='search_heading'>Videos</h3>")
        self.ListSearchShows(html)

        return True

    def ListCalendar(self):
        self.log(u"", xbmc.LOGDEBUG)
        listItems = []

        try:
            html = None
            html = self.httpManager.GetWebPage(rootMenuUrl, 300)
            minDateString=re.search( u"minDate: '([0-9][0-9]/[0-9][0-9]/[0-9][0-9][0-9][0-9])'", html).group(1)
            maxDateString=re.search( u"maxDate: '([0-9][0-9]/[0-9][0-9]/[0-9][0-9][0-9][0-9])'", html).group(1)
    
            minDate = date.fromtimestamp(mktime(strptime(minDateString, u"%m/%d/%Y")))
            today = date.fromtimestamp(mktime(strptime(maxDateString, u"%m/%d/%Y")))
        
            # Today
            newLabel = u"Today"
            newListItem = xbmcgui.ListItem( label=newLabel )
            url = self.GetURLStart() + u'&date=' + maxDateString
            listItems.append( (url,newListItem,True) )
        
            # Yesterday
            newLabel = u"Yesterday"
            newListItem = xbmcgui.ListItem( label=newLabel )
            url = self.GetURLStart() + u'&date=' + (today - timedelta(1)).strftime(u"%m/%d/%Y")
            listItems.append( (url,newListItem,True) )
        
            # Weekday
            newLabel = (today - timedelta(2)).strftime(u"%A")
            newListItem = xbmcgui.ListItem( label=newLabel )
            url = self.GetURLStart() + u'&date=' + (today - timedelta(2)).strftime(u"%m/%d/%Y")
            listItems.append( (url,newListItem,True) )
        
            # Weekday
            newLabel = (today - timedelta(3)).strftime(u"%A")
            newListItem = xbmcgui.ListItem( label=newLabel )
            url = self.GetURLStart() + u'&date=' + (today - timedelta(3)).strftime(u"%m/%d/%Y")
            listItems.append( (url,newListItem,True) )
        
            currentDate = today - timedelta(4)
            sentinelDate = minDate - timedelta(1)
            while currentDate > sentinelDate:
                newLabel = currentDate.strftime(u"%A, %d %B %Y")
                newListItem = xbmcgui.ListItem( label=newLabel )
                url = self.GetURLStart() + u'&date=' + currentDate.strftime(u"%m/%d/%Y")
                listItems.append( (url,newListItem,True) )
    
                currentDate = currentDate - timedelta(1) 
        
            xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
            xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
            
            return True
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
            
            if html is not None:
                msg = "html:\n\n%s\n\n" % html
                exception.addLogMessage(msg)
                
            # "Error creating calendar list"
            message = self.language(30064)
            details = utils.valueIfDefined(minDateString, 'minDateString') + ", "
            details = details + utils.valueIfDefined(maxDateString, 'maxDateString') + ", "
            
            if utils.variableDefined( currentDate ):
                details = details + "currentDate: " + unicode(currentDate) + ", "
            else:
                details = details + "currentDate: Not defined"
                
            details = details + utils.valueIfDefined(url, 'url')
            
            exception.addLogMessage(logMessage = message + "\n" + details)
            # "Error creating calendar list"
            exception.process(message, "", self.logLevel(xbmc.LOGERROR))
            return False
    
    def ListByDate(self, date):
        values = {'queryString' : date}
        
        html = None
        html = self.httpManager.GetWebPage( calendarUrl, 3600, values = values)
        if html is None or html == '':
            # Data returned from web page: %s, is: '%s'
            logException = LoggingException(logMessage = self.language(30060) % ( searchUrl, html ))

            # Error getting web page
            logException.process(self.language(30050), '', self.logLevel(xbmc.LOGERROR))
            return False

        soup = BeautifulSoup(html)

        listItems = []
        htmlparser = HTMLParser.HTMLParser()
        videos = soup.findAll('div', {'id':'tooltip_showvideo_cal'})
        
        if len(videos) == 1 and len(videos[0].findAll('a')) == 0:
            # No videos broadcast on this date.
            xbmc.executebuiltin('XBMC.Notification(IrishTV, %s)' % (videos[0].text))
            return True
        
        for video in videos:
            try:
                anchors = video.findAll('a')
                
                time = anchors[2].small.text
                title = self.fullDecode( anchors[1].b.text + ", " + time )
                description = self.fullDecode( anchors[3].text )
                infoLabels = {'Title': title, 'Plot': description, 'PlotOutline': description}
    
                page = anchors[0]['href']
                thumbnail = anchors[0].img['src']
                newLabel=title
                
                newListItem = xbmcgui.ListItem( label=newLabel)
                newListItem.setThumbnailImage(thumbnail)
                newListItem.setInfo(u'video', infoLabels)
                newListItem.setProperty("Video", "true")
                #newListItem.setProperty('IsPlayable', 'true')
                
                url = self.GetURLStart() + u'&page=' + mycgi.URLEscape(page)
    
                listItems.append( (url, newListItem, False) )
            except (Exception) as exception:
                if not isinstance(exception, LoggingException):
                    exception = LoggingException.fromException(exception)
                
                if video is not None:
                    msg = "video:\n\n%s\n\n" % video
                    exception.addLogMessage(msg)
                    
                # "Error processing video"
                exception.addLogMessage(logMessage = self.language(30063) % "video\n" + repr(video))
                # "Error processing video"
                exception.process(self.language(30063) % programme % "video\n", "", xbmc.LOGWARNING)
                continue
            
        xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
        xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
            
        return True
    
