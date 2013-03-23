# -*- coding: utf-8 -*-
import re
import sys

from time import strftime,strptime,mktime
from datetime import date
import time

import simplejson

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
#	 where member variables are redundant or can be replaced by local vars passed
#	 as parameters or returned from methods. Clean up.

#==================================================================================
# EpisodeList
#
# This class exists to provide two methods that have very similar functionality
# but with a minimum of code duplication
#
# Those methods are
# 1) Parse a web page that lists episodes of a show and create an XBMC list item
#	for each episode
#
# 2) Parse the SAME web page to find a particular episode  
#==================================================================================

ps3ShowUrl = u"http://ps3.channel4.com/pmlsd/%s/4od.json?platform=ps3&uid=%s" # showId, time

class EpisodeList:

	def __init__(self, baseURL, cache, showWatched = False):
		self.log = sys.modules[u"__main__"].log
		self.assetId		 = u''
		self.baseURL		= baseURL
		self.cache		 = cache
		self.showWatched = showWatched 
		self.episodeDetails = {}

	def getAssetId(self):
		return self.assetId

	def initialise(self, showId, showTitle):
		method = u"EpisodeList.initialise"
		self.log (u"initialise showId: %s, showTitle: %s " % ( showId, showTitle ), xbmc.LOGDEBUG)

		try:
			jsonText = None
			url = None
			url = ps3ShowUrl % (showId, int(time.time()*1000))

			jsonText = self.cache.GetWebPage( url, 600 ) # 10 minutes
			jsonData = simplejson.loads(jsonText)

			if isinstance(jsonData[u'feed'][u'entry'], list):
				self.entries = jsonData[u'feed'][u'entry']
			else:
				# Single entry, put in a list
				self.entries = [ jsonData[u'feed'][u'entry'] ] 

			self.showId = showId
			self.showTitle = showTitle

			return True
		except (Exception) as exception:
			if not isinstance(exception, LoggingException):
				exception = LoggingException.fromException(exception)
			
			if jsonText is not None:
				msg = u"jsonText:\n\n%s\n\n" % jsonText
				exception.addLogMessage(msg)
			
			# 'Error getting episode list'
			exception.addLogMessage(__language__(30790))
			raise exception
	
	def getInfolabelsAndLogo(self, episodeDetail):
		
		infoLabels = {
						u'Title': episodeDetail.label, 
						u'Plot': episodeDetail.description, 
						u'PlotOutline': episodeDetail.description, 
						u'Premiered': episodeDetail.premieredDate,
						u'Season': episodeDetail.seriesNum,
						u'Episode': episodeDetail.epNum
						}

		return (infoLabels, episodeDetail.thumbnail)
		
	def createNewListItem(self, episodeDetail):
		(infoLabels, thumbnail) = self.getInfolabelsAndLogo(episodeDetail)

		contextMenuItems = []
		if self.showWatched:
			if Watched().isWatched(episodeDetail.assetId):
				infoLabels['PlayCount']  = 1
				contextMenuItems.append((u'Mark as unwatched', u"XBMC.RunPlugin(%s?unwatched=1&ep=%s)" % (sys.argv[0], episodeDetail.assetId) ))
			else:
				contextMenuItems.append((u'Mark as watched', u"XBMC.RunPlugin(%s?watched=1&ep=%s)" % (sys.argv[0], episodeDetail.assetId) ))
			
		newListItem = xbmcgui.ListItem( infoLabels['Title'] )
		newListItem.setThumbnailImage(thumbnail)
		newListItem.setInfo(u'video', infoLabels)
		
		if len(contextMenuItems) > 0:
			newListItem.addContextMenuItems( contextMenuItems )

		return newListItem
		
		
	#==============================================================================
	# createListItems
	#
	# Create an XBMC list item for each episode
	#==============================================================================
	def createListItems(self, mycgi):
		listItems = []
		epsDict = dict()
		
		#episodeIndex = 0
		for entry in self.entries:
			episodeDetail = EpisodeDetail(entry, self.log)
			self.episodeDetails[episodeDetail.assetId] = episodeDetail 
			
			episodeDetail.refine(self.showId, self.showTitle)
			
			newListItem = self.createNewListItem( episodeDetail )
			
			url = self.baseURL + u'&ep=' + mycgi.URLEscape(episodeDetail.assetId) + u"&show=" + mycgi.URLEscape(self.showId) + u"&seriesNumber=" + mycgi.URLEscape(str(episodeDetail.seriesNum)) + "&episodeNumber=" + mycgi.URLEscape(str(episodeDetail.epNum)) + "&title=" + mycgi.URLEscape(episodeDetail.label) #+ "&swfPlayer=" + mycgi.URLEscape(self.swfPlayer)
			
			listItems.append( (url, newListItem, False) )

		return listItems

	def GetEpisodeDetail(self, matchingAssetId):
		for entry in self.entries:
			episodeDetail = EpisodeDetail(entry, self.log)
			if episodeDetail.assetId == matchingAssetId:
				episodeDetail.refine(self.showId, self.showTitle)
				
				return episodeDetail
			
		return None

	#==============================================================================
	# createNowPlayingListItem
	#
	# Create a single XBMC list item for one particular episode
	#==============================================================================
	def createNowPlayingListItem(self, episodeDetail):

		newListItem = self.createNewListItem(episodeDetail)
		return newListItem
		
