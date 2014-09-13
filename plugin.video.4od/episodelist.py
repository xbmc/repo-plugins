# -*- coding: utf-8 -*-
import re
import sys

from time import strftime,strptime,mktime
from datetime import date
import time


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

from watched import Watched

from BeautifulSoup import BeautifulSoup

from httpmanager import HttpManager
from loggingexception import LoggingException

import utils
from xbmcaddon import Addon

__PluginName__  = u'plugin.video.4od'
__addon__ = Addon(__PluginName__)
__language__ = __addon__.getLocalizedString

#TODO Add more comprehensive debug logging to this class (EpisodeList)
#TODO There is much reliance on member variables. Probably many cases 
#     where member variables are redundant or can be replaced by local vars passed
#     as parameters or returned from methods. Clean up.

#==================================================================================
# EpisodeList
#
# This class exists to provide two methods that have very similar functionality
# but with a minimum of code duplication
#
# Those methods are
# 1) Parse a web page that lists episodes of a show and create an XBMC list item
#    for each episode
#
# 2) Parse the SAME web page to find a particular episode  
#==================================================================================

class EpisodeList:

    def __init__(self, baseURL, showUrl, cache, showWatched = False):
        self.log = sys.modules[u"__main__"].log
        self.assetId         = u''
        self.baseURL        = baseURL
        self.cache         = cache
        self.showWatched = showWatched 
        self.episodeDetails = {}
        self.showUrl = showUrl

    def getAssetId(self):
        return self.assetId

    def initialise(self, showId, showTitle, season, dataFolder):
        method = u"EpisodeList.initialise"
        self.log (u"initialise showId: %s, showTitle: %s, season: %s " % ( showId, showTitle, season ), xbmc.LOGDEBUG)

        try:
            self.html = None
            self.dataFolder = dataFolder
            url = None
            url = self.showUrl % (showId, season)

            self.html = self.cache.GetWebPage( url, 600 ) # 10 minutes
            
            self.log (u"page: %s\n\n%s\n\n" % ( url, self.html ), xbmc.LOGDEBUG)
            self.showId = showId
            self.showTitle = showTitle
            self.currentSeason = season

            return True
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
            
            if html is not None:
                msg = u"html:\n\n%s\n\n" % html
                exception.addLogMessage(msg)
            
            # 'Error getting episode list'
            exception.addLogMessage(__language__(30790))
            raise exception
    
    def getInfolabelsAndLogo(self, episodeDetail):
        
        infoLabels = {}
        infoLabels[u'Title'] = episodeDetail.label 
                        #u'Plot': episodeDetail.description, 
                        #u'PlotOutline': episodeDetail.description, 
        infoLabels[u'Premiered'] = episodeDetail.premieredDate
        infoLabels[u'Season'] = episodeDetail.seriesNum
        infoLabels[u'Episode'] = episodeDetail.epNum


        return (infoLabels, episodeDetail.thumbnail)
        
    #==============================================================================
    # createListItems
    #
    # Create an XBMC list item for each episode
    #==============================================================================
    def createListItems(self, mycgi, resumeEnabled, fourOD):
        """
         <section id="episodeList">
                <!-- got episode Shameless -->
                        <div class="episodeGroup clearfix underlined">
                        <article class="episode clearfix" data-rating="18"
                                 data-wsbrandtitle="/shameless" data-preselectasseturl="http://ais.channel4.com/asset/3270370"
                                 data-preselectassetguidance="Very strong language and sexual scenes">
        
                        <div class="screenshotCont">
                            <a href="">
                                <img class="screenShot" src="http://cache.channel4.com/assets/programmes/images/shameless/series-1/episode-1/c06b3dbe-c9d6-4908-9f2c-708518482916_200x113.jpg" width="160" height="91"
                                     alt="Shameless"><span></span>
                            </a>
                        </div>
                        <div class="details">
                            <h1>
                                <a href="/4od/shameless/series-1/3270370">
                                        Shameless</a>
                            </h1>
                                <p>
                                        Series 1
                                        Episode 1
                                    
                                </p>
                                <p>
                                    12am
                                     Tue 13 Jan
                                     2004
                                </p>
                            <p>
                                        Channel 4
                                (49min)
                                    <span class="guidance">Very strong language and sexual scenes</span>
                            </p>
                        </div>
                        <div class="rightLinks">
                                         <a class="seeAll" href="/4od/shameless/series-1/3270370"><span>More</span></a>
                        </div>
                    </article>
        """
        listItems = []
        epsDict = dict()
        
        soup = BeautifulSoup(self.html)
        
        articles = soup.find("section", id="episodeList").findAll('article')

        self.log (u"articles: %s" % articles, xbmc.LOGDEBUG)
        
        for entry in articles:
            episodeDetail = EpisodeDetail(entry, self.log)
            self.episodeDetails[episodeDetail.assetId] = episodeDetail 
            
            episodeDetail.refine(self.showId, self.showTitle)
            
            contextMenuItems = []
            infoLabels = {}
            
            (infoLabels, thumbnail) = self.getInfolabelsAndLogo(episodeDetail)
            
            url = self.baseURL + u'&episodeId=' + mycgi.URLEscape(episodeDetail.assetId) + u"&show=" + mycgi.URLEscape(self.showId) + u"&seriesNumber=" + mycgi.URLEscape(str(episodeDetail.seriesNum)) + "&episodeNumber=" + mycgi.URLEscape(str(episodeDetail.epNum)) + "&title=" + mycgi.URLEscape(episodeDetail.label) + "&thumbnail=" + mycgi.URLEscape(episodeDetail.thumbnail) + "&premiereDate=" + mycgi.URLEscape(episodeDetail.premieredDate) #+ "&swfPlayer=" + mycgi.URLEscape(self.swfPlayer)
            
            episodeId = episodeDetail.assetId
            newListItem = fourOD.ResumeWatchListItem(url, episodeId, contextMenuItems, infoLabels, thumbnail)
            listItems.append( (url, newListItem, False) )

        seriesAnchors = soup.find("nav", "seriesNav").findAll('a')
        for series in seriesAnchors:
            pattern = u'/4od/%s(.*)' % self.showId 
            match = re.search(pattern, series[u'href'])
            seasonId = match.group(1)

            if seasonId == u'' or seasonId == self.currentSeason:
                continue
            
            newListItem = xbmcgui.ListItem( "Series " + series.text )

            url = self.baseURL + u'&show=' + mycgi.URLEscape(self.showId) + u'&title=' + mycgi.URLEscape(self.showTitle) + u'&season=' + mycgi.URLEscape(seasonId)
            listItems.append( (url, newListItem, True) )

        return listItems

    def GetEpisodeDetail(self, matchingAssetId):
        soup = BeautifulSoup(self.html)
        
        articles = soup.find("section", id="episodeList").findAll('article')
        
        for entry in articles:
            episodeDetail = EpisodeDetail(entry, self.log)
            if episodeDetail.assetId == matchingAssetId:
                episodeDetail.refine(self.showId, self.showTitle)
                
                return episodeDetail
            
        return None

        
