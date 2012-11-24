# -*- coding: utf-8 -*-
import re

import xbmc
import xbmcgui
from xbmc import log

from errorhandler import ErrorCodes
from errorhandler import ErrorHandler
from geturllib import CacheHelper

import utils
from xbmcaddon import Addon

__PluginName__  = 'plugin.video.4od'
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

	def __init__(self, baseURL, cache):
		self.assetId 		= ''
		self.baseURL		= baseURL
		self.cache 		= cache

	def getAssetId(self):
		return self.assetId

	def getHTML(self):
		return self.html


	def initialise(self, showId, showTitle):
		method = "EpisodeList.initialise"
		log ("initialise showId: %s, showTitle: %s " % ( showId, showTitle ), xbmc.LOGDEBUG)
		(self.html, logLevel) = self.cache.GetURLFromCache( "http://www.channel4.com/programmes/" + showId + "/4od", 600 ) # 10 minutes

		if self.html is None or self.html == '':
			error = ErrorHandler('EpisodeList.initialise', ErrorCodes.ERROR_GETTING_EPISODE_LIST, __language__(30800))
			return error

		self.swfPlayer = utils.GetSwfPlayer( self.html )

		(self.genre, error) = utils.findString(method, '<meta name="primaryBrandCategory" content="(.*?)"/>', self.html)
		if error is not None:
			# Can't determine genre
			error.process(__language__(30710), "", xbmc.LOGWARNING)
			self.genre = ''

		(ol, error) = utils.findString(method, '<ol class="all-series">(.*?)</div>', self.html)
		if error is not None:
			return error						

		self.listItemsHtml = re.findall( '<li(.*?[^p])>', ol, re.DOTALL | re.IGNORECASE )
		self.showId = showId
		self.showTitle = showTitle

		return None

	def getEpisodeDetails(self, htmlListItem):
		
		dataKeyValues = re.findall('data-([a-zA-Z\-]*?)="(.*?)"', htmlListItem, re.DOTALL | re.IGNORECASE )
		assetId		= ''
		url		= ''
		image		= ''
		premieredDate	= ''
		progTitle	= ''
		epTitle		= ''
		description	= ''
		epNum		= ''
		seriesNum	= ''
		programmeNum = ''


		for dataKeyValue in dataKeyValues:
			if ( dataKeyValue[0].lower() == 'wsprogrammeid' ):
				try: 
					programmeString = re.search( '[0-9]*?-([0-9][0-9][0-9])', dataKeyValue[1], re.DOTALL)
					
					if programmeString:
						programmeNum = int(programmeString.group(1))
				except:
					pass
				continue

			if ( dataKeyValue[0].lower() == 'episode-number' ):
				try: 
					epNum 	= int(dataKeyValue[1])
				except:
					pass
				continue

			if ( dataKeyValue[0].lower() == 'assetid' ):
				assetId		= dataKeyValue[1]
				continue 
			if ( dataKeyValue[0].lower() == 'episodeurl' ):
				url		= dataKeyValue[1]
				continue
			if ( dataKeyValue[0].lower() == 'image-url'):
				image		= dataKeyValue[1]
				continue
			if ( dataKeyValue[0].lower()  == 'txdate'):
				dateParts = dataKeyValue[1].split()
				if len(dateParts) == 3:
					if len(dateParts[0]) == 1:
						dateParts[0] = '0' + dateParts[0]

					dateParts[1] = (dateParts[1])[0:3]

					premieredDate = "%s %s %s" % (dateParts[0], dateParts[1], dateParts[2])
				else:
					premieredDate = dataKeyValue[1]

				continue

			if ( dataKeyValue[0].lower()  == 'episodetitle' ):
				progTitle	= dataKeyValue[1]
				continue
			if ( dataKeyValue[0].lower()  == 'episodeinfo' ):
				epTitle		= dataKeyValue[1]
				continue
			if ( dataKeyValue[0].lower()  == 'episodesynopsis' ):
				description	= dataKeyValue[1]
				continue
			if ( dataKeyValue[0].lower() == 'series-number' ):
				try: 
					seriesNum = int(dataKeyValue[1])
				except:
					pass
				continue


		if assetId <> '':
			log ('Episode details: ' + str((assetId,epNum,url,image,premieredDate,progTitle,epTitle,description,seriesNum,programmeNum)), xbmc.LOGDEBUG)
			self.assetId 		= assetId
			self.epNum 		= epNum
			self.url 		= url
			self.image 		= image
			self.premieredDate 	= premieredDate
			self.progTitle 		= progTitle
			self.epTitle 		= epTitle
			self.description	= description
			self.seriesNum		= seriesNum
			self.programmeNum		= programmeNum


	def refineEpisodeDetails(self):
#		xbmc.log( "Start: %s" % str(self.seriesNum), xbmc.LOGDEBUG)
#		xbmc.log( str(self.epNum), xbmc.LOGDEBUG)
		if ( self.seriesNum == "" or self.epNum == "" ):
			pattern = 'series-([0-9]+?)/episode-([0-9]+?)'
			seasonAndEpisodeList = re.findall( pattern, self.url, re.DOTALL | re.IGNORECASE )

