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

import sys, urllib, os
import xbmc
from filelock import FileLock
	
class YouTubeStorage:
	__settings__ = sys.modules[ "__main__"].__settings__ 
	__plugin__ = sys.modules[ "__main__"].__plugin__
	__language__ = sys.modules[ "__main__" ].__language__
	
	__utils__ = sys.modules[ "__main__" ].__utils__
	__lock__ = FileLock(os.path.join( xbmc.translatePath( "special://temp" ), "YouTubeDownloadQueue.lock"), 10)
	
	# This list contains the list options a user sees when indexing a contact 
	#				label					  , external		 , login		 ,	thumbnail					, feed
	user_options = (
				{'Title':__language__( 30020 ), 'external':"true", 'login':"true", 'thumbnail':"favorites", 	'user_feed':"favorites"},
				{'Title':__language__( 30023 ), 'external':"true", 'login':"true", 'thumbnail':"playlists", 	'user_feed':"playlists", 'folder':"true"},
				{'Title':__language__( 30021 ), 'external':"true", 'login':"true", 'thumbnail':"subscriptions", 'user_feed':"subscriptions", 'folder':"true"},
				{'Title':__language__( 30022 ), 'external':"true", 'login':"true", 'thumbnail':"uploads", 		'user_feed':"uploads"},
				)

	def getStoredSearches(self, params = {}):
		get = params.get
		try:
			if (get("store") == "searches"):
				searches = eval(self.__settings__.getSetting("stored_searches"))
			else:
				searches = eval(self.__settings__.getSetting("stored_disco_searches"))
		except:
			searches = []
		
		result = []
		for search in searches:
			item = {}
			item["path"] = get("path")
			item["Title"] = search
			item["search"] = urllib.quote_plus(search)
			
			if (get("store") == "searches"):
				item["feed"] = "search"
				item["icon"] = "search"
				item["thumbnail"] = self.__settings__.getSetting("search_" + search + "_thumb")
			else:
				item["scraper"] = "search_disco"
				item["icon"] = "discoball"
				item["thumbnail"] = self.__settings__.getSetting("disco_search_" + search + "_thumb")
			
			result.append(item)
				
		return (result, 200)
						
	def deleteStoredSearch(self, params = {}):
		get = params.get
		query = get("delete")
		query = urllib.unquote_plus(query)
		try:
			if (get("action") == "delete_search"):
				searches = eval(self.__settings__.getSetting("stored_searches"))
			else:
				searches = eval(self.__settings__.getSetting("stored_disco_searches"))
		except:
			searches = []
			
		for count, search in enumerate(searches):
			if (search.lower() == query.lower()):
				del(searches[count])
				break
		
		if (get("action") == "delete_search"):
			self.__settings__.setSetting("stored_searches", repr(searches))
		else:
			self.__settings__.setSetting("stored_disco_searches", repr(searches))
		
		xbmc.executebuiltin( "Container.Refresh" )
		
	def saveSearch(self, params = {}):
		get = params.get
		
		if get("search"):
			key = self.getStorageKey(params)
			searches = []
			
			new_query = urllib.unquote_plus(get("search"))
			old_query = new_query
			
			if get("old_search"):
				old_query = urllib.unquote_plus(get("old_search"))
			
			try:
				searches = eval(self.retrieveValue(key))
			except:
				searches = []
			
			for count, search in enumerate(searches):
				if (search.lower() == old_query.lower()):
					del(searches[count])
					break
			
			searchCount = ( 10, 20, 30, 40, )[ int( self.__settings__.getSetting( "saved_searches" ) ) ]
			searches = [new_query] + searches[:searchCount]
			self.storeValue(key, repr(searches))
	
	def editStoredSearch(self, params = {}):
		get = params.get
		if (get("search")):
			old_query = urllib.unquote_plus(get("search"))
			new_query = self.__utils__.getUserInput(self.__language__(30515), old_query)
			params["search"] = new_query
			params["old_search"] = old_query
			
			if (get("action") == "edit_search"):
				params["store"] = "searches"
				self.saveSearch(params)
				params["feed"] = "search"
			else:
				params["store"] = "disco_searches"
				self.saveSearch(params)
				params["scraper"] = "search_disco"
			
			params["search"] = urllib.quote_plus(new_query)
		
		del params["old_search"]
		del params["store"]
		del params["action"]
	
	def refineStoredSearch(self, params = {}):
		get = params.get
		query = get("search")
		query = urllib.unquote_plus(query)
		
		try:
			searches = eval(self.__settings__.getSetting("stored_searches_author"))
		except :
			searches = {}
			
		if query in searches:
			author = self.__utils__.getUserInput(self.__language__(30517), searches[query])
		else:
			author = self.__utils__.getUserInput(self.__language__(30517), '')

		if author == "":
			if author in searches:
				del searches[query]
				xbmc.executebuiltin( "Container.Refresh" )
		elif author:
			searches[query] = author
			
			self.__settings__.setSetting("stored_searches_author", repr(searches))
			self.__utils__.showMessage(self.__language__(30006), self.__language__(30616))
			xbmc.executebuiltin( "Container.Refresh" )
		
	def deleteStoredSearchRefinement(self, params = {}):
		get = params.get
		query = get("search")
		query = urllib.unquote_plus(query)
		try:
			searches = eval(self.__settings__.getSetting("stored_searches_author"))
		except :
			searches = {}
			
		if query in searches:
			del searches[query]
			self.__settings__.setSetting("stored_searches_author", repr(searches))
			self.__utils__.showMessage(self.__language__(30006), self.__language__(30610))
			xbmc.executebuiltin( "Container.Refresh" )
		
	def getUserOptionFolder(self, params = {}):
		get = params.get
		result = []
		for item in self.user_options:
			item["path"] = get("path")
			item["contact"] = get("contact")
			result.append(item)
		
		return (result, 200)
	
	def changeSubscriptionView(self, params = {}):
		get = params.get
		
		if (get("view_mode")):  
			key = ""
			if (get("external")):
				key += "external_" + get("contact") + "_"
			key += "view_mode_" + get("channel")
			
			self.storeValue(key, get("view_mode"))

			params['user_feed'] = get("view_mode")
			if get("viewmode") == "playlists":
				params["folder"] = "true"
	
	def reversePlaylistOrder(self, params = {}):
		get = params.get
		
		if (get("playlist")):
			key = "reverse_playlist_" + get("playlist")
			if (get("external")):
				key += "_external_" + get("contact") 
			
			value = "true"
			existing = self.retrieveValue(key)
			if existing == "true":
				value = "false"
						
			self.storeValue(key, value)
		
		xbmc.executebuiltin( "Container.Refresh" )
		
	def getReversePlaylistOrder(self, params = {}):
		get = params.get 
		result = False
		if (get("playlist")):
			key = "reverse_playlist_" + get("playlist")
			if (get("external")):
				key += "_external_" + get("contact") 
			
			existing = self.retrieveValue(key)
			if existing == "true":
				result = True
		
		return result
	
	def addVideoToDownloadQeueu(self, params = {}):
		try:
			print self.__plugin__ + " addVideoToDownloadQeueu trying to acquire"
			self.__lock__.acquire()
		except:
			print self.__plugin__ + " addVideoToDownloadQeueu Exception "
		else:
			get = params.get

			videos = []
			if get("videoid"):			
				#queue = self.__settings__.getSetting("download_queue")
				fd = os.open(os.path.join( xbmc.translatePath( "special://temp" ), "YouTubeDownloadQueue"), os.O_RDWR | os.O_CREAT)
				queue = os.read(fd, 65535)	
				os.close(fd)
				print self.__plugin__ + " qeueu loaded : " + repr(queue)

				if queue:
					try:
						videos = eval(queue)
					except:
						videos = []
		
				if get("videoid") not in videos:
					videos.append(get("videoid"))
			
					#self.__settings__.setSetting("download_queue",repr(videos))

					os.unlink(os.path.join( xbmc.translatePath( "special://temp" ), "YouTubeDownloadQueue"))
					fd = os.open(os.path.join( xbmc.translatePath( "special://temp" ), "YouTubeDownloadQueue"), os.O_RDWR | os.O_CREAT)
					os.write(fd, repr(videos))
					os.close(fd)
					print self.__plugin__ + " Added: " + get("videoid") + " to: " + repr(videos)

			self.__lock__.release()
			print self.__plugin__ + " addVideoToDownloadQeueu released"
		
	def removeVideoFromDownloadQueue(self, videoid):
		try:
			print self.__plugin__ + " removeVideoFromDownloadQueue trying to acquire"
			self.__lock__.acquire()
		except:
			print self.__plugin__ + " removeVideoFromDownloadQueue Exception "
		else:
			videos = []
			#queue = self.__settings__.getSetting("download_queue")
			fd = os.open(os.path.join( xbmc.translatePath( "special://temp" ), "YouTubeDownloadQueue"), os.O_RDWR | os.O_CREAT)
			queue = os.read(fd, 65535)
			os.close(fd)
			print self.__plugin__ + " qeueu loaded : " + repr(queue)
			if queue:
				try:
					videos = eval(queue)
				except:
					videos = []
		
			if videoid in videos:
				videos.remove(videoid)
				#self.__settings__.setSetting("download_queue",repr(videos))
				os.unlink(os.path.join( xbmc.translatePath( "special://temp" ), "YouTubeDownloadQueue"))
				fd = os.open(os.path.join( xbmc.translatePath( "special://temp" ), "YouTubeDownloadQueue"), os.O_RDWR | os.O_CREAT)
				os.write(fd, repr(videos))
				os.close(fd)
				print self.__plugin__ + " Removed: " + videoid + " from: " + repr(videos)
			else:
				print self.__plugin__ + " Didn't remove: " + videoid + " from: " + repr(videos)

			self.__lock__.release()
			print self.__plugin__ + " removeVideoFromDownloadQueue released"
		
	def store(self, params = {}, results = []):
		key = self.getStorageKey(params)				
		self.storeResultSet(key, results)
		
	def retrieve(self, params = {}):
		key = self.getStorageKey(params)
		return self.retrieveResultSet(key)
	
	def getStorageKey(self, params):
		get = params.get
		key = ""
		
		if get("scraper"):
			key = "s_" + get("scraper")
		
		if get("scraper") == "music_hits" and get("category"):
			key += "_" + get("category")
		
		if get("scraper") == "music_artist" and get("artist"):
			key += "_" + get("artist")
		
		if get("scraper") == "search_disco":
			if get("query"):
				key = "disco_search_%s" % urllib.unquote_plus(get("search"))
				
		if get("user_feed"):
			key = "result_" + get("user_feed")
			
			if get("playlist"):
				key += "_" + get("playlist")
			
			if get("channel"):
				key += "_" + get("channel")
			
			if get("external") and not get("thumb"):
				key += "_external_" + get("contact")
		
		if get("thumb"):
			key += "_thumb"
			params["thumb"] = ""
		
		return key
	
	def storeResultSet(self, key, results = []):
		if results:
			value = repr(results)
			self.__settings__.setSetting(key,value)
	
	def retrieveResultSet(self, key):
		results = []
		
		value = self.__settings__.getSetting(key)		
		if value: 
			try:
				results = eval(value)
			except:
				results = []
		
		return results
		
	def storeValue(self, key, value):
		if value:
			self.__settings__.setSetting(key, value)
		
	def retrieveValue(self, key):
		value = ""
		if key:
			value = self.__settings__.getSetting(key)
		
		return value
		
	def getNextVideoFromDownloadQueue(self):
		try:
			print self.__plugin__ + " getNextVideoFromDownloadQueue trying to acquire"
			self.__lock__.acquire()
		except:
			print self.__plugin__ + " getNextVideoFromDownloadQueue Exception "
		else:
			videos = []
			
			fd = os.open(os.path.join( xbmc.translatePath( "special://temp" ), "YouTubeDownloadQueue"), os.O_RDWR | os.O_CREAT)
			queue = os.read(fd, 65535)
			os.close(fd)
			print self.__plugin__ + " qeueu loaded : " + repr(queue)

			if queue:
				try:
					videos = eval(queue)
				except: 
					videos = []
		
			videoid = ""
			if videos:
				videoid = videos[0]

			self.__lock__.release()
			print self.__plugin__ + " getNextVideoFromDownloadQueue released. returning : " + videoid
			return videoid

	def addNextFolder(self, items = [], params = {}):
		get = params.get
		item = {"Title":self.__language__( 30509 ), "thumbnail":"next", "next":"true", "page":str(int(get("page", "0")) + 1)} 
		for k, v in params.items():
			if (k != "thumbnail" and k != "Title" and k != "page"):
				item[k] = v
		items.append(item)
