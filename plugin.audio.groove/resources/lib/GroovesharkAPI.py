# Copyright 2011 Stephen Denham

#    This file is part of xbmc-groove.
#
#    xbmc-groove is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    xbmc-groove is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with xbmc-groove.  If not, see <http://www.gnu.org/licenses/>.

import urllib2, pprint, md5, os, pickle, tempfile, time, re, simplejson, base64, sys, socket
from blowfish import Blowfish

SESSION_EXPIRY = 1209600 # 2 weeks

# Web app
WEB_APP_URL = "http://xbmc-groove.appspot.com/"

# GrooveAPI constants
THUMB_URL = 'http://beta.grooveshark.com/static/amazonart/m'
SONG_LIMIT = 25
ALBUM_LIMIT = 15
ARTIST_LIMIT = 15
SONG_SUFFIX = '.mp3'

# Main API
class GrooveAPI:

	_ip = '0.0.0.0'
	_country = ''
	_sessionID = ''
	_userID = 0
	_lastSessionTime = 0
	_key = md5.new(os.path.basename("GroovesharkAPI.py")).hexdigest()
	_debugging = False

	# Constructor
	def __init__(self, debug):
		
		self._debugging = debug
		self.simplejson = simplejson
		if "linux" in sys.platform.lower():
			socket.setdefaulttimeout(30)
			
		self.cacheDir = os.path.join(tempfile.gettempdir(), 'groovesharkapi')
		if os.path.isdir(self.cacheDir) == False:
			os.makedirs(self.cacheDir)
			if self._debugging:
				print "Made " + self.cacheDir
		self._getSavedSession()
		# session ids last 2 weeks
		if self._sessionID == '' or time.time()- self._lastSessionTime >= SESSION_EXPIRY:
			self._sessionID = self._getSessionID()
			if self._sessionID == '':
				raise StandardError('Failed to get session id')
			else:
				if self._debugging:
					print "New GrooveAPI session id: " + self._sessionID
				self._ip = self._getIP()
				self._country = self._getCountry()
				self._setSavedSession()

	# Call to API
	def _callRemote(self, method, params):
		try:
			res = self._getRemote(method, params)
			url = res['url']
			postData = res['postData']
		except:
			print "Failed to get request URL and post data"
			return []
		try:
			req = urllib2.Request(url, postData)
			response = urllib2.urlopen(req)
			result = response.read()
			if self._debugging:
				print "Response..."
				pprint.pprint(result)
			response.close()
			result = simplejson.loads(result)
			return result
		except urllib2.HTTPError, e:
			print "HTTP error " + e.code
		except urllib2.URLError, e:
			print "URL error " + e.reason
		except:
			print "Request to Grooveshark API failed"
			return []	


	# Get the API call
	def _getRemote(self, method, params = {}):
		postData = { "method": method, "sessionid": self._sessionID, "parameters": params }
		postData = simplejson.dumps(postData)
		
		cipher = Blowfish(self._key)
		cipher.initCTR()
		encryptedPostData = cipher.encryptCTR(postData)
		encryptedPostData = base64.urlsafe_b64encode(encryptedPostData)
		url = WEB_APP_URL + "?postData=" + encryptedPostData
		req = urllib2.Request(url)
		response = urllib2.urlopen(req)
		result = response.read()
		if self._debugging:
			print "Request..."
			pprint.pprint(result)
		response.close()
		try:
			result = simplejson.loads(result)
			return result
		except:
			return []		

	# Get a session id
	def _getSessionID(self):
		params = {}
		result = self._callRemote('startSession', params)
		if 'result' in result:
			self._lastSessionTime = time.time()
			return result['result']['sessionID']
		else:
			return ''
	
	def _getSavedSession(self):
		path = os.path.join(self.cacheDir, 'session.dmp')
		try:
			f = open(path, 'rb')
			session = pickle.load(f)
			self._sessionID = session['sessionID']
			self._lastSessionTime = session['lastSessionTime']
			self._userID = session['userID']
			self._ip = session['ip']
			self._country = session['country']
			f.close()
		except:
			self._sessionID = ''
			self._lastSessionTime = 0
			self._userID = 0
			self._ip = '0.0.0.0'
			self._country = ''		
			pass		

	def _setSavedSession(self):			
		try:
			# Create the directory if it doesn't exist.
			if not os.path.exists(self.cacheDir):
				os.makedirs(self.cacheDir)
			path = os.path.join(self.cacheDir, 'session.dmp')
			f = open(path, 'wb')
			session = { 'sessionID' : self._sessionID, 'lastSessionTime' : self._lastSessionTime, 'userID': self._userID, 'ip' : self._ip, 'country' : self._country } 
			pickle.dump(session, f, protocol=pickle.HIGHEST_PROTOCOL)
			f.close()
		except:
			print "An error occurred during save session"
			pass
	
	# Get IP
	def _getIP(self):
		try:
			myip = urllib2.urlopen('http://ipecho.net/plain').read()
			if re.match("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$", myip):
				if self._debugging:
					print "IP is " + myip
				return myip
		except:
			return '0.0.0.0'

	# Get country
	def _getCountry(self):
		params = { 'ip' : self._ip }
		response = self._callRemote("getCountry", params)
		return response['result']
	
	# Get userid from name
	def _getUserIDFromUsername(self, username):
		result = self._callRemote('getUserIDFromUsername', {'username' : username})
		if 'result' in result and result['result']['UserID'] > 0:
			return result['result']['UserID']
		else:
			return 0
	
	# Authenticates the user for current API session
	def _authenticate(self, login, password):
		md5pwd = md5.new(password).hexdigest()
		params = {'login': login, 'password': md5pwd}
		
		result = self._callRemote('authenticate', params)
		try:
			uid = result['result']['UserID']
		except:
			uid = 0
		if (uid > 0):
			return uid
		else:
			return 0
	
	# Check the service
	def pingService(self,):
		result = self._callRemote('pingService', {});
		if 'result' in result and result['result'] != '':
			return True
		else:
			return False
	
	# Login
	def login(self, username, password):
		if self._userID <= 0:
			# Check cache
			self._getSavedSession()
			if self._userID <= 0: 
				self._userID = self._authenticate(username, password)
				if self._userID > 0:
					self._setSavedSession()
		return self._userID
		
	# Logs the user out
	def logout(self):
		result = self._callRemote('logout', {'sessionID' : self._sessionID})
		if 'result' in result and result['result']['success'] == True: 
			self._userID = 0
			self._setSavedSession()
			return True
		return False

	# Gets a stream key and host to get song content
	def getSubscriberStreamKey(self, songID):
		params = { "songID": songID, "country": self._country }
		response = self._callRemote("getSubscriberStreamKey", params)
		try: 
			res = response["result"]
			return res
		except:
			return False

	# Search for albums
	def getArtistSearchResults(self, query, limit=ARTIST_LIMIT):
		result = self._callRemote('getArtistSearchResults', {'query' : query,'limit' : limit})
		if 'result' in result:
			return self._parseArtists(result)
		else:
			return []

	# Search for albums
	def getAlbumSearchResults(self, query, limit=ALBUM_LIMIT):
		result = self._callRemote('getAlbumSearchResults', {'query' : query,'limit' : limit})
		if 'result' in result:
			return self._parseAlbums(result)
		else:
			return []
		
	# Search for songs
	def getSongSearchResults(self, query, limit=SONG_LIMIT):
		result = self._callRemote('getSongSearchResults', {'query' : query, 'country' : self._country, 'limit' : limit})
		if 'result' in result:
			return self._parseSongs(result)
		else:
			return []
		
	# Get artists albums
	def getArtistAlbums(self, artistID, limit=ALBUM_LIMIT):
		result = self._callRemote('getArtistVerifiedAlbums', {'artistID' : artistID})
		if 'result' in result:
			return self._parseAlbums(result, limit)
		else:
			return []

	# Get album songs
	def getAlbumSongs(self, albumID, limit=SONG_LIMIT):
		result = self._callRemote('getAlbumSongs', {'albumID' : albumID, 'limit' : limit})
		if 'result' in result:
			return self._parseSongs(result)
		else:
			return []

	# Get artist's popular songs
	def getArtistPopularSongs(self, artistID, limit = SONG_LIMIT):
		result = self._callRemote('getArtistPopularSongs', {'artistID' : artistID})
		if 'result' in result:
			return self._parseSongs(result, limit)
		else:
			return []

	# Gets the popular songs
	def getPopularSongsToday(self, limit=SONG_LIMIT):
		result = self._callRemote('getPopularSongsToday', {'limit' : limit})
		if 'result' in result:
			# Note limit is broken in the Grooveshark getPopularSongsToday method
			return self._parseSongs(result, limit)
		else:
			return []

	# Gets the favorite songs of the logged-in user
	def getUserFavoriteSongs(self):
		if (self._userID == 0):
			return [];
		result = self._callRemote('getUserFavoriteSongs', {})
		if 'result' in result:
			return self._parseSongs(result)
		else:
			return []

	# Get song info
	def getSongsInfo(self, songIDs):
		result = self._callRemote('getSongsInfo', {'songIDs' : songIDs})
		if 'result' in result and 'SongID' in result['result']:
			info = result['result']
			if 'CoverArtFilename' in info and info['CoverArtFilename'] != None:
				info['CoverArtFilename'] = THUMB_URL+info['CoverArtFilename'].encode('ascii', 'ignore')
			else:
				info['CoverArtFilename'] = 'None'
			return info
		else:
			return 'None'
		
	# Add song to user favorites
	def addUserFavoriteSong(self, songID):
		if (self._userID == 0):
			return False;
		result = self._callRemote('addUserFavoriteSong', {'songID' : songID})
		return result['result']['success']

	# Remove songs from user favorites
	def removeUserFavoriteSongs(self, songIDs):
		if (self._userID == 0):
			return False;
		result = self._callRemote('removeUserFavoriteSongs', {'songIDs' : songIDs})
		return result['result']['success']

	# Gets the playlists of the logged-in user
	def getUserPlaylists(self):
		if (self._userID == 0):
			return [];
		result = self._callRemote('getUserPlaylists', {})
		if 'result' in result:
			return self._parsePlaylists(result)
		else:
			return []
		
	# Gets the playlists of the logged-in user
	def getUserPlaylistsByUsername(self, username):
		userID = self._getUserIDFromUsername(username)
		if (userID > 0):
			result = self._callRemote('getUserPlaylistsByUserID', {'userID' : userID})
			if 'result' in result and result['result']['playlists'] != None:
				playlists = result['result']['playlists']
				return self._parsePlaylists(playlists)
		else:
			return []

	# Creates a playlist with songs
	def createPlaylist(self, name, songIDs):
		result = self._callRemote('createPlaylist', {'name' : name, 'songIDs' : songIDs})
		if 'result' in result and result['result']['success'] == True: 
			return result['result']['playlistID']
		elif 'errors' in result:
			return 0

	# Sets the songs for a playlist
	def setPlaylistSongs(self, playlistID, songIDs):
		result = self._callRemote('setPlaylistSongs', {'playlistID' : playlistID, 'songIDs' : songIDs})
		if 'result' in result and result['result']['success'] == True: 
			return True
		else:
			return False

	# Gets the songs of a playlist
	def getPlaylistSongs(self, playlistID):
		result = self._callRemote('getPlaylistSongs', {'playlistID' : playlistID});
		if 'result' in result:
			return self._parseSongs(result)
		else:
			return []
		
			
	def playlistDelete(self, playlistId):
		result =  self._callRemote("deletePlaylist", {"playlistID": playlistId})
		if 'fault' in result:
			return 0
		else:
			return 1

	def playlistRename(self, playlistId, name):
		result = self._callRemote("renamePlaylist", {"playlistID": playlistId, "name": name})
		if 'fault' in result:
			return 0
		else:
			return 1
		
	def getSimilarArtists(self, artistId, limit):
		items = self._callRemote("getSimilarArtists", {"artistID": artistId, "limit": limit})
		if 'result' in items:
			i = 0
			list = []
			artists = items['result']['artists']
			while(i < len(artists)):
				s = artists[i]
				list.append([s['artistName'].encode('ascii', 'ignore'),\
				s['artistID']])
				i = i + 1
			return list
		else:
			return []		
	
	def getDoesArtistExist(self, artistId):
		response = self._callRemote("getDoesArtistExist", {"artistID": artistId})
		if 'result' in response and response['result'] == True:
			return True
		else:
			return False

	def getDoesAlbumExist(self, albumId):
		response = self._callRemote("getDoesAlbumExist", {"albumID": albumId})
		if 'result' in response and response['result'] == True:
			return True
		else:
			return False

	def getDoesSongExist(self, songId):
		response = self._callRemote("getDoesSongExist", {"songID": songId})
		if 'result' in response and response['result'] == True:
			return True
		else:
			return False
		
	# After 30s play time
	def markStreamKeyOver30Secs(self, streamKey, streamServerID):
		params = { "streamKey" : streamKey, "streamServerID" : streamServerID }
		self._callRemote("markStreamKeyOver30Secs", params)

	# Song complete
	def markSongComplete(self, songid, streamKey, streamServerID):		
		params = { "songID" : songid, "streamKey" : streamKey, "streamServerID" : streamServerID }
		self._callRemote("markSongComplete", params)
		
	# Extract song data	
	def _parseSongs(self, items, limit=0):
		if 'result' in items:
			i = 0
			list = []
			index = ''
			l = -1
			try:
				if 'songs' in items['result'][0]:
					l = len(items['result'][0]['songs'])
					index = 'songs[]'
			except: pass
			try:
				if l < 0 and 'songs' in items['result']:
					l = len(items['result']['songs'])
					index = 'songs'
			except: pass
			try:
				if l < 0 and 'song' in items['result']:
					l = 1
					index = 'song'
			except: pass
			try:
				if l < 0:
					l = len(items['result'])
			except: pass

			if limit > 0 and l > limit:
				l = limit
			while(i < l):
				if index == 'songs[]':
					s = items['result'][0]['songs'][i]
				elif index == 'songs':
					s = items['result'][index][i]
				elif index == 'song':
					s = items['result'][index]
				else:
					s = items['result'][i]
				if 'CoverArtFilename' not in s:
					info = self.getSongsInfo(s['SongID'])
					coverart = info['CoverArtFilename']
				elif s['CoverArtFilename'] != None:
					coverart = THUMB_URL+s['CoverArtFilename'].encode('ascii', 'ignore')
				else:
					coverart = 'None'
				if 'Name' in s:
					name = s['Name']
				else:
					name = s['SongName']
				list.append([name.encode('ascii', 'ignore'),\
				s['SongID'],\
				s['AlbumName'].encode('ascii', 'ignore'),\
				s['AlbumID'],\
				s['ArtistName'].encode('ascii', 'ignore'),\
				s['ArtistID'],\
				coverart])
				i = i + 1
			return list
		else:
			return []

	# Extract artist data	
	def _parseArtists(self, items):
		if 'result' in items:
			i = 0
			list = []
			artists = items['result']['artists']
			while(i < len(artists)):
				s = artists[i]
				list.append([s['ArtistName'].encode('ascii', 'ignore'),\
				s['ArtistID']])
				i = i + 1
			return list
		else:
			return []

	# Extract album data	
	def _parseAlbums(self, items, limit=0):
		if 'result' in items:
			i = 0
			list = []
			try:
				albums = items['result']['albums']
			except:
				res = items['result'][0]
				albums = res['albums']
			l = len(albums)
			if limit > 0 and l > limit:
				l = limit
			while(i < l):
				s = albums[i]
				if 'CoverArtFilename' in s and s['CoverArtFilename'] != None:
					coverart = THUMB_URL+s['CoverArtFilename'].encode('ascii', 'ignore')
				else:
					coverart = 'None'
				list.append([s['ArtistName'].encode('ascii', 'ignore'),\
				s['ArtistID'],\
				s['AlbumName'].encode('ascii', 'ignore'),\
				s['AlbumID'],\
				coverart])
				i = i + 1
			return list
		else:
			return []

	def _parsePlaylists(self, items):
		i = 0
		list = []
		if 'result' in items:
			playlists = items['result']['playlists']
		elif len(items) > 0:
			playlists = items
		else:
			return []

		while (i < len(playlists)):
			s = playlists[i]
			list.append([unicode(s['PlaylistName']).encode('utf8', 'ignore'), s['PlaylistID']])
			i = i + 1
		return list