"""
<article class="episode clearfix" data-rating="18"
         data-wsbrandtitle="/shameless" data-preselectasseturl="http://ais.channel4.com/asset/3270370"
         data-preselectassetguidance="Very strong language and sexual scenes">

<div class="screenshotCont">
    <a href="">
        <img class="screenShot" src="http://cache.channel4.com/assets/programmes/images/shameless/series-1/episode-1/c06b3dbe-c9d6-4908-9f2c-708518482916_200x113.jpg" width="160" height="91"
             alt="Shameless"><span></span>
    </a>
</div>
<div class="details">
    <h1>
        <a href="/4od/shameless/series-1/3270370">
                Shameless</a>
    </h1>
        <p>
                Series 1
                Episode 1
            
        </p>
        <p>
            12am
             Tue 13 Jan
             2004
        </p>
    <p>
                Channel 4
        (49min)
            <span class="guidance">Very strong language and sexual scenes</span>
    </p>
</div>
<div class="rightLinks">
                 <a class="seeAll" href="/4od/shameless/series-1/3270370"><span>More</span></a>
</div>
</article>
"""
class EpisodeDetail:
    def __init__(self, entry, log):
        self.log = log
        self.label = ""
        self.thumbnail = ""
        assetUrl = entry['data-preselectasseturl']
        match = re.search(u'http://ais.channel4.com/asset/(\d+)', assetUrl)
        self.assetId= match.group(1)
        self.url = ""

        details = entry.find('div', 'details')
        pList = details.findAll('p')
        self.seriesNum = ""
        self.epNum = ""
        try:
            pattern = u'\s*Series\s([0-9]+)\s+Episode\s([0-9]+)'
            for p in pList:
                try:
                    seasonAndEpisodeMatch = re.search( pattern, p.text, re.DOTALL | re.IGNORECASE )
            
                    self.seriesNum = seasonAndEpisodeMatch.group(1)
                    self.epNum = seasonAndEpisodeMatch.group(2)
                    break
                except (Exception) as exception:
                    self.log("Exception getting series and episode number: " + unicode(exception), xbmc.LOGWARNING)
                    
        except (Exception) as exception:
            self.logException(exception, u'series and episode number')

        self.hasSubtitles = False
        try:
            subtitlesTag = details.find('span', 'subtitles')
            if subtitlesTag and subtitlesTag.text == "Subtitles":
                self.hasSubtitles = True
        except (Exception) as exception:
            self.logException(exception, u'subtitles')

        try:
            self.thumbnail = entry.find('img')['src']
        except (Exception) as exception:
            self.logException(exception, u'thumbnail')
            self.thumbnail = ""

        self.premieredDate = ""
        try:
            for p in pList:
                try:
                    timeString = p.text.replace('\r\n', '').replace('Sept', 'Sep').replace('July', 'Jul').replace('June', 'Jun')
                    timeString = re.sub(' +', ' ', timeString)
                    lastDate = date.fromtimestamp(mktime(strptime(timeString, u"%I%p %a %d %b %Y")))
                    self.premieredDate = lastDate.strftime(u"%d.%m.%Y")
                    break
                except (Exception) as exception:
                    self.log("Exception getting timestamp: " + unicode(exception), xbmc.LOGWARNING)
        except (Exception) as exception:
            self.logException(exception, u'timestamp')

        try:
            title = details.find('p').text.replace('\r\n', '')
            self.epTitle = re.sub(' +', ' ', title)
        except (Exception) as exception:
            self.logException(exception, u'title')
            self.epTitle = ""

        self.description = ""
        """
        try:
            self.description = entry[u'summary'][u'$']
        except (Exception) as exception:
            self.logException(exception, u'summary')
            self.description = ""
        
        try:
            self.seriesNum = int(entry[u'dc:relation.SeriesNumber'])
        except (Exception) as exception:
            self.logException(exception, u'dc:relation.SeriesNumber')
            self.seriesNum = ""
        """
        self.log (u'Episode details: ' + unicode((self.assetId,self.epNum,self.url,self.thumbnail,self.premieredDate,self.epTitle,self.description,self.seriesNum,self.hasSubtitles)), xbmc.LOGDEBUG)

    def refine(self, showId, showTitle):
        if ( self.seriesNum == u"" or self.epNum == u"" ):
            pattern = u'series-([0-9]+)(\\\)?/episode-([0-9]+)'
            seasonAndEpisodeMatch = re.search( pattern, self.thumbnail, re.DOTALL | re.IGNORECASE )

            self.log(u"Searching for season and episode numbers in thumbnail url: %s" % self.thumbnail)
            if seasonAndEpisodeMatch is not None:
                self.seriesNum = int(seasonAndEpisodeMatch.group(1))
                self.epNum = int(seasonAndEpisodeMatch.group(3))
            