#			xbmc.log( "%s" % seasonAndEpisodeList)
			if len(seasonAndEpisodeList) > 0:
				seasonAndEpisode = seasonAndEpisodeList[0]
				print seasonAndEpisode

				self.seriesNum = int(seasonAndEpisode[0])
				self.epNum = int(seasonAndEpisode[1])
			
#				xbmc.log( "End1: %s" % str(self.seriesNum), xbmc.LOGDEBUG)
#				xbmc.log( str(self.epNum), xbmc.LOGDEBUG)

#		xbmc.log( "End2: %s" % str(self.seriesNum), xbmc.LOGDEBUG)
#		xbmc.log( str(self.epNum), xbmc.LOGDEBUG)

		# Correct inconsistent Come Dine With Me episodes numbers
		if self.epNum <> "" and self.programmeNum <> "" and self.epNum !=  self.programmeNum:
			xbmc.log("Different episode and programmes values: %s, %s" % (self.epNum, self.programmeNum), xbmc.LOGERROR)
			match = re.search('come-dine-with-me/', self.url, re.DOTALL | re.IGNORECASE)
			if match:
					self.epNum =  self.programmeNum


		if ( self.epNum == "" ):
			self.epNum = self.programmeNum

		#elif len(self.premieredDate) > 0:
		#	self.filename = self.showId + "." + self.premieredDate.replace( ' ', '.' )
		#else:
		#	self.filename = self.showId + "." + self.assetId

		self.progTitle = self.progTitle.strip()
		self.progTitle = self.progTitle.replace( '&amp;', '&' )
		self.epTitle = self.epTitle.strip()
		self.showTitle = utils.remove_extra_spaces(utils.remove_square_brackets(self.showTitle))
		if ( self.progTitle == self.showTitle and self.epTitle <> "" ):
			self.label = self.epTitle
		else:
			self.label = self.progTitle

		if self.label == '':
			self.label = self.showTitle

		if len(self.premieredDate) > 0 and self.premieredDate not in self.label:
				self.label = self.label + '  [' + self.premieredDate + ']'

		self.description = utils.remove_extra_spaces(utils.remove_html_tags(self.description))
		self.description = self.description.replace( '&amp;', '&' )
		self.description = self.description.replace( '&pound;', '£')
		self.description = self.description.replace( '&quot;', "'" )

		if (self.image == ""):
			(self.thumbnail, error) = utils.findString('EpisodeList.refineEpisodeDetails', '<meta property="og:image" content="(.*?)"', self.html)
			if error is not None:
				# Error getting image
				error.process(ERROR_GETTING_IMAGE, "", xbmc.LOGWARNING)
				self.thumbnail = ''

		else:
			self.thumbnail = "http://www.channel4.com" + self.image


	def createNewListItem(self):
		newListItem = xbmcgui.ListItem( self.label )
		newListItem.setThumbnailImage(self.thumbnail)

		infoLabels = {'Title': self.label, 'Plot': self.description, 'PlotOutline': self.description, 'Genre': self.genre, 'premiered': self.premieredDate}

		if self.epNum <> '':
			infoLabels['Episode'] = self.epNum
 
		newListItem.setInfo('video', infoLabels)

		return newListItem


	#==============================================================================
	# createListItems
	#
	# Create an XBMC list item for each episode
	#==============================================================================
	def createListItems(self, mycgi, youtube):
		
	        listItems = []
	        epsDict = dict()

		episodeIndex = 0
	        for listItemHtml in self.listItemsHtml:
	                self.getEpisodeDetails(listItemHtml)

	                if (self.assetId == ''):
        	                continue;

    		        if ( self.assetId in epsDict ):
				continue

        	        epsDict[self.assetId] = 1

			self.refineEpisodeDetails()

			if youtube.isNotOnYoutube(episodeIndex, self.showId, self.seriesNum, self.epNum, self.premieredDate):
				self.label = '[Not on Youtube] ' + self.label

			episodeIndex = episodeIndex + 1

	                newListItem = self.createNewListItem( )
	                #url = self.baseURL + '?ep=' + mycgi.URLEscape(self.assetId) + "&show=" + mycgi.URLEscape(self.showId) + "&title=" + mycgi.URLEscape(self.label) + "&fn=" + mycgi.URLEscape(self.filename) + "&swfPlayer=" + mycgi.URLEscape(self.swfPlayer)
			url = self.baseURL + '?ep=' + mycgi.URLEscape(self.assetId) + "&show=" + mycgi.URLEscape(self.showId) + "&seriesNumber=" + mycgi.URLEscape(str(self.seriesNum)) + "&episodeNumber=" + mycgi.URLEscape(str(self.epNum)) + "&title=" + mycgi.URLEscape(self.label) + "&swfPlayer=" + mycgi.URLEscape(self.swfPlayer)

	                listItems.append( (url,newListItem,False) )


		return listItems


	#==============================================================================
	# createNowPlayingListItem
	#
	# Create a single XBMC list item for one particular episode
	#==============================================================================
	def createNowPlayingListItem(self, matchingAssetId):
		
	        for listItemHtml in self.listItemsHtml:
	                self.getEpisodeDetails(listItemHtml)

	                if (self.assetId <> matchingAssetId):
        	                continue;

			self.label = ''
			self.thumbnail = ''
			self.refineEpisodeDetails()

			newListItem = self.createNewListItem()
			return newListItem


