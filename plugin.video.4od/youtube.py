import re
import os
import xbmc
import xbmcgui
import utils
import urllib2
import contextlib

from errorhandler import ErrorCodes
from errorhandler import ErrorHandler

from geturllib import CacheHelper
from xbmc import log
__PluginName__  = 'plugin.video.4od'

from xbmcaddon import Addon

__addon__ = Addon(__PluginName__)
__language__ = __addon__.getLocalizedString

DATA_FOLDER  		= xbmc.translatePath( os.path.join( "special://masterprofile","addon_data", __PluginName__ ) )
YOUTUBE_CHECK_FILE     	= os.path.join( DATA_FOLDER, 'YoutubeCheck' )
TITLECHANGES_PATH = os.path.join( __addon__.getAddonInfo( "path" ), "titlechanges.txt" )



class YouTube:
	def __init__(self, cache, platform):
		self.cache = cache
		self.platform = platform
		self.installed = False

		self.titleChanges = {}
		with open(TITLECHANGES_PATH) as f:
			for line in f:
				if len(line) > 0:
					(key, val) = line.split(',')
					self.titleChanges[key] = val

	def getYoutubeUrlFromId(self, youtubeId):
		if 'xbox' == self.platform:
		  url = "plugin://video/YouTube/?path=/root/video&action=play_video&videoid=" + youtubeId
		else:
		  url = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + youtubeId

		return url

	def downloadFromYoutube(self, youtubeId):
		if 'xbox' == self.platform:
		  url = "plugin://video/YouTube/?path=/root/video&action=download&videoid=" + youtubeId
		else:
		  url = "plugin://plugin.video.youtube/?path=/root/video&action=download&videoid=" + youtubeId

		xbmc.executebuiltin('XBMC.RunPlugin(%s)' % url)

	def verifyYoutubePage(self, youtubeId, seriesTarget, episodeTarget):
		(episodePage, logLevel) = self.cache.GetURLFromCache( "http://www.youtube.com/watch?v=%s&has_verified=1&has_verified=1" % youtubeId, 40000 )

		if episodePage is None or len(episodePage) == 0:
			# Error getting episodePage from Youtube. youtube id:
			log (__language__(30900) + youtubeId, logLevel)
			return False

		(episodeCandidate, error) = utils.findString('verifyYoutubePage', 'Season %s Ep\. ([0-9]+)' % seriesTarget, episodePage)

		# episodeCandidate: 
		log (__language__(30905) + str(episodeCandidate), xbmc.LOGDEBUG)

		if episodeCandidate is not None and int(episodeCandidate) == episodeTarget:
			return True

		if error is not None:
			# Error verifying Youtube page
			error.process(__language__(30880), '', xbmc.LOGDEBUG)

		return False

	def videoFromPlaylist(self, playlist, seriesNumber, episodeNumber):
		# Best guess - assume that the episodes are listed in order starting with 1. Works out that way a lot of the time, but not always.
		(youtubeId, error) = utils.findString('videoFromPlaylist', 'href="/watch\?v=([^&]*?)&[^"]*?index=%s' % episodeNumber, playlist)

		if error is None:

			# Verify 
			if self.verifyYoutubePage(youtubeId, seriesNumber, episodeNumber):
				return (youtubeId, None)

	
		# Try each index in turn	
		youtubeIdList = re.findall( 'href="/watch\?v=([^&]*?)&[^"]*?index=[0-9]*?', playlist, re.DOTALL | re.IGNORECASE )

		for youtubeId in youtubeIdList:
			if self.verifyYoutubePage(youtubeId, seriesNumber, episodeNumber):
				return (youtubeId, None)

		# Season %i, Episode %i
		error = ErrorHandler('videoFromPlaylist', ErrorCodes.UNABLE_TO_FIND_YOUTUBE_ID, __language__(30935) % (seriesNumber, episodeNumber))

		log ('videoFromPlaylist: youtubeId, error: %s, %s' % (str(youtubeId), str(error)))
		return (None, error)	
	
	# Workaround for incorrectly formed Youtube show URLs
	def getShowURL(self, title):
		if title == 'gordonbehindbars':
			return "http://www.youtube.com/channel/SWR_nf_mWkeWs"
		elif title == 'lifers':
			return "http://www.youtube.com/channel/SW2VCLcwGuST4"
		
		return  "http://www.youtube.com/show/%s" % title
	
		
	def getYoutubeId(self, title, seriesNumber, episodeNumber):
		# Searching Youtube...
		log (__language__(30910), xbmc.LOGWARNING)

		youtubeId = None
		title = title.replace( '-', '' )

		if title in self.titleChanges:
			log('Change title from "%s" to "%s" for Youtube processing' % (title, self.titleChanges[title]), xbmc.LOGDEBUG)
			title = self.titleChanges[title]
			
		if seriesNumber <> '' and episodeNumber <> '':
			log ('seriesNumber, episodeNumber: %s, %s, ' % (str(seriesNumber), str(episodeNumber)), xbmc.LOGDEBUG)

			(tubeShow, logLevel) = self.cache.GetURLFromCache( self.getShowURL(title), 600 )
		
			if tubeShow is None or tubeShow == '':
				error = ErrorHandler('getYoutubeId', ErrorCodes.ERROR_GETTING_YOUTUBE_SHOW, '')
				return ( None, error )

			(playlistAppendage, error) = utils.findString('getYoutubeId', 'href="([^"]*?)">\s+Season %s Episodes' % seriesNumber, tubeShow)

			if error is None:
				(tubeSeasonPlaylist, logLevel) = self.cache.GetURLFromCache( "http://www.youtube.com%s" % playlistAppendage, 600 )

				if tubeSeasonPlaylist is None or tubeSeasonPlaylist == '':
					error = ErrorHandler('getYoutubeId', ErrorCodes.ERROR_GETTING_YOUTUBE_SEASON, '')
					return ( None, error )

				#log ('seriesNumber, episodeNumber: %s, %s' % (str(seriesNumber), str(episodeNumber)), xbmc.LOGDEBUG)

				(youtubeId, error) = self.videoFromPlaylist(tubeSeasonPlaylist, seriesNumber, episodeNumber)
				log ('youtubeId, error: %s, %s' % (str(youtubeId), str(error)))
				

		else:
			# defaultFilename: 
			error = ErrorHandler('getYoutubeId', ErrorCodes.CANNOT_DETERMINE_SHOW_NUMBERS, __language__(30925) )


		return (youtubeId, error)


	def getYoutubeUrl(self, showId, seriesNumber, episodeNumber, logLevel):
		(youtubeId, errorYoutube) = self.getYoutubeId(showId, seriesNumber, episodeNumber)

		log ('getYoutubeUrl: youtubeId, error: %s, %s' % (str(youtubeId), str(errorYoutube)))

		if errorYoutube is None:
			playUrl = self.getYoutubeUrlFromId(youtubeId)
		else:
			playUrl = None
			# Error streaming video from Youtube, It's possible that this programme is not available from 4od on Youtube (e.g. all US shows) or is not avilable on Youtube yet
			errorYoutube.process(__language__(30850), __language__(30855), logLevel)

		return (youtubeId, playUrl, errorYoutube)

	#==============================================================================
	# isNotOnYoutube
	#
	# Decide whether or not to prefix title with '[Not on Youtube]'
	#==============================================================================
	def isNotOnYoutube(self, episodeIndex, showId, seriesNum, epNum, premieredDate):
		if premieredDate is None or premieredDate == '':
			log ('isNotOnYoutube: Invalid premiereDate', xbmc.LOGERROR)
			return False

		if episodeIndex is None or episodeIndex == '':
			log ('isNotOnYoutube: Invalid episodeIndex', xbmc.LOGERROR)
			return False

		if showId is None or showId == '':
			log ('isNotOnYoutube: Invalid showId', xbmc.LOGERROR)
			return False

		if seriesNum is None or seriesNum == '':
			log ('isNotOnYoutube: Invalid seriesNum', xbmc.LOGERROR)
			return False

		if epNum is None or epNum == '':
			log ('isNotOnYoutube: Invalid epNum', xbmc.LOGERROR)
			return False

		log ('isNotOnYoutube: showId: %s, seriesNumber: %s, episodeNumber: %s, episodeIndex: %s, premieredDate: %s, youtube_force_check: "%s"' % (str(showId), str(seriesNum), str(epNum), str(episodeIndex), premieredDate, str(__addon__.getSetting( 'youtube_force_check' ))), xbmc.LOGDEBUG)
		# Only do this for the first two episodes, or for all episodes (since Aug 13 2012) if force_check is on
		if episodeIndex > 1 and not __addon__.getSetting( 'youtube_force_check' ):
			log ('isNotOnYoutube: Not checking youtube - episodeIndex > 1 and youtube_force_check not set', xbmc.LOGDEBUG)
			return False
		
		# Only applies to recent episodes
		if not utils.isRecentDate(premieredDate):
			log ('isNotOnYoutube: Not checking youtube - not a recent episode', xbmc.LOGDEBUG)
			return False

		(youtubeId, errorYoutube) = self.getYoutubeId(showId, seriesNum, epNum)
		if youtubeId is None:
			# Episode not found, use the prefix
			log ('isNotOnYoutube: Episode not found, use the prefix', xbmc.LOGDEBUG)
			return True

		log ('isNotOnYoutube: Episode found, not using the prefix', xbmc.LOGDEBUG)
		return False