"""
{"feed":
	{"link":
		{"self":"http:\/\/ps3.channel4.com\/pmlsd\/the-horse-hoarder.json?platform=ps3",
		"related":["http:\/\/ps3.channel4.com\/pmlsd\/the-horse-hoarder\/episode-guide.json?platform=ps3","http:\/\/ps3.channel4.com\/pmlsd\/the-horse-hoarder\/4od.json?platform=ps3","http:\/\/ps3.channel4.com\/pmlsd\/the-horse-hoarder\/4od\/recommendations.json?platform=ps3"]
		},
	"$":"\n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n",
	"id":"tag:ps3.channel4.com,2009:\/programmes\/the-horse-hoarder",
	"title":"The Horse Hoarder",
	"subtitle":
		{"@type":"html",
		"$":"Pensioner Clwyd Davies has accumulated 52 untamed horses, which he keeps at his home in Wrexham's suburbs"
		},
	"updated":"2013-01-07T12:30:53.872Z",
	"author":
		{"$":"\n	\n  ",
		"name":"Channel 4 Television"
		},
	"logo":
		{"@imageSource":"own",
		"$":"http:\/\/cache.channel4.com\/assets\/programmes\/images\/the-horse-hoarder\/ea8a20f0-2ba9-4648-8eec-d25a0fe35d3c_200x113.jpg"
		},
	"category":[
		{"@term":"http:\/\/ps3.channel4.com\/pmlsd\/tags\/animals.atom?platform=ps3",
		"@scheme":"tag:ps3.channel4.com,2010:\/category\/primary",
		"@label":"Animals"
		},
		{"@term":"http:\/\/ps3.channel4.com\/pmlsd\/tags\/documentaries.atom?platform=ps3",
		"@scheme":"tag:ps3.channel4.com,2010:\/category\/secondary",
		"@label":"Documentaries"
		}],
	"dc:relation.BrandFlattened":false,
	"dc:relation.presentationBrand":"C4",
	"dc:relation.platformClientVersion":1,
	"dc:relation.BrandWebSafeTitle":"the-horse-hoarder",
	"dc:relation.BrandTitle":"The Horse Hoarder",
	"dc:relation.ProgrammeType":"OOS",
	"generator":
		{"@version":"1.43","$":"PMLSD"},
	"entry":
		{"link":
			{"related":"http:\/\/ais.channel4.com\/asset\/3464654",
			"self":"http:\/\/ps3.channel4.com\/pmlsd\/the-horse-hoarder\/episode-guide\/series-1\/episode-1.json?platform=ps3"
			},
		"$":"\n	\n	\n	\n	\n	\n	\n	\n	\n	\n	\n	\n  ",
		"id":"tag:ps3.channel4.com,2009:\/programmes\/the-horse-hoarder\/episode-guide\/series-1\/episode-1",
		"title":"The Horse Hoarder",
		"summary":
			{"@type":"html",
			"$":"Pensioner Clwyd Davies squats in a derelict house, dedicating his life to caring for 52 wild horses. But he has been reported to the RSPCA. This documentary follows Clwyd's battle to keep his horses."
			},
		"updated":"2013-01-07T12:30:54.027Z",
		"content":
			{"$":"\n	  \n	",
			"thumbnail":
				{"@url":"http:\/\/cache.channel4.com\/assets\/programmes\/images\/the-horse-hoarder\/series-1\/episode-1\/e5c98d93-4f82-4174-b3f1-a1f7d180958a_200x113.jpg",
				"@height":"113",
				"@width":"200",
				"@imageSource":"own",
				"@altText":"The Horse Hoarder"
				}
			},
		"dc:relation.SeriesNumber":1,
		"dc:relation.EpisodeNumber":1,
		"dc:date.Last":"2013-01-07T20:30:00.000Z",
		"dc:relation.LastChannel":"C4"
		}
	}
}
"""
class EpisodeDetail:
	def __init__(self, entry, log):
		self.log = log
		self.label = ""
		self.thumbnail = ""
		player = entry[u'group'][u'player']['@url']
		match = re.search(u'http://ais.channel4.com/asset/(\d+)', player)
		self.assetId= match.group(1)
		self.url = entry[u'link'][u'related']

		try:
			self.epNum = int(entry[u'dc:relation.EpisodeNumber'])
		except (Exception) as exception:
			self.logException(exception, u'dc:relation.EpisodeNumber')
			self.epNum = ""

		try:
			self.hasSubtitles = bool(entry['dc:relation.Subtitles'])
		except (Exception) as exception:
			self.logException(exception, u'dc:relation.Subtitles')
			self.hasSubtitles = False

		try:
			self.thumbnail = entry[u'group'][u'thumbnail'][u'@url']
		except (Exception) as exception:
			self.logException(exception, u'thumbnail')
			self.thumbnail = ""

		try:
			lastDate = date.fromtimestamp(mktime(strptime(entry[u'dc:date.TXDate'], u"%Y-%m-%dT%H:%M:%S.%fZ")))
			self.premieredDate = lastDate.strftime(u"%d.%m.%Y")
		except (Exception) as exception:
			self.logException(exception, u'dc:date.Last')
			self.premieredDate = ""

		try:
			self.epTitle = unicode(entry[u'title'])
		except (Exception) as exception:
			self.logException(exception, u'title')
			self.epTitle = ""

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

		self.log (u'Episode details: ' + unicode((self.assetId,self.epNum,self.url,self.thumbnail,self.premieredDate,self.epTitle,self.description,self.seriesNum,self.hasSubtitles)), xbmc.LOGDEBUG)

	def refine(self, showId, showTitle):
		if ( self.seriesNum == u"" or self.epNum == u"" ):
			pattern = u'series-([0-9]+)(\\\)?/episode-([0-9]+)'
			seasonAndEpisodeMatch = re.search( pattern, self.url, re.DOTALL | re.IGNORECASE )

			self.log(u"Searching for season and episode numbers in url: %s" % self.url)
			if seasonAndEpisodeMatch is not None:
				self.seriesNum = int(seasonAndEpisodeMatch.group(1))
				self.epNum = int(seasonAndEpisodeMatch.group(3))
			
#				self.log( "End1: %s" % str(self.seriesNum), xbmc.LOGDEBUG)
#				self.log( str(self.epNum), xbmc.LOGDEBUG)

#		self.log( "End2: %s" % str(self.seriesNum), xbmc.LOGDEBUG)
#		self.log( str(self.epNum), xbmc.LOGDEBUG)

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
		