#                self.log( "End1: %s" % str(self.seriesNum), xbmc.LOGDEBUG)
#                self.log( str(self.epNum), xbmc.LOGDEBUG)

#        self.log( "End2: %s" % str(self.seriesNum), xbmc.LOGDEBUG)
#        self.log( str(self.epNum), xbmc.LOGDEBUG)

        if len(self.premieredDate) > 0:
            self.filename = showId + "." + self.premieredDate.replace( ' ', '.' )
        else:
            self.filename = showId + "." + self.assetId

        self.epTitle = self.epTitle.strip()
        showTitle = utils.remove_extra_spaces(utils.remove_square_brackets(showTitle))

        self.label = self.epTitle
        if self.epTitle == showTitle:
            self.label = "Series %d Episode %d" % (self.seriesNum, self.epNum)

        if len(self.premieredDate) > 0 and self.premieredDate not in self.label:
                self.label = self.label + u'  [' + self.premieredDate + u']'

        self.description = utils.remove_extra_spaces(utils.remove_html_tags(self.description))
        self.description = self.description.replace( u'&amp;', u'&' )
        self.description = self.description.replace( u'&pound;', u'£')
        self.description = self.description.replace( u'&quot;', u"'" )


    def logException(self, exception, detailName):
        if not isinstance(exception, LoggingException):
            exception = LoggingException.fromException(exception)
    
        # 'Error getting episode data "%s"'
        exception.addLogMessage(__language__(30960) % detailName)
        exception.printLogMessages(severity = xbmc.LOGWARNING)
        

