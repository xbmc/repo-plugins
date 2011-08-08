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

import sys, urllib
import YouTubeCore

class YouTubeFeeds(YouTubeCore.YouTubeCore):
	__settings__ = sys.modules[ "__main__" ].__settings__
	__language__ = sys.modules[ "__main__" ].__language__
	__plugin__ = sys.modules[ "__main__" ].__plugin__
	__dbg__ = sys.modules[ "__main__" ].__dbg__
	
	__storage__ = sys.modules[ "__main__" ].__storage__
		
	def __init__(self):
		# YouTube General Feeds
		self.urls['playlist'] = "http://gdata.youtube.com/feeds/api/playlists/%s"
		self.urls['related'] = "http://gdata.youtube.com/feeds/api/videos/%s/related"
		self.urls['search'] = "http://gdata.youtube.com/feeds/api/videos?q=%s&safeSearch=%s"
	
		# YouTube User specific Feeds
		self.urls['uploads'] = "http://gdata.youtube.com/feeds/api/users/%s/uploads"
		self.urls['favorites'] = "http://gdata.youtube.com/feeds/api/users/%s/favorites"
		self.urls['playlists'] = "http://gdata.youtube.com/feeds/api/users/%s/playlists"
		self.urls['contacts'] = "http://gdata.youtube.com/feeds/api/users/default/contacts"
		self.urls['subscriptions'] = "http://gdata.youtube.com/feeds/api/users/%s/subscriptions"
		self.urls['newsubscriptions'] = "http://gdata.youtube.com/feeds/api/users/%s/newsubscriptionvideos"
	
		# YouTube Standard feeds
		self.urls['feed_rated'] = "http://gdata.youtube.com/feeds/api/standardfeeds/top_rated?time=%s"
		self.urls['feed_favorites'] = "http://gdata.youtube.com/feeds/api/standardfeeds/top_favorites?time=%s"
		self.urls['feed_viewed'] = "http://gdata.youtube.com/feeds/api/standardfeeds/most_viewed?time=%s"
		self.urls['feed_linked'] = "http://gdata.youtube.com/feeds/api/standardfeeds/most_popular?time=%s" 
		self.urls['feed_discussed'] = "http://gdata.youtube.com/feeds/api/standardfeeds/most_discussed?time=%s"
		self.urls['feed_responded'] = "http://gdata.youtube.com/feeds/api/standardfeeds/most_responded?time=%s"
		self.urls['feed_live'] = "http://gdata.youtube.com/feeds/api/charts/live/events/live_now"
	
		# Wont work with time parameter
		self.urls['feed_recent'] = "http://gdata.youtube.com/feeds/api/standardfeeds/most_recent" 
		self.urls['feed_featured'] = "http://gdata.youtube.com/feeds/api/standardfeeds/recently_featured"
		self.urls['feed_trending'] = "http://gdata.youtube.com/feeds/api/standardfeeds/on_the_web"
		self.urls['feed_shared'] = "http://gdata.youtube.com/feeds/api/standardfeeds/most_shared"
	
	def createUrl(self, params = {}):
		get = params.get
		time = "this_week"
		per_page = ( 10, 15, 20, 25, 30, 40, 50 )[ int( self.__settings__.getSetting( "perpage" ) ) ]
		region = ('', 'AU', 'BR', 'CA', 'CZ', 'FR', 'DE', 'GB', 'NL', 'HK', 'IN', 'IE', 'IL', 'IT', 'JP', 'MX', 'NZ', 'PL', 'RU', 'KR', 'ES','SE', 'TW', 'US', 'ZA' )[ int( self.__settings__.getSetting( "region_id" ) ) ]
		
		page = get("page","0")
		start_index = per_page * int(page) + 1
		url = ""
		
		if (get("feed")):
			url = self.urls[get("feed")]
		
		if (get("user_feed")):
			url = self.urls[get("user_feed")]
		
		if get("search"):
			query = urllib.unquote_plus(get("search"))
			safe_search = ("none", "moderate", "strict" ) [int( self.__settings__.getSetting( "safe_search" ) ) ]	
			url = url % (query, safe_search)  
			authors = self.__settings__.getSetting("stored_searches_author")
			if len(authors) > 0:
				try:
					authors = eval(authors)
					if query in authors:
						url += "&" + urllib.urlencode({'author': authors[query]})
				except:
					print self.__plugin__ + " search - eval failed "	
			
		if (url.find("%s") > 0):
			if ( get("contact") and not (get("external") and get("channel"))):
				url = url % get("contact")
			elif ( get("channel") ):
				url = url % get("channel")
			elif ( get("playlist") ):
				url = url % get("playlist")
			elif ( get("videoid") and not get("action") == "add_to_playlist"):
				url = url % get("videoid")
			elif (url.find("time=") > 0 ): 
				url = url % time			
			else: 
				url = url % "default"
		
		if ( url.find("?") == -1 ):
			url += "?"
		else:
			url += "&"
			
		if not get("playlist") and not get("folder") and not get("action") == "play_all" and not get("action") == "add_to_playlist":
			url += "start-index=" + repr(start_index) + "&max-results=" + repr(per_page)
		
		if (url.find("standardfeeds") > 0 and region):
			url = url.replace("/standardfeeds/", "/standardfeeds/"+ region + "/")
						
		url = url.replace(" ", "+")
		return url
	
	def list(self, params = {}):
		get = params.get
		result = { "content": "", "status": 303 }
		
		if get("folder"):
			return self.listFolder(params)
		
		if get("playlist"):
			return self.listPlaylist(params)
		
		if get("login") == "true":
			if ( not self._getAuth() ):
				if self.__dbg__:
					print self.__plugin__ + " login required but auth wasn't set!"
				return ( self.__language__(30609) , 303 )

		url = self.createUrl(params)
		
		if url:
			result = self._fetchPage({"link": url, "auth": get("login"), "api": "true"})
		
		if result["status"] != 200:
			return ( result["content"], result["status"] )
		
		if not get("folder"):
			videos = self.getVideoInfo(result["content"], params)
		
		if len(videos) == 0:
			return (videos, 303)
		
		thumbnail = videos[0].get('thumbnail', "")
		
		if thumbnail:
			self.__storage__.store(params, thumbnail, "thumbnail")
						
		return (videos, 200)
	
	def listPlaylist(self, params = {}):
		get = params.get
		page = int(get("page", "0"))
		per_page = ( 10, 15, 20, 25, 30, 40, 50 )[ int( self.__settings__.getSetting( "perpage" ) ) ]
		next = 'false'
		
		videos = self.__storage__.retrieve(params)
		
		if page != 0 and videos:
			if ( per_page * ( page + 1 ) < len(videos) ):
				next = 'true'
			
			videos = videos[(per_page * page):(per_page * (page + 1))]
			
			(result, status) = self.getBatchDetailsOverride(videos, params)
		else:
			result = self.listAll(params)
				
			if len(result) == 0:
				return (result, 303)
			
			videos = []
			for video in result:
				vget = video.get
				item = {}
				item["playlist_entry_id"] = vget("playlist_entry_id")
				item["videoid"] = vget("videoid")
				videos.append(item)
			
			self.__storage__.store(params, videos)
			
			thumbnail = result[0].get('thumbnail', "")
			if (thumbnail):
				self.__storage__.store(params, thumbnail, "thumbnail")
			
			if (len(result) > 0):
				if ( per_page * ( page + 1 ) < len(result) ):
					next = 'true'
			
			result = result[(per_page * page):(per_page * (page + 1))]
		
		if next == "true":
			self.addNextFolder(result, params)
		
		return (result, 200)
	
	def listFolder(self, params = {}):
		get = params.get
		result = []
		
		if get("store"): 
			if get("store") == "contact_options":
				return self.__storage__.getUserOptionFolder(params)
			else:
				return self.__storage__.getStoredSearches(params)

		page = int(get("page", "0"))
		per_page = ( 10, 15, 20, 25, 30, 40, 50 )[ int( self.__settings__.getSetting( "perpage" ) ) ]
		
		if ( page != 0):
			result = self.__storage__.retrieve(params)
		
		elif not get("page"):
			result = self.listAll(params)
			
			if len(result) == 0:
				return (result, 303)
			
			self.__storage__.store(params, result)
		
		next = 'false'
		if (len(result) > 0):
			if ( per_page * ( page + 1 ) < len(result) ):
				next = 'true'
		
		result = result[(per_page * page):(per_page * (page + 1))]
		
		if get("user_feed") == "subscriptions":
			for item in result:
				viewmode = self.__storage__.retrieve(params, "viewmode", item)
				
				if (get("external")):
					item["external"] = "true"
					item["contact"] = get("contact")	
				
				if (viewmode == "favorites"):
					item["user_feed"] = "favorites"
					item["view_mode"] = "subscriptions_uploads"
				elif(viewmode == "playlists"):
					item["user_feed"] = "playlists"
					item["folder"] = "true"
					item["view_mode"] = "subscriptions_playlists"
				else:
					item["user_feed"] = "uploads"  
					item["view_mode"] = "subscriptions_favorites"
		
		if next == "true":
			self.addNextFolder(result, params)
		
		return (result,200)
	
	def listAll(self, params ={}):
		get = params.get
		result = { "content": "", "status": 303 }
		
		if get("login") == "true":
			if ( not self._getAuth() ):
				if self.__dbg__:
					print self.__plugin__ + " login required but auth wasn't set!"
				return ( self.__language__(30609) , 303 )
		
		feed = self.createUrl(params)
		index = 1
		url = feed + "v=2&start-index=" + str(index) + "&max-results=" + repr(50)
		url = url.replace(" ", "+")

		ytobjects = []
		
		result = self._fetchPage({"link":url, "auth":"true"})
		
		if result["status"] == 200:
			if get("folder") == "true":
				ytobjects = self.getFolderInfo(result["content"], params)
			else:
				ytobjects = self.getVideoInfo(result["content"], params)
		
		if len(ytobjects) == 0:
			return ytobjects
		
		next = ytobjects[len(ytobjects)-1].get("next","false")
		if next == "true": 
			ytobjects = ytobjects[:len(ytobjects)-1]
		
		while next == "true":
			index += 50
			url = feed + "start-index=" + str(index) + "&max-results=" + repr(50)
			url = url.replace(" ", "+")
			result = self._fetchPage({"link": url, "auth":"true"})
			
			if result["status"] != 200:
				break
			temp_objects = []
			if get("folder") == "true":
				temp_objects = self.getFolderInfo(result["content"], params)
			else:
				temp_objects = self.getVideoInfo(result["content"], params)
		
			next = temp_objects[len(temp_objects)-1].get("next","false")
			if next == "true":
				temp_objects = temp_objects[:len(temp_objects)-1]
			ytobjects += temp_objects
		
		if get("user_feed"):
			if get("user_feed") != "playlist" and get("action") != "play_all":
				ytobjects.sort(key=lambda item:item["Title"].lower(), reverse=False)
			else:
				if (self.__storage__.getReversePlaylistOrder(params)):
					ytobjects.reverse()
		
		return ytobjects
