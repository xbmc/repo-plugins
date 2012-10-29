########################################
#  Digitally Imported XBMC plugin
#  by Tim C. 'Bitcrusher' Steinmetz
#  http://qualisoft.dk
#  Github: https://github.com/Bitcrusher/Digitally-Imported-XBMC-plugin
#  Git Read-only: git://github.com/Bitcrusher/Digitally-Imported-XBMC-plugin.git
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#

import os
import sys
import re
import urllib
import urllib2
import string
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import pickle
import time
import unicodedata
from xml.dom import minidom
from httpcomm import HTTPComm	


# Import JSON - compatible with Python<v2.6
try:
    import json
except ImportError:
    import simplejson as json

# Various vars used throughout the script
HANDLE = int(sys.argv[1])
ADDON = xbmcaddon.Addon(id='plugin.audio.jazzradio.com')

# Plugin constants
__plugin__       = ADDON.getAddonInfo('name')
__author__       = "Tim C. Steinmetz"
__url__          = "http://qualisoft.dk/"
__platform__     = "xbmc media center, [LINUX, OS X, WIN32]"
__date__         = "2. October 2012"
__version__      = ADDON.getAddonInfo('version')

class musicAddonXbmc:
	_addonProfilePath = xbmc.translatePath( ADDON.getAddonInfo('profile') ).decode('utf-8') # Dir where plugin settings and cache will be stored
	
	_checkinKey 	= "381b49f1b3522ea7fd125245c66e63537776726c"
	
	_cacheStreams	= _addonProfilePath + "cache_streamlist.dat"
	_cacheListenkey	= _addonProfilePath + "cache_listenkey.dat"
	_checkinFile	= _addonProfilePath + "cache_lastcheckin.dat"
	
	_baseUrl 		= "http://www.jazzradio.com/"
	_loginUrl		= "http://www.jazzradio.com/login"
	_listenkeyUrl	= "http://www.jazzradio.com/member/listen_key"
	
	_publicStreamsJson40k	= "http://listen.jazzradio.com/public3/"		# Public AAC 40k/sec AAC+ JSON url
	_premiumStreamsJson40k	= "http://listen.jazzradio.com/premium_low/" 	# AAC 40k/sec AAC+ JSON url
	_premiumStreamsJson64k	= "http://listen.jazzradio.com/premium_medium/"	# AAC 64k/sec AAC+ JSON url
	_premiumStreamsJson128k	= "http://listen.jazzradio.com/premium/"		# AAC 128k/sec AAC+ JSON url
	_favoritesStreamJson40k	= "http://listen.jazzradio.com/premium_low/favorites.pls" 		# Favorites AAC 40k/sec AAC+ playlist url
	_favoritesStreamJson64k	= "http://listen.jazzradio.com/premium_medium/favorites.pls"	# Favorites AAC 64k/sec AAC+ playlist url
	_favoritesStreamJson128k= "http://listen.jazzradio.com/premium/favorites.pls"			# Favorites AAC 128k/sec AAC+ playlist url
	
	_httpComm = HTTPComm() # Init CURL thingy
	_frontpageHtml = ""
	
	_newChannels = 0
	_bitrate = 40
	
	def __init__( self ) :
		# If stats is allowed and its been at least 24 hours since last checkin
		if (ADDON.getSetting('allowstats') == "true") and (self.checkFileTime(self._checkinFile, self._addonProfilePath, 86400) == True) :
			open(self._checkinFile, "w")
			
			account = 'public'
			if ADDON.getSetting('username') != "" :
				account = 'premium'
		
			xbmc.log( 'Submitting stats', xbmc.LOGNOTICE )
			self._httpComm.get('http://stats.qualisoft.dk/?plugin=' +  ADDON.getAddonInfo('id') +'&version=' + __version__ + '&account=' + account + '&key=' + self._checkinKey)
			print 'http://stats.qualisoft.dk/?plugin=' +  ADDON.getAddonInfo('id') +'&version=' + __version__ + '&account=' + account + '&key=' + self._checkinKey
		xbmc.log( "[PLUGIN] %s v%s (%s)" % ( __plugin__, __version__, __date__ ), xbmc.LOGNOTICE )

		
	# Let's get some tunes!
	def start( self ) :
		jsonList = [] 	# list that data from the JSON will be put in
		streamList = []	# the final list of channels, with small custom additions
		
		# Check if cachefile has expired
		if ADDON.getSetting("forceupdate") == "true" or ((int( ADDON.getSetting("cacheexpire") ) * 60) != 0 and self.checkFileTime(self._cacheStreams, self._addonProfilePath, (int( ADDON.getSetting("cacheexpire") ) * 60)) == True) :
			listenkey = ""	# will contain the premium listenkey
			
			if ADDON.getSetting('username') != "" and ADDON.getSetting("usefavorites") == 'false' : # if username is set and not using favorites
				xbmc.log( "Going for Premium streams", xbmc.LOGNOTICE )
				
				# Checks if forceupdate is set and if the listenkey cachefile exists
				if ADDON.getSetting("forceupdate") == "true" or not os.path.exists(self._cacheListenkey) :
					listenkey = self.getListenkey()
					pickle.dump( listenkey, open(self._cacheListenkey, "w"), protocol=0 ) # saves listenkey for further use
				else :
					listenkey = pickle.load( open(self._cacheListenkey, "r") )
				
				if ADDON.getSetting('bitrate') == '0' :
					self._bitrate = 40
					jsonList = self.getJSONChannelList( self._premiumStreamsJson40k )
					streamList = self.customizeStreamListAddMenuitem( jsonList, listenkey )
				elif ADDON.getSetting('bitrate') == '1' :
					self._bitrate = 64
					jsonList = self.getJSONChannelList( self._premiumStreamsJson64k )
					streamList = self.customizeStreamListAddMenuitem( jsonList, listenkey )
				else :
					self._bitrate = 128
					jsonList = self.getJSONChannelList( self._premiumStreamsJson128k )
					streamList = self.customizeStreamListAddMenuitem( jsonList, listenkey )
				
				xbmc.log( "Bitrate set to " + str( self._bitrate ), xbmc.LOGNOTICE )
				
				
			elif ADDON.getSetting('username') != "" and ADDON.getSetting("usefavorites") == 'true' : # if username is set and wants to use favorites
				xbmc.log( "Going for Premium favorite streams", xbmc.LOGNOTICE )
				listenkey = self.getListenkey()
				if ADDON.getSetting('bitrate') == '0' :
					self._bitrate = 40
					streamList = self.getFavoriteStreamsList( self._favoritesStreamJson40k + "?" + listenkey )
				elif ADDON.getSetting('bitrate') == '1' :
					self._bitrate = 64
					streamList = self.getFavoriteStreamsList( self._favoritesStreamJson64k + "?" + listenkey )
				else :
					self._bitrate = 128
					streamList = self.getFavoriteStreamsList( self._favoritesStreamJson128k + "?" + listenkey )
				
				xbmc.log( "Bitrate set to " + str(self._bitrate), xbmc.LOGNOTICE )
				
				for channel in streamList :
					self.addItem( channel['name'], channel['playlist'], channel["description"], channel['bitrate'], self._addonProfilePath + "art_" + channel['key'] + ".png", channel['isNew'] )

			else :
				xbmc.log( "Going for Public streams", xbmc.LOGNOTICE )
				jsonList = self.getJSONChannelList( self._publicStreamsJson40k )
				streamList = self.customizeStreamListAddMenuitem(jsonList, "") # sending a blank string as listenkey

			# save streams to cachefile
			pickle.dump( streamList, open(self._cacheStreams, "w"), protocol=0 )
			
			if (self._newChannels > 0) : # Yay! New channels found
				xbmc.log( ADDON.getLocalizedString(30130) + " " + ADDON.getLocalizedString(30131) + str(self._newChannels) + ADDON.getLocalizedString(30132) + " " + ADDON.getLocalizedString(30133) + " " + ADDON.getLocalizedString(30134), xbmc.LOGNOTICE )
				xbmcgui.Dialog().ok( ADDON.getLocalizedString(30130), ADDON.getLocalizedString(30131) + str(self._newChannels) + ADDON.getLocalizedString(30132), ADDON.getLocalizedString(30133),ADDON.getLocalizedString(30134) )

		else :
			xbmc.log( "Using cached streams", xbmc.LOGNOTICE )
			streamList = pickle.load( open(self._cacheStreams, "r") )

			# Add streams to GUI
			for channel in streamList :	
				self.addItem( channel['name'], channel['playlist'], channel["description"], channel['bitrate'], self._addonProfilePath + "art_" + channel['key'] + ".png", channel['isNew'] )
		
		# If streams should be sorted A-Z
		if ADDON.getSetting('sortaz') == "true" :
			xbmcplugin.addSortMethod( HANDLE, sortMethod=xbmcplugin.SORT_METHOD_LABEL )
		
		# End of channel list
		xbmcplugin.endOfDirectory( HANDLE, succeeded=True )

		# Resets the 'Force refresh' setting
		ADDON.setSetting( id="forceupdate", value="false" )
		
		return True
		
		
	"""Return list - False if it fails
	Gets the favorites playlist and returns the streams as a list
	Also every channel is added to the GUI from here, as the progress indication
	in the GUI would not reflect that something is actually happening till the very end
	"""
	def customizeStreamListAddMenuitem( self, list, listenkey ) :
		# Precompiling regexes		
		streamurl_re = re.compile('File\d+=([^\n]*)', re.I) # streams in .pls file
		
		streamList = []
		
		# Will add list elements to a new list, with a few additions
		for channel in list :
			channel['key'] = self.makeChannelIconname( channel['name'] ) # customize the key that is used to find channelart
			channel['isNew'] = False # is used to highlight when it's a new channel
			channelArt = "art_" + channel['key'] + ".png"
			channel['bitrate'] = self._bitrate
		
			if ADDON.getSetting('username') != "" : # append listenkey to playlist url if username is set
				channel['playlist'] = self.getFirstStream( channel['playlist'] + "?" + listenkey, streamurl_re )
			else :
				channel['playlist'] = self.getFirstStream( channel['playlist'], streamurl_re )
				
			if (not os.path.isfile(self._addonProfilePath + channelArt)) : # if channelart is not in cache
				print "Channelart for " + channel['name'].encode('ascii', 'ignore') + " not found in cache at " + self._addonProfilePath + channelArt
				self.getChannelArt( channel['id'], "art_" + channel['key'] )
				channel['isNew'] = True
				self._newChannels = self._newChannels + 1
			
			streamList.append( channel )
			
			# I'd have prefeered it if I didn't have to add menuitem from within this method
			# but I have to, too give the user some visual feedback that stuff is happening
			self.addItem( channel['name'].encode('utf-8'), channel['playlist'], channel["description"], self._bitrate, self._addonProfilePath + "art_" + channel['key'] + ".png", channel['isNew'] )

		return streamList # returns the channellist so it can be saved to cache
	
	
	"""return bool
	Will check if channelart/icon is present in cache - if not, try to download
	"""
	def getChannelArt( self, channelId, channelKey ) :
		channelArt_re = re.compile('data-id="' + str(channelId) +'">(?:[\n\s]*)<a(?:[^>]*)><img(?:[^>]*)src="([^"]*)"', re.I)
		
		try :
			if (self._frontpageHtml == "") : # If frontpage html has not already been downloaded, do it
				self._frontpageHtml = self._httpComm.get( self._baseUrl )
		
			channelartDict = channelArt_re.findall( self._frontpageHtml )

			# Will download and save the channelart to the cache
			self._httpComm.getImage( channelartDict[0], self._addonProfilePath + channelKey + ".png" )

			return True

		except Exception :
			sys.exc_clear() # Clears all exceptions so the script will continue to run
			xbmcgui.Dialog().ok( ADDON.getLocalizedString(30160), ADDON.getLocalizedString(30161), ADDON.getLocalizedString(30162) + channelartDict[0] )
			xbmc.log( ADDON.getLocalizedString(30160) + " " + ADDON.getLocalizedString(30161) + channelKey + " " + ADDON.getLocalizedString(30162)+ channelartDict[0], xbmc.LOGERROR )
			return False
		
		return True
	
	
	"""return String
	Extracts the premium listenkey from the frontpage html
	"""
	def getListenkey( self ) :
		listenkey_re = re.compile('Key is:<br />[^<]*<strong>([\w\d]*)<', re.DOTALL)
		
		try :
			logindata = urllib.urlencode({	'member_session[username]':  ADDON.getSetting('username'),
											'member_session[password]':  ADDON.getSetting('password') })
			
			self._httpComm.post( self._loginUrl, logindata ) # logs in so the listenkey page is accessible
			
			listenkeyHtml = self._httpComm.get( self._listenkeyUrl)
			listenkeyDict = listenkey_re.findall( listenkeyHtml )
			
			xbmc.log( "Found listenkey", xbmc.LOGNOTICE )
			return listenkeyDict[0]

		except Exception :
			sys.exc_clear() # Clears all exceptions so the script will continue to run
			xbmcgui.Dialog().ok( ADDON.getLocalizedString(30100), ADDON.getLocalizedString(30101), ADDON.getLocalizedString(30102) )
			xbmc.log( ADDON.getLocalizedString(30100) + " " + ADDON.getLocalizedString(30101) + " " + ADDON.getLocalizedString(30102), xbmc.LOGERROR )
			return False
		
		return False

	
	"""return list - False if it fails
	Will get a HTML page containing JSON data, decode it and return
	"""
	def getJSONChannelList( self, url ) :
		try :
			jsonData = self._httpComm.get( url )
			jsonData = jsonData.encode('ascii', 'replace')
			jsonData = json.loads(jsonData)
		except Exception : # Show error message in XBMC GUI if failing to parse JSON
			sys.exc_clear() # Clears all exceptions so the script will continue to run
			xbmcgui.Dialog().ok( ADDON.getLocalizedString(30100), ADDON.getLocalizedString(30101), ADDON.getLocalizedString(30102) )
			xbmc.log( ADDON.getLocalizedString(30100) + " " + ADDON.getLocalizedString(30101) + " " + ADDON.getLocalizedString(30102), xbmc.LOGERROR )
			return False

		return jsonData
	
	
	"""return list - False if it fails
	Gets the favorites playlist and returns the streams as a list
	"""
	def getFavoriteStreamsList( self, url ) :
		try :
			favoritesPlaylist = self._httpComm.get( url ) # favorites .pls playlist in plaintext
			favoritesList = [] # list that will contain streamlist
			
			streamurl_re 	= re.compile( 'File\d+=([^\n]*)', re.I ) # first stream in .pls file
			channeltitle_re = re.compile( 'Title\d+=([^\n]*)', re.I )
			
			streamTitles = channeltitle_re.findall( favoritesPlaylist )
			streamUrls	= streamurl_re.findall( favoritesPlaylist )
			
			if len(streamUrls) == len( streamTitles ) : # only continue if the count of urls and titles are equal
				for streamUrl in streamUrls :
					listitem = {}
					listitem['playlist'] = streamUrl
					tmp_name = streamTitles.pop()
					listitem['name'] = tmp_name.replace( "JAZZRADIO.com - ", "" ) # favorite stream titles has some "fluff" text it that is removed
					listitem['key'] = self.makeChannelIconname( listitem['name'] )
					listitem['isNew'] = False
					listitem['bitrate'] = self._bitrate
					listitem['description'] = ""
					favoritesList.append( listitem )
					
			else :
				return False

			return favoritesList
			
		except Exception : # Show error message in XBMC GUI if failing to parse JSON
			#sys.exc_clear() # Clears all exceptions so the script will continue to run
			xbmcgui.Dialog().ok( ADDON.getLocalizedString(30120), ADDON.getLocalizedString(30111), url )
			xbmc.log( ADDON.getLocalizedString(30120) + " " + ADDON.getLocalizedString(30111) + " " + url, xbmc.LOGERROR )
			return False

		return favoritesList

	
	"""return string
	Will take a channelname, lowercase it and remove spaces, dashes and other special characters
	The string returned is normally used as part of the filename for the channelart
	"""
	def makeChannelIconname( self, channelname ) :
		iconreplacement_re = re.compile('[^a-z0-9]', re.I) # regex that hits everything but a-z and 0-9
		iconname = string.lower(iconreplacement_re.sub( '', channelname) )
		return iconname
	
	
	"""return bool
	Simply adds a music item to the XBMC GUI
	"""
	# Adds item to XBMC itemlist
	def addItem( self, channelTitle, streamUrl, streamDescription, streamBitrate, icon, isNewChannel ) :

		if isNewChannel == True : # tart it up a bit if it's a new channel
			li = xbmcgui.ListItem(label="[COLOR FF007EFF]" + channelTitle + "[/COLOR]",thumbnailImage=icon)
			xbmc.log( "New channel found: " + channelTitle, xbmc.LOGERROR )
		else :
			li = xbmcgui.ListItem(label=channelTitle, thumbnailImage=icon)

		li.setProperty("mimetype", 'audio/aac')
		li.setInfo( type="Music", infoLabels={ "label": channelTitle, "Genre": channelTitle, "Comment": streamDescription, "Size": (streamBitrate * 1024)  })
		li.setProperty("IsPlayable", "true")
		li.setProperty("IsLive", "true")

		xbmcplugin.addDirectoryItem(handle=HANDLE, url=streamUrl, listitem=li, isFolder=False)
		
		return True

	
	"""return string
	Gets the first stream from a playlist
	"""
	def getFirstStream( self, playlistUrl, regex ) :
		plsData = self._httpComm.get( playlistUrl )
		streamurls = regex.findall(plsData)
		
		return streamurls[0]
	

	"""return bool
	Checks if a file is older than x seconds
	"""
	def checkFileTime( self, tmpfile, cachedir, timesince ) :
		if not os.path.exists( cachedir ) :
			os.makedirs( cachedir )
			return False
		
		# If file exists, check timestamp
		if os.path.exists( tmpfile ) :
			if os.path.getmtime( tmpfile ) > ( time.time() - timesince ) :
				xbmc.log( 'It has not been ' + str( timesince/60 ) + ' minutes since ' + tmpfile + ' was last updated', xbmc.LOGNOTICE )
				return False
			else :
				xbmc.log( 'The cachefile ' + tmpfile + ' + has expired', xbmc.LOGNOTICE )
				return True
		# If file does not exist, return true so the file will be created by scraping the page
		else :
			xbmc.log( 'The cachefile ' + tmpfile + ' does not exist', xbmc.LOGNOTICE )
			return True
	
			
MusicAddonInstance = musicAddonXbmc()
MusicAddonInstance.start()
