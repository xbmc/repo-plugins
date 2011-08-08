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
import xbmc, xbmcgui, xbmcplugin
import YouTubeUtils
	
class YouTubeNavigation(YouTubeUtils.YouTubeUtils): 
	__settings__ = sys.modules[ "__main__" ].__settings__
	__plugin__ = sys.modules[ "__main__"].__plugin__	
	__language__ = sys.modules[ "__main__" ].__language__
	__dbg__ = sys.modules[ "__main__" ].__dbg__
	
	__playlist__ = sys.modules[ "__main__" ].__playlist__
	__login__ = sys.modules[ "__main__" ].__login__
	__feeds__ = sys.modules[ "__main__" ].__feeds__
	__player__ = sys.modules[ "__main__" ].__player__
	__downloader__ = sys.modules[ "__main__" ].__downloader__
	__storage__ = sys.modules[ "__main__" ].__storage__
	__scraper__ = sys.modules[ "__main__" ].__scraper__
	
	# This list contains the main menu structure the user first encounters when running the plugin
	#			   label						  , path									        , thumbnail					  		,  login		  ,  feed / action
	categories = (
				  {'Title':__language__( 30044 )  ,'path':"/root/explore"			 				, 'thumbnail':"explore"				, 'login':"false" },
				  {'Title':__language__( 30041 )  ,'path':"/root/explore/categories"				, 'thumbnail':"explore"				, 'login':"false" , 'scraper':'categories', 'folder':'true'},
				  {'Title':__language__( 30037 )  ,'path':"/root/explore/disco"						, 'thumbnail':"discoball"		 	, 'login':"false" , 'store':"disco_searches", 'folder':'true' },
				  {'Title':__language__( 30040 )  ,'path':"/root/explore/disco/new"					, 'thumbnail':"search"		   		, 'login':"false" , 'scraper':"search_disco"},
				  {'Title':__language__( 30055 )  ,'path':"/root/explore/disco/top100"				, 'thumbnail':"discoball"		 	, 'login':"false" , 'scraper':"music_top100"},
				  {'Title':__language__( 30039 )  ,'path':"/root/explore/disco/popular"				, 'thumbnail':"discoball"		 	, 'login':"false" , 'scraper':"disco_top_artist", 'folder':'true'},
				  {'Title':__language__( 30001 )  ,'path':"/root/explore/feeds"						, 'thumbnail':"feeds"			 	, 'login':"false" },
				  {'Title':__language__( 30009 )  ,'path':"/root/explore/feeds/discussed"			, 'thumbnail':"most"			 	, 'login':"false" , 'feed':"feed_discussed" },
				  {'Title':__language__( 30010 )  ,'path':"/root/explore/feeds/linked"				, 'thumbnail':"most"			 	, 'login':"false" , 'feed':"feed_linked" },
				  {'Title':__language__( 30011 )  ,'path':"/root/explore/feeds/viewed"				, 'thumbnail':"most"			 	, 'login':"false" , 'feed':"feed_viewed" },
				  {'Title':__language__( 30012 )  ,'path':"/root/explore/feeds/recent"				, 'thumbnail':"most"			 	, 'login':"false" , 'feed':"feed_recent" },
				  {'Title':__language__( 30013 )  ,'path':"/root/explore/feeds/responded"			, 'thumbnail':"most"			 	, 'login':"false" , 'feed':"feed_responded" },
				  {'Title':__language__( 30050 )  ,'path':"/root/explore/feeds/shared"				, 'thumbnail':"most"				, 'login':"false" , 'feed':"feed_shared" },
				  {'Title':__language__( 30014 )  ,'path':"/root/explore/feeds/featured"			, 'thumbnail':"featured"		 	, 'login':"false" , 'feed':"feed_featured" },
				  {'Title':__language__( 30049 )  ,'path':"/root/explore/feeds/trending"			, 'thumbnail':"featured"			, 'login':"false" , 'feed':"feed_trending" },
				  {'Title':__language__( 30015 )  ,'path':"/root/explore/feeds/favorites"			, 'thumbnail':"top"					, 'login':"false" , 'feed':"feed_favorites" },
				  {'Title':__language__( 30016 )  ,'path':"/root/explore/feeds/rated"				, 'thumbnail':"top"					, 'login':"false" , 'feed':"feed_rated" },
				  {'Title':__language__( 30043 )  ,'path':"/root/explore/movies"					, 'thumbnail':"movies"				, 'login':"false" , 'scraper':'movies', 'folder':'true'},
				  {'Title':__language__( 30052 )  ,'path':"/root/explore/music"						, 'thumbnail':"music"				, 'login':"false" , 'store':"artists", "folder":"true" },
				  {'Title':__language__( 30053 )  ,'path':"/root/explore/music/hits"				, 'thumbnail':"music"				, 'login':"false" , 'scraper':'music_hits', "folder":"true"},
				  {'Title':__language__( 30054 )  ,'path':"/root/explore/music/artists"				, 'thumbnail':"music"				, 'login':"false" , 'scraper':'music_artists', "folder":"true" },
				  {'Title':__language__( 30055 )  ,'path':"/root/explore/music/top100"				, 'thumbnail':"music"				, 'login':"false" , 'scraper':'music_top100'},
				  {'Title':__language__( 30042 )  ,'path':"/root/explore/shows"						, 'thumbnail':"shows"				, 'login':"false" , 'scraper':'shows', 'folder':'true'},
				  {'Title':__language__( 30032 )  ,'path':"/root/explore/trailers"					, 'thumbnail':"trailers"			, 'login':"false" },
				  {'Title':__language__( 30035 )  ,'path':"/root/explore/trailers/latest"   		, 'thumbnail':"trailers"			, 'login':"false" , 'scraper':"latest_trailers" },
				  {'Title':__language__( 30034 )  ,'path':"/root/explore/trailers/current"  		, 'thumbnail':"trailers"			, 'login':"false" , 'scraper':"current_trailers" },
				  {'Title':__language__( 30036 )  ,'path':"/root/explore/trailers/upcoming" 		, 'thumbnail':"trailers"			, 'login':"false" , 'scraper':"upcoming_trailers" },
				  {'Title':__language__( 30033 )  ,'path':"/root/explore/trailers/popular"  		, 'thumbnail':"trailers"			, 'login':"false" , 'scraper':"popular_trailers" },
				  {'Title':__language__( 30047 )  ,'path':"/root/explore/trailers/latest_game"  	, 'thumbnail':"trailers"			, 'login':"false" , 'scraper':"latest_game_trailers" },
				  {'Title':__language__( 30048 )  ,'path':"/root/explore/trailers/upcoming_game"  	, 'thumbnail':"trailers"			, 'login':"false" , 'scraper':"upcoming_game_trailers" },
				  {'Title':__language__( 30046 )  ,'path':"/root/explore/trailers/popular_game"  	, 'thumbnail':"trailers"			, 'login':"false" , 'scraper':"popular_game_trailers" },
				  {'Title':__language__( 30051 )  ,'path':"/root/explore/live"  					, 'thumbnail':"live"				, 'login':"false" , 'feed':"feed_live" },
				  {'Title':__language__( 30019 )  ,'path':"/root/recommended"						, 'thumbnail':"recommended"			, 'login':"true"  , 'scraper':"recommended" },
				  {'Title':__language__( 30008 )  ,'path':"/root/watch_later"						, 'thumbnail':"watch_later"			, 'login':"true"  , 'scraper':"watch_later" },
				  {'Title':__language__( 30056 )  ,'path':"/root/liked"								, 'thumbnail':"liked"				, 'login':"true"  , 'scraper':"liked_videos" },
				  {'Title':__language__( 30018 )  ,'path':"/root/contacts"			  				, 'thumbnail':"contacts"			, 'login':"true"  , 'user_feed':"contacts", 'folder':'true' },
				  {'Title':__language__( 30024 )  ,'path':"/root/contacts/new"						, 'thumbnail':"contacts"			, 'login':"true"  , 'action':"add_contact"},
				  {'Title':__language__( 30002 )  ,'path':"/root/favorites"		 					, 'thumbnail':"favorites"			, 'login':"true"  , 'user_feed':"favorites" },
				  {'Title':__language__( 30017 )  ,'path':"/root/playlists"		 					, 'thumbnail':"playlists"			, 'login':"true"  , 'user_feed':"playlists", 'folder':'true' },
				  {'Title':__language__( 30003 )  ,'path':"/root/subscriptions"	 					, 'thumbnail':"subscriptions"		, 'login':"true"  , 'user_feed':"subscriptions", 'folder':'true' },
				  {'Title':__language__( 30004 )  ,'path':"/root/subscriptions/new" 				, 'thumbnail':"newsubscriptions"	, 'login':"true"  , 'user_feed':"newsubscriptions" },
				  {'Title':__language__( 30005 )  ,'path':"/root/uploads"							, 'thumbnail':"uploads"				, 'login':"true"  , 'user_feed':"uploads" },
				  {'Title':__language__( 30045 )  ,'path':"/root/downloads"							, 'thumbnail':"downloads"			, 'login':"false" , 'feed':"downloads" },
				  {'Title':__language__( 30006 )  ,'path':"/root/search"							, 'thumbnail':"search"				, 'login':"false" , 'store':"searches", 'folder':'true' },
				  {'Title':__language__( 30007 )  ,'path':"/root/search/new"						, 'thumbnail':"search"				, 'login':"false" , 'feed':"search" },				  
				  {'Title':__language__( 30027 )  ,'path':"/root/login"			 					, 'thumbnail':"login"				, 'login':"false" , 'action':"settings" },
				  {'Title':__language__( 30028 )  ,'path':"/root/settings"		  					, 'thumbnail':"settings"			, 'login':"true"  , 'action':"settings" }
				  )
	
	#==================================== Main Entry Points===========================================
	def listMenu(self, params = {}):
		get = params.get
		cache = True
		
		path = get("path", "/root")
		if not get("feed") == "search" and not get("feed") == "related" and not get("channel") and not get("contact") and not get("playlist") and get("page","0") == "0" and not get("scraper") == "search_disco" and not get("scraper") == "music_artist":
			for category in self.categories:
				cat_get = category.get 
				if (cat_get("path").find(path +"/") > -1 ):
					if (cat_get("path").rfind("/") <= len(path +"/")):
						setting = self.__settings__.getSetting( cat_get("path").replace("/root/explore/","").replace("/root/", "") )
						
						if not setting or setting == "true":
							if (get("feed") == "downloads"):
								if (self.__settings__.getSetting("downloadPath")):
									self.addListItem(params, category)
							else:
								self.addListItem(params, category)
				
		if (get("feed") or get("user_feed") or get("options") or get("store") or get("scraper")):
			return self.list(params)
				
		video_view = self.__settings__.getSetting("list_view") == "1"
		
		if (get("scraper") == "shows" and get("category") and not video_view):
			video_view = self.__settings__.getSetting("list_view") == "0"
			
		if (video_view):
			xbmc.executebuiltin("Container.SetViewMode(500)")
		
		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True, cacheToDisc=cache )

	def executeAction(self, params = {}):
		get = params.get
		if (get("action") == "settings"):
			self.__login__.login(params)
		if (get("action") == "test"):
			self.__downloader__.test(params)
		if (get("action") in ["delete_search", "delete_disco"]):
			self.__storage__.deleteStoredSearch(params)
		if (get("action") in ["edit_search", "edit_disco"]):
			self.__storage__.editStoredSearch(params)
			self.listMenu(params)
		if (get("action") == "delete_artist"):
			self.__storage__.deleteStoredArtist(params)
		if (get("action") == "remove_favorite"):
			self.removeFromFavorites(params)
		if (get("action") == "add_favorite"):
			self.addToFavorites(params)
		if (get("action") == "remove_contact"):
			self.removeContact(params)
		if (get("action") == "add_contact"):
			self.addContact(params)
		if (get("action") == "remove_subscription"):
			self.removeSubscription(params)
		if (get("action") == "add_subscription"):
			self.addSubscription(params)
		if (get("action") == "download"):
			self.__downloader__.downloadVideo(params)
		if (get("action") == "play_video"):
			self.__player__.playVideo(params)
		if (get("action") == "queue_video"):
			self.__playlist__.queueVideo(params)
		if (get("action") == "change_subscription_view"):
			self.__storage__.changeSubscriptionView(params)
			self.list(params)
		if (get("action") == "play_all"):
			self.__playlist__.playAll(params)
		if (get("action") == "add_to_playlist"):
			self.__playlist__.addToPlaylist(params)
		if (get("action") == "remove_from_playlist"):
			self.__playlist__.removeFromPlaylist(params)
		if (get("action") == "delete_playlist"):
			self.__playlist__.deletePlaylist(params)
		if (get("action") == "reverse_order"):
			self.__storage__.reversePlaylistOrder(params)
			
	#==================================== Item Building and Listing ===========================================	
	def list(self, params = {}):
		get = params.get
		results = []
		if (get("feed") == "search" or get("scraper") == "search_disco"):
			if not get("search"):
				query = self.getUserInput(self.__language__(30006), '')
				if not query:
					return False
				params["search"] = query
			if get("scraper") == "search_disco":
				params["store"] = "disco_searches"
			self.__storage__.saveStoredSearch(params)
			if get("scraper") == "search_disco":
				del params["store"]
		
		if get("scraper"):
			(results , status) = self.__scraper__.scrape(params)
		elif get("store"):
			(results , status) = self.__storage__.list(params)
			print self.__plugin__ + " store returned " + repr(results)
		else:
			(results , status) = self.__feeds__.list(params)
		
		if status == 200:
			if get("folder"):
				self.parseFolderList(params, results)
			else:
				self.parseVideoList(params, results)
			return True
		else:
			label = ""
			if get("external"):
				categories = self.__storage__.user_options
			else:
				categories = self.categories
				
			for category in categories:
				cat_get = category.get
				if (
					(get("feed") and cat_get("feed") == get("feed")) or 
					(get("user_feed") and cat_get("user_feed") == get("user_feed")) or
					(get("scraper") and cat_get("scraper") == get("scraper")) 
					):
					label = cat_get("Title")
			
			if get("channel"):
				label = get("channel")
			if get("playlist"):
				label = self.__language__(30615)
			if label:
				self.showMessage(label, self.__language__(30601))
		return False
	
	#================================== Plugin Actions =========================================
	
	def addToFavorites(self, params = {}):
		get = params.get
		if (get("videoid")):
			(message, status) = self.__feeds__.add_favorite(params)
			if status != 200:
				self.showErrorMessage(self.__language__(30020), message, status)
				return False	
		return True
			
	def removeFromFavorites(self, params = {}):
		get = params.get
		
		if (get("editid")):
			(message, status ) = self.__feeds__.delete_favorite(params)
			if status != 200:
				self.showErrorMessage(self.__language__(30020), message, status)
				return False
			xbmc.executebuiltin( "Container.Refresh" )
		
		return True
	
	def addContact(self, params = {}):
		get = params.get

		if not get("contact"):
			contact = self.getUserInput(self.__language__(30519), '')
			params["contact"] = contact
			
		if (get("contact")):
			(result, status) = self.__feeds__.add_contact(params)
			if status != 200:
				self.showErrorMessage(self.__language__(30029), result, status)
				return False
			self.showMessage(self.__language__(30613), contact)
			xbmc.executebuiltin( "Container.Refresh" )

		return True
	
	def removeContact(self, params = {}):
		get = params.get

		if (get("contact")):
			(result, status) = self.__feeds__.remove_contact(params)
			if status != 200:
				self.showErrorMessage(self.__language__(30029), result, status)
				return False
			
			self.showMessage(self.__language__(30614), get("contact"))
			xbmc.executebuiltin( "Container.Refresh" )
		return True
	
	def addSubscription(self, params = {}):
		get = params.get
		if (get("channel")):
			(message, status) = self.__feeds__.add_subscription(params)
			if status != 200:
				self.showErrorMessage(self.__language__(30021), message, status)
				return False
		
		return True
	
	def removeSubscription(self, params = {}):
		get = params.get
		if (get("editid")):
			(message, status) = self.__feeds__.remove_subscription(params)
			if status != 200:
				self.showErrorMessage(self.__language__(30021), message, status)
				return False
												
			xbmc.executebuiltin( "Container.Refresh" )
		return True
		
	#================================== List Item manipulation =========================================	
	# is only used by List Menu
	def addListItem(self, params = {}, item_params = {}):
		get = params.get
		item = item_params.get
		
		if (not item("action")): 
			if (item("login") == "false"):
				self.addFolderListItem(params, item_params)				
			else:
				if (len(self.__settings__.getSetting( "oauth2_access_token" )) > 0):
					self.addFolderListItem(params, item_params)
		else :
			if (item("action") == "settings"):
				if (len(self.__settings__.getSetting( "oauth2_access_token" )) > 0):
					if (item("login") == "true"):
						self.addActionListItem(params, item_params)
				else:
					if (item("login") == "false"):
						self.addActionListItem(params, item_params)
			elif (item("action") == "play_video"):
				self.addVideoListItem(params, item_params, 0)
			else:
				self.addActionListItem(params, item_params)
	
	# common function for adding folder items
	def addFolderListItem(self, params = {}, item_params = {}, size = 0):
		get = params.get
		item = item_params.get
		
		icon = "DefaultFolder.png"
		if item("icon"):
			icon = self.getThumbnail(item("icon"))
				
		thumbnail = item("thumbnail")
		
		cm = self.addFolderContextMenuItems(params, item_params)
		
		if (item("thumbnail", "DefaultFolder.png").find("http://") == -1):	
			thumbnail = self.getThumbnail(item("thumbnail"))
			
		listitem=xbmcgui.ListItem( item("Title"), iconImage=icon, thumbnailImage=thumbnail )
		url = '%s?path=%s&' % ( sys.argv[0], item("path") )
		url = self.buildItemUrl(item_params, url)
		
		if len(cm) > 0:
			listitem.addContextMenuItems( cm, replaceItems=False )
		
		listitem.setProperty( "Folder", "true" )
		if (item("feed") == "downloads"):
			url = self.__settings__.getSetting("downloadPath")
		xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=True, totalItems=size)
	
	# common function for adding action items
	def addActionListItem(self, params = {}, item_params = {}, size = 0):
		get = params.get
		item = item_params.get
		folder = True
		icon = "DefaultFolder.png"
		thumbnail = self.getThumbnail(item("thumbnail"))
		listitem=xbmcgui.ListItem( item("Title"), iconImage=icon, thumbnailImage=thumbnail )
		
		if (item("action") == "playbyid"):
			folder = False
			listitem.setProperty('IsPlayable', 'true');
			
		url = '%s?path=%s&' % ( sys.argv[0], item("path") )
		url += 'action=' + item("action") + '&'
			
		xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=folder, totalItems=size)
	
	# common function for adding video items
	def addVideoListItem(self, params = {}, item_params = {}, listSize = 0): 
		get = params.get
		item = item_params.get
		
		icon = item("icon","default")
		if (get("scraper", "").find("trailers") > 0):
			icon = "trailers"
		elif(get("scraper","").find("movies") > 0):
			icon = "movies"
		elif(get("scraper","").find("disco") > 0):
			icon = "discoball"
		elif(get("feed","").find("live") > 0):
			icon = "live"
		
		icon = self.getThumbnail(icon)
		
		listitem=xbmcgui.ListItem(item("Title"), iconImage=icon, thumbnailImage=item("thumbnail") )

		url = '%s?path=%s&action=play_video&videoid=%s' % ( sys.argv[0], item("path"), item("videoid"));
		
		if get("scraper") == "watch_later":
			url+= "&watch_later=true&playlist=%s&playlist_entry_id=%s&" % (get("playlist"), item("playlist_entry_id")) 
			
		cm = self.addVideoContextMenuItems(params, item_params)
				
		listitem.addContextMenuItems( cm, replaceItems=True )

		listitem.setProperty( "Video", "true" )
		listitem.setProperty( "IsPlayable", "true")
		listitem.setInfo(type='Video', infoLabels=item_params)
		xbmcplugin.setContent( handle=int( sys.argv[ 1 ] ), content="movies" )
		xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=False, totalItems=listSize + 1)
	
	#==================================== Core Output Parsing Functions ===========================================

	#parses a folder list consisting of a tuple of dictionaries
	def parseFolderList(self, params, results):
		listSize = len(results)
		get = params.get
		
		cache = True
		if get("store") or get("user_feed"):
			cache = False
		
		for result_params in results:
			result_params["path"] = get("path")
			self.addFolderListItem( params, result_params, listSize + 1)
		
		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True, cacheToDisc=cache )
	
	#parses a video list consisting of a tuple of dictionaries 
	def parseVideoList(self, params, results):
		listSize = len(results)
		get = params.get
		
		for result_params in results:
			result_params["path"] = get("path")
			result = result_params.get

			if result("videoid") == "false":
				continue
			
			if get("scraper") == "watch_later":
				result_params["index"] = str(results.index(result_params) + 1)
			
			if result("next") == "true":
				self.addFolderListItem(params, result_params, listSize)
			else:
				self.addVideoListItem( params, result_params, listSize)
				
		video_view = int(self.__settings__.getSetting("list_view")) <= 1
		if (video_view):
			xbmc.executebuiltin("Container.SetViewMode(500)")
		
		xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED )
		xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
		xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RATING )
		xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE )
		xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_PROGRAM_COUNT )
		xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
		xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_GENRE )	   
		
		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True, cacheToDisc=True )

	def addVideoContextMenuItems(self, params = {}, item_params = {}):
		cm = []
		get = params.get
		item = item_params.get

		title = self.makeAscii(item("Title"))
		url_title = urllib.quote_plus(title)
		studio = self.makeAscii(item("Studio","Unknown Author"))
		url_studio = urllib.quote_plus(studio)
		
		cm.append( ( self.__language__( 30504 ), "XBMC.Action(Queue)", ) )
		
		if (get("playlist")):
			cm.append( (self.__language__(30521), "XBMC.RunPlugin(%s?path=%s&action=play_all&playlist=%s&videoid=%s&)" % ( sys.argv[0], item("path"), get("playlist"), item("videoid") ) ) )
					
		if (get("user_feed") == "newsubscriptions" or get("user_feed") == "favorites"):
			contact = "default"
			if get("contact"):
				contact = get("contact") 
			cm.append( (self.__language__(30521), "XBMC.RunPlugin(%s?path=%s&action=play_all&user_feed=%s&contact=%s&videoid=%s&)" % ( sys.argv[0], item("path"), get("user_feed"), contact, item("videoid") ) ) )
				
		cm.append( ( self.__language__(30501), "XBMC.RunPlugin(%s?path=%s&action=download&videoid=%s)" % ( sys.argv[0],  item("path"), item("videoid") ) ) )

		if ( self.__settings__.getSetting( "username" ) != "" and self.__settings__.getSetting( "oauth2_access_token" ) ):
			if ( get("user_feed") == "favorites" and not get("contact") ):
				cm.append( ( self.__language__( 30506 ), 'XBMC.RunPlugin(%s?path=%s&action=remove_favorite&editid=%s&)' % ( sys.argv[0], item("path"), item("editid") ) ) )
			else:
				cm.append( ( self.__language__( 30503 ), 'XBMC.RunPlugin(%s?path=%s&action=add_favorite&videoid=%s&)' % ( sys.argv[0],  item("path"), item("videoid") ) ) )
			if (get("external") == "true" or (get("feed") != "subscriptions_favorites" and get("feed") != "subscriptions_uploads" and get("feed") != "subscriptions_playlists" and (get("user_feed") != "uploads" and not get("external")))):
				cm.append( ( self.__language__( 30512 ) % item("Studio"), 'XBMC.RunPlugin(%s?path=%s&channel=%s&action=add_subscription)' % ( sys.argv[0], item("path"), item("Studio") ) ) )
				
			if (get("playlist") and item("playlist_entry_id")):
				cm.append( (self.__language__(30530), "XBMC.RunPlugin(%s?path=%s&action=remove_from_playlist&playlist=%s&playlist_entry_id=%s&)" % ( sys.argv[0], item("path"), get("playlist"), item("playlist_entry_id") ) ) )
			cm.append( (self.__language__(30528), "XBMC.RunPlugin(%s?path=%s&action=add_to_playlist&videoid=%s&)" % ( sys.argv[0], item("path"), item("videoid") ) ) )
			
		if (get("feed") != "uploads" and get("user_feed") != "uploads" ):
			cm.append( ( self.__language__( 30516 ) % studio, "XBMC.Container.Update(%s?path=%s&feed=uploads&channel=%s)" % ( sys.argv[0],  get("path"), url_studio ) ) )
					
		cm.append( ( self.__language__( 30514 ), "XBMC.Container.Update(%s?path=%s&feed=search&search=%s)" % ( sys.argv[0],  get("path"), url_title ) ) )
		cm.append( ( self.__language__( 30527 ), "XBMC.Container.Update(%s?path=%s&feed=related&videoid=%s)" % ( sys.argv[0],  get("path"), item("videoid") ) ) )
		cm.append( ( self.__language__( 30523 ), "XBMC.ActivateWindow(VideoPlaylist)"))
		cm.append( ( self.__language__( 30502 ), "XBMC.Action(Info)", ) )
		
		return cm
		
	def addFolderContextMenuItems(self, params = {}, item_params = {}):
		cm = []
		get = params.get
		item = item_params.get
		
		if (item("next","false") == "true"):
			return cm
		
		if item("artist"):
			cm.append ( (self.__language__(30507), "XBMC.Container.Update(%s?path=%s&scraper=similar_artist&artist=%s&folder=true&)" % ( sys.argv[0], item("path"), item("artist") ) ) )
			cm.append ( (self.__language__(30540), "XBMC.RunPlugin(%s?path=%s&action=delete_artist&store=artists&artist=%s&)" % ( sys.argv[0], item("path"), item("artist") ) ) )			
			cm.append( (self.__language__( 30520 ), "XBMC.RunPlugin(%s?path=%s&action=play_all&scraper=music_artists&artist=%s&)" % ( sys.argv[0], item("path"), item("artist") ) ) )
			cm.append( (self.__language__( 30522 ), "XBMC.RunPlugin(%s?path=%s&action=play_all&shuffle=true&scraper=music_artists&artist=%s&)" % ( sys.argv[0], item("path"), item("artist") ) ) )

			
		if (item("user_feed") == "favorites" or item("user_feed") == "newsubscriptions"):
			cm.append ( (self.__language__(30520), "XBMC.RunPlugin(%s?path=%s&action=play_all&user_feed=%s&contact=%s&)" % ( sys.argv[0], item("path"), item("user_feed"), "default" ) ) )
			cm.append ( (self.__language__(30522), "XBMC.RunPlugin(%s?path=%s&action=play_all&shuffle=true&user_feed=%s&contact=%s&)" % ( sys.argv[0], item("path"), item("user_feed"), "default" ) ) )
		if (item("playlist")):
			cm.append ( (self.__language__(30531), "XBMC.RunPlugin(%s?path=%s&action=reverse_order&playlist=%s&)" % ( sys.argv[0], item("path"), item("playlist") ) ) )
			cm.append ( (self.__language__(30520), "XBMC.RunPlugin(%s?path=%s&action=play_all&playlist=%s&)" % ( sys.argv[0], item("path"), item("playlist") ) ) )
			cm.append ( (self.__language__(30522), "XBMC.RunPlugin(%s?path=%s&action=play_all&shuffle=true&playlist=%s&)" % ( sys.argv[0], item("path"), item("playlist") ) ) )
			if not get("external"):
				cm.append ( (self.__language__(30539), "XBMC.RunPlugin(%s?path=%s&action=delete_playlist&playlist=%s&)" % ( sys.argv[0], item("path"), item("playlist") ) ) )
			
		if item("scraper") == "watch_later":
			cm.append( (self.__language__( 30520 ), "XBMC.RunPlugin(%s?path=%s&action=play_all&scraper=watch_later&login=true&)" % ( sys.argv[0], item("path") ) ) )
			cm.append( (self.__language__( 30522 ), "XBMC.RunPlugin(%s?path=%s&action=play_all&shuffle=true&scraper=watch_later&login=true&)" % ( sys.argv[0], item("path") ) ) )
		
		if item("scraper") == "recommended":
			cm.append( (self.__language__( 30520 ), "XBMC.RunPlugin(%s?path=%s&action=play_all&scraper=recommended&login=true&)" % ( sys.argv[0], item("path") ) ) )
			cm.append( (self.__language__( 30522 ), "XBMC.RunPlugin(%s?path=%s&action=play_all&shuffle=true&scraper=recommended&login=true&)" % ( sys.argv[0], item("path") ) ) )
				
		if (item("scraper") == "liked_videos"):
			cm.append( (self.__language__( 30520 ), "XBMC.RunPlugin(%s?path=%s&action=play_all&scraper=liked_videos&login=true&)" % ( sys.argv[0], item("path") ) ) )
			cm.append( (self.__language__( 30522 ), "XBMC.RunPlugin(%s?path=%s&action=play_all&shuffle=true&scraper=liked_videos&login=true&)" % ( sys.argv[0], item("path") ) ) )
		
		if (item("scraper") == "search_disco"):
			cm.append( (self.__language__( 30520 ), "XBMC.RunPlugin(%s?path=%s&action=play_all&search_disco=%s&)" % ( sys.argv[0], item("path"), item("search") ) ) )
			cm.append( (self.__language__( 30522 ), "XBMC.RunPlugin(%s?path=%s&action=play_all&shuffle=true&search_disco=%s&)" % ( sys.argv[0], item("path"), item("search") ) ) )
			if not get("scraper") == "disco_top_artist":			
				cm.append( ( self.__language__( 30524 ), 'XBMC.Container.Update(%s?path=%s&action=edit_disco&store=disco_searches&search=%s&)' % ( sys.argv[0], item("path"), item("search") ) ) )
				cm.append( ( self.__language__( 30525 ), 'XBMC.RunPlugin(%s?path=%s&action=delete_disco&store=disco_searches&delete=%s&)' % ( sys.argv[0], item("path"), item("search") ) ) )								

		if (item("feed") == "search"):
			cm.append( ( self.__language__( 30515 ), 'XBMC.Container.Update(%s?path=%s&action=edit_search&store=searches&search=%s&)' % ( sys.argv[0], item("path"), item("search") ) ) )
			cm.append( ( self.__language__( 30508 ), 'XBMC.RunPlugin(%s?path=%s&action=delete_search&store=searches&delete=%s&)' % ( sys.argv[0], item("path"), item("search") ) ) )
					
		if (item("view_mode")):
			cm_url = 'XBMC.Container.Update(%s?path=%s&channel=%s&action=change_subscription_view&view_mode=%s&' % ( sys.argv[0], item("path"), item("channel"), "%s")
			if (item("external")):
				cm_url += "external=true&contact=" + get("contact") + "&"
			cm_url +=")"
			
			if (item("user_feed") == "favorites"):
				cm.append ( (self.__language__( 30511 ), cm_url % ("uploads")))
				cm.append( (self.__language__( 30526 ), cm_url % ("playlists&folder=true")))
			elif(item("user_feed") == "playlists"):
				cm.append( (self.__language__( 30511 ), cm_url % ("uploads"))) 
				cm.append ( (self.__language__( 30510 ), cm_url % ("favorites")))
			elif (item("user_feed") == "uploads"):
				cm.append ( (self.__language__( 30510 ), cm_url % ("favorites")))
				cm.append( (self.__language__( 30526 ), cm_url % ("playlists&folder=true")))
		
		if (item("channel") or item("contact")):
			if ( self.__settings__.getSetting( "username" ) != "" and self.__settings__.getSetting( "oauth2_access_token" ) ):
				if (get("external")):
					channel = get("channel","")
					if not channel:
						channel = get("contact")
					cm.append( ( self.__language__( 30512 ) % item("channel"), 'XBMC.RunPlugin(%s?path=%s&channel=%s&action=add_subscription)' % ( sys.argv[0], item("path"), channel ) ) )
				else:
					if item("editid") and item("channel"):
						cm.append( ( self.__language__( 30513 ) % item("channel"), 'XBMC.RunPlugin(%s?path=%s&editid=%s&action=remove_subscription)' % ( sys.argv[0], item("path"), item("editid") ) ) )
		
		if (item("contact") and not get("store")):
			if ( self.__settings__.getSetting( "username" ) != "" and self.__settings__.getSetting( "oauth2_access_token" ) ):
				if (item("external")):
					cm.append( (self.__language__(30026), 'XBMC.RunPlugin(%s?path=%s&action=add_contact&)' % ( sys.argv[0], item("path") ) ) )
				else:
					cm.append( (self.__language__(30025), 'XBMC.RunPlugin(%s?path=%s&action=remove_contact&contact=%s&)' % ( sys.argv[0], item("path"), item("Title") ) ) )
				
		cm.append( ( self.__language__( 30523 ), "XBMC.ActivateWindow(VideoPlaylist)"))
		return cm
