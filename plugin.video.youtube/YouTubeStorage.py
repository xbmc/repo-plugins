'''
   YouTube plugin for XBMC
   Copyright (C) 2010-2011 Tobias Ussing And Henrik Mosgaard Jensen

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.
   
   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys, urllib, io

class YouTubeStorage():

	def __init__(self):
		self.xbmc = sys.modules["__main__"].xbmc
		self.settings = sys.modules[ "__main__" ].settings
		self.language = sys.modules[ "__main__" ].language
		self.plugin = sys.modules[ "__main__"].plugin
		self.dbg = sys.modules[ "__main__" ].dbg

		self.utils =  sys.modules[ "__main__" ].utils
		self.common = sys.modules[ "__main__" ].common
		self.cache = sys.modules[ "__main__" ].cache
					
		# This list contains the list options a user sees when indexing a contact 
		#				label					  , external		 , login		 ,	thumbnail					, feed
		self.user_options = (
					{'Title':self.language( 30020 ), 'external':"true", 'login':"true", 'thumbnail':"favorites", 	'user_feed':"favorites"},
					{'Title':self.language( 30023 ), 'external':"true", 'login':"true", 'thumbnail':"playlists", 	'user_feed':"playlists", 'folder':"true"},
					{'Title':self.language( 30021 ), 'external':"true", 'login':"true", 'thumbnail':"subscriptions", 'user_feed':"subscriptions", 'folder':"true"},
					{'Title':self.language( 30022 ), 'external':"true", 'login':"true", 'thumbnail':"uploads", 		'user_feed':"uploads"},
					)
	
	def list(self, params = {}):
		get = params.get
		if get("store") == "contact_options":
			return self.getUserOptionFolder(params)
		elif get("store") == "artists":
			return self.getStoredArtists(params)
		elif get("store"):
			return self.getStoredSearches(params)
	
	def openFile(self, filepath, options = "w"):
		try:
			return io.open(filepath, options)
		except:
			return io.open(filepath, options + "b")
	
	def getStoredArtists(self, params = {}):
		get = params.get
		self.common.log("")
		
		artists = self.retrieve(params)
		
		result = []
		for title, artist in artists:
			item = {}
			item["path"] = get("path")
			item["Title"] = urllib.unquote_plus(title)
			item["artist"] = artist
			item["scraper"] = "music_artist"
			item["icon"] = "music" 
			item["thumbnail"] = "music"
			thumbnail = self.retrieve(params, "thumbnail", item)
			
			if thumbnail:
				item["thumbnail"] = thumbnail	
			
			result.append(item)
				
		return (result, 200)
	
	def deleteStoredArtist(self, params = {}):
		get = params.get
		self.common.log("")

		artist = get("artist")
		artists = self.retrieve(params)
		
		for count, (title, artist_id) in enumerate(artists):
			if (artist == artist_id):
				del(artists[count])
				break
		
		self.store(params, artists)
		
		self.xbmc.executebuiltin( "Container.Refresh" )
		
	def saveStoredArtist(self, params = {}):
		get = params.get
		self.common.log("")
		
		if get("artist") and get("artist_name"):
			params["store"] = "artists"
			artists = self.retrieve(params)
			searchCount = ( 10, 20, 30, 40, )[ int( self.settings.getSetting( "saved_searches" ) ) ] - 1
			artists = [(get("artist_name"), get("artist"))] + artists[:searchCount]
			self.store(params, artists)
			del params["store"]
		
	def getStoredSearches(self, params = {}):
		get = params.get
		self.common.log("")
		
		searches = self.retrieve(params)
				
		result = []
		for search in searches:
			item = {}
			item["path"] = get("path")
			item["Title"] = search
			item["search"] = urllib.quote_plus(search)
			
			if (get("store") == "searches"):
				item["feed"] = "search"
				item["icon"] = "search" 
			elif get("store") == "disco_searches":
				item["scraper"] = "search_disco" 
				item["icon"] = "discoball"
			
			thumbnail = self.retrieve(params, "thumbnail", item)
			if thumbnail:
				item["thumbnail"] = thumbnail
			else: 
				item["thumbnail"] = item["icon"] 
			result.append(item)
				
		return (result, 200)
			
	def deleteStoredSearch(self, params = {}):
		get = params.get
		self.common.log("")
		
		query = urllib.unquote_plus(get("delete"))		
		searches = self.retrieve(params)
		
		for count, search in enumerate(searches):
			if (search.lower() == query.lower()):
				del(searches[count])
				break
		
		self.store(params, searches)
		
		self.xbmc.executebuiltin( "Container.Refresh" )
	
	def saveStoredSearch(self, params = {}):
		get = params.get
		self.common.log("")
		
		if get("search"):
			searches = self.retrieve(params)
			
			new_query = urllib.unquote_plus(get("search"))
			old_query = new_query
			
			if get("old_search"):
				old_query = urllib.unquote_plus(get("old_search"))
			
			for count, search in enumerate(searches):
				if (search.lower() == old_query.lower()):
					del(searches[count])
					break
			
			searchCount = ( 10, 20, 30, 40, )[ int( self.settings.getSetting( "saved_searches" ) ) ] - 1
			searches = [new_query] + searches[:searchCount]
			self.store(params, searches)
	
	def editStoredSearch(self, params = {}):
		get = params.get
		self.common.log("")


		if (get("search")):
			old_query = urllib.unquote_plus(get("search"))
			new_query = self.utils.getUserInput(self.language(30515), old_query)
			params["search"] = new_query
			params["old_search"] = old_query
			
			if get("action") == "edit_disco":
				params["scraper"] = "search_disco"
				params["store"] = "disco_searches"
			else:
				params["store"] = "searches"
				params["feed"] = "search"
			
			self.saveStoredSearch(params)

			params["search"] = urllib.quote_plus(new_query)
			del params["old_search"]
		
		if get("action"):
			del params["action"]
		if get("store"):
			del params["store"]
		
	def getUserOptionFolder(self, params = {}):
		get = params.get
		self.common.log("")
		
		result = []
		for item in self.user_options:
			item["path"] = get("path")
			item["contact"] = get("contact")
			result.append(item)
		
		return (result, 200)
	
	def changeSubscriptionView(self, params = {}):
		get = params.get
		self.common.log("")
	
		if (get("view_mode")):  
			key = self.getStorageKey(params, "viewmode")
			
			self.storeValue(key, get("view_mode"))
			
			params['user_feed'] = get("view_mode")
			if get("viewmode") == "playlists":
				params["folder"] = "true" # No result
	
	def reversePlaylistOrder(self, params = {}):
		get = params.get
		self.common.log("")
		
		if (get("playlist")):			
			value = "true"
			existing = self.retrieve(params, "value")
			if existing == "true":
				value = "false" # No result
			
			self.store(params, value, "value")
		
			self.xbmc.executebuiltin( "Container.Refresh" )
		
	def getReversePlaylistOrder(self, params = {}):
		get = params.get 
		self.common.log("")
		
		result = False
		if (get("playlist")):
			existing = self.retrieve(params, "value")
			if existing == "true":
				result = True
		
		return result
	
	#=================================== Storage Key ========================================
	def getStorageKey(self, params = {}, type = "", item = {}):
		get = params.get
		
		if type == "value":
			return self._getValueStorageKey(params, item)
		elif type == "viewmode":
			return self._getViewModeStorageKey(params, item)
		elif type == "thumbnail":
			return self._getThumbnailStorageKey(params, item)
		
		return self._getResultSetStorageKey(params)
		
	def _getThumbnailStorageKey(self, params = {}, item = {}):
		get = params.get
		iget = item.get
		key = ""
		
		if get("search") or iget("search"):
			key = "disco_search_"
			if get("feed") or iget("feed"):
				key = "search_"
			
			if get("store") == "searches":
				key = "search_"
			
			if get("search"):
				key += urllib.unquote_plus(get("search",""))
			
			if iget("search"):
				key += urllib.unquote_plus(iget("search",""))
		
		if get("artist") or iget("artist"):
			key = "artist_"
			
			if get("artist"):
				key += get("artist")
			
			if iget("artist"):
				key += iget("artist")
			
		if get("user_feed"):
			key = get("user_feed")
			
			if get("channel"):
				key = "subscriptions_" + get("channel")

			if iget("channel"):
				key = "subscriptions_" + iget("channel")
		
			if get("playlist"):
				key = "playlist_" + get("playlist")
			
			if iget("playlist"):
				key = "playlist_" + iget("playlist")
			
		if key:
			key += "_thumb"
		
		return key
	
	def _getValueStorageKey(self, params = {}, item = {}):
		get = params.get
		iget = item.get
		key = ""
		
		if ((get("action") == "reverse_order" or get("user_feed") == "playlist") and (iget("playlist") or get("playlist"))):
			
			key = "reverse_playlist_" 
			if iget("playlist"):
				key += iget("playlist")
			
			if get("playlist"):
				key += get("playlist")
				
			if (get("external")):
				key += "_external_" + get("contact")
		
		return key 
	
	def _getViewModeStorageKey(self, params = {}, item = {}):
		get = params.get
		iget = item.get
		key = ""
				
		if (get("external")):
			key = "external_" + get("contact") + "_"
		elif (iget("external")):
			key = "external_" + iget("contact") + "_"
					
		if get("channel"):
			key += "view_mode_" + get("channel")
		elif (iget("channel")):  
			key += "view_mode_" + iget("channel")
		
		return key
	
	def _getResultSetStorageKey(self, params = {}):
		get = params.get
		
		key = ""
		
		if get("scraper"):
			key = "s_" + get("scraper")
						
			if get("scraper") == "music_artist" and get("artist"):
				key += "_" + get("artist")
			
			if get("scraper") == "disco_search":
				key = "store_disco_searches"
			
			if get("category"):
				key += "_category_" + get("category")
			
			if get("show"):
				key += "_" + get("show")
				key += "_season_" + get("season","0")
		
		if get("user_feed"):
			key = "result_" + get("user_feed")
			
			if get("playlist"):
				key += "_" + get("playlist")
			
			if get("channel"):
				key += "_" + get("channel")
			
			if get("external") and not get("thumb"):
				key += "_external_" + get("contact")
		
		if get("feed") == "search":
			key = "store_searches"
		
		if get("store"):
			key = "store_"+ get("store")
		
		return key
	
	#============================= Storage Functions =================================
	def store(self, params = {}, results = [], type = "", item = {}):
		key = self.getStorageKey(params, type, item)
		
		self.common.log("Got key " + repr(key))
		
		if type == "thumbnail" or type == "viewmode" or type == "value":
			self.storeValue(key, results)
		else:
			self.storeResultSet(key, results)
	
	def storeValue(self, key, value):
		if value:
			self.cache.set(key, value)

	def storeResultSet(self, key, results = [], params = {}):
		get = params.get
		
		if results:
			if get("prepend"):
				searchCount = ( 10, 20, 30, 40, )[ int( self.settings.getSetting( "saved_searches" ) ) ]
				existing = self.retrieveResultSet(key)
				existing = [results] + existing[:searchCount]
				self.cache.set(key, repr(existing))
			elif get("append"):
				existing = self.retrieveResultSet(key)  
				existing.append(results)
				self.cache.set(key, repr(existing))
			else:
				value = repr(results)
				self.cache.set(key,value)
	
	#============================= Retrieval Functions =================================
	def retrieve(self, params = {}, type = "", item = {}):
		key = self.getStorageKey(params, type, item)
		
		self.common.log("Got key " + repr(key))
		
		if type == "thumbnail" or type == "viewmode" or type == "value":
			return self.retrieveValue(key)
		else:
			return self.retrieveResultSet(key)

	def retrieveValue(self, key):
		value = ""
		if key:
			value = self.cache.get(key)
		
		return value
	
	def retrieveResultSet(self, key):
		results = []
		
		value = self.cache.get(key)		
		if value: 
			try:
				results = eval(value)
			except:
				results = []
		
		return results
		
	#============================= Download Queue =================================
	def getNextVideoFromDownloadQueue(self):
		if self.cache.lock("YouTubeQueueLock"):
			videos = []
			
			queue = self.cache.get("YouTubeDownloadQueue")
			self.common.log("queue loaded : " + repr(queue))
			
			if queue:
				try:
					videos = eval(queue)
				except: 
					videos = []
		
			videoid = ""
			if videos:
				videoid = videos[0]

			self.cache.unlock("YouTubeQueueLock")
			self.common.log("getNextVideoFromDownloadQueue released. returning : " + videoid)
			return videoid
		else:
			self.common.log("getNextVideoFromDownloadQueue Exception")

	def addVideoToDownloadQueue(self, params = {}):
		if self.cache.lock("YouTubeQueueLock"):
			get = params.get

			videos = []
			if get("videoid"):
				queue = self.cache.get("YouTubeDownloadQueue")
				self.common.log("queue loaded : " + repr(queue))

				if queue:
					try:
						videos = eval(queue)
					except:
						videos = []
		
				if get("videoid") not in videos:
					videos.append(get("videoid"))
					
					self.cache.set("YouTubeDownloadQueue", repr(videos))
					self.common.log("Added: " + get("videoid") + " to: " + repr(videos))

			self.cache.unlock("YouTubeQueueLock")
			self.common.log("addVideoToDownloadQueue released")
		else:
			self.common.log("addVideoToDownloadQueue Exception")
		
	def removeVideoFromDownloadQueue(self, videoid):
		if self.cache.lock("YouTubeQueueLock"):
			videos = []
			
			queue = self.cache.get("YouTubeDownloadQueue")
			self.common.log("queue loaded : " + repr(queue))
			if queue:
				try:
					videos = eval(queue)
				except:
					videos = []
		
			if videoid in videos:
				videos.remove(videoid)

				self.cache.set("YouTubeDownloadQueue", repr(videos))
				self.common.log("Removed: " + videoid + " from: " + repr(videos))
			else:
				self.common.log("Didn't remove: " + videoid + " from: " + repr(videos))

			self.cache.unlock("YouTubeQueueLock")
			self.common.log("removeVideoFromDownloadQueue released")
		else:
			self.common.log("removeVideoFromDownloadQueue Exception")
