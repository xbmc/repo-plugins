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

import sys
import os
import xbmc
import xbmcgui
import xbmcplugin
import urllib
import YouTubeCore
import YouTubePlayer
import YouTubeScraperCore

core = YouTubeCore.YouTubeCore()
scraper = YouTubeScraperCore.YouTubeScraperCore()
player = YouTubePlayer.YouTubePlayer()

class YouTubeNavigation:	 
	__settings__ = sys.modules[ "__main__" ].__settings__
	__language__ = sys.modules[ "__main__" ].__language__
	__plugin__ = sys.modules[ "__main__"].__plugin__	
	__dbg__ = sys.modules[ "__main__" ].__dbg__
	
	plugin_thumbnail_path = os.path.join( __settings__.getAddonInfo('path'), "thumbnails" )
	pr_video_quality = __settings__.getSetting("pr_video_quality") == "true"

	#===============================================================================
	# The time parameter restricts the search to videos uploaded within the specified time. 
	# Valid values for this parameter are today (1 day), this_week (7 days), this_month (1 month) and all_time. 
	# The default value for this parameter is all_time.
	# 
	# This parameter is supported for search feeds as well as for the top_rated, top_favorites, most_viewed, 
	# most_popular, most_discussed and most_responded standard feeds.
	#===============================================================================

	feeds = {};
	feeds['uploads'] = "http://gdata.youtube.com/feeds/api/users/%s/uploads"
	feeds['favorites'] = "http://gdata.youtube.com/feeds/api/users/%s/favorites"
	feeds['playlists'] = "http://gdata.youtube.com/feeds/api/users/%s/playlists"
	feeds['playlist_root'] = "http://gdata.youtube.com/feeds/api/playlists/%s"
	feeds['list_related'] = "http://gdata.youtube.com/feeds/api/videos/%s/related"
	feeds['newsubscriptions'] = "http://gdata.youtube.com/feeds/api/users/%s/newsubscriptionvideos";
	feeds['contacts'] = "http://gdata.youtube.com/feeds/api/users/default/contacts";
	feeds['subscriptions'] = "http://gdata.youtube.com/feeds/api/users/%s/subscriptions";
	feeds['feed_rated'] = "http://gdata.youtube.com/feeds/api/standardfeeds/top_rated?time=%s";
	feeds['feed_favorites'] = "http://gdata.youtube.com/feeds/api/standardfeeds/top_favorites?time=%s";
	feeds['feed_viewed'] = "http://gdata.youtube.com/feeds/api/standardfeeds/most_viewed?time=%s";
	feeds['feed_linked'] = "http://gdata.youtube.com/feeds/api/standardfeeds/most_popular?time=%s"; 
	feeds['feed_recent'] = "http://gdata.youtube.com/feeds/api/standardfeeds/most_recent"; # doesn't work with time
	feeds['feed_discussed'] = "http://gdata.youtube.com/feeds/api/standardfeeds/most_discussed?time=%s";
	feeds['feed_responded'] = "http://gdata.youtube.com/feeds/api/standardfeeds/most_responded?time=%s";
	feeds['feed_featured'] = "http://gdata.youtube.com/feeds/api/standardfeeds/recently_featured"; # doesn't work with time
	feeds['subscriptions_uploads'] = "http://gdata.youtube.com/feeds/api/users/%s/uploads";
	feeds['subscriptions_favorites'] = "http://gdata.youtube.com/feeds/api/users/%s/favorites";
	feeds['subscriptions_playlists'] = "http://gdata.youtube.com/feeds/api/users/%s/playlists";

	# we fill the list with category definitions, with labels from the appropriate language file
	#			   label						  , path								    , thumbnail					  ,  login		  ,  feed / action
	categories = (
				  {'Title':__language__( 30044 )  ,'path':"/root/explore"			 		, 'thumbnail':"explore"				, 'login':"false" },
				  {'Title':__language__( 30041 )  ,'path':"/root/explore/categories"		, 'thumbnail':"explore"				, 'login':"false" , 'scraper':'categories'},
				  {'Title':__language__( 30037 )  ,'path':"/root/explore/disco"				, 'thumbnail':"discoball"		 	, 'login':"false" , 'store':"disco_searches" },
				  {'Title':__language__( 30040 )  ,'path':"/root/explore/disco/search"		, 'thumbnail':"search"		   		, 'login':"false" , 'action':"search_disco"},
				  {'Title':__language__( 30038 )  ,'path':"/root/explore/disco/top_25"		, 'thumbnail':"discoball"		 	, 'login':"false" , 'scraper':"disco_top_25"},
				  {'Title':__language__( 30039 )  ,'path':"/root/explore/disco/popular"		, 'thumbnail':"discoball"		 	, 'login':"false" , 'scraper':"disco_top_artist"},
				  {'Title':__language__( 30001 )  ,'path':"/root/explore/feeds"				, 'thumbnail':"feeds"			 	, 'login':"false" },
				  {'Title':__language__( 30009 )  ,'path':"/root/explore/feeds/discussed"	, 'thumbnail':"most"			 	, 'login':"false" , 'feed':"feed_discussed" },
				  {'Title':__language__( 30010 )  ,'path':"/root/explore/feeds/linked"		, 'thumbnail':"most"			 	, 'login':"false" , 'feed':"feed_linked" },
				  {'Title':__language__( 30011 )  ,'path':"/root/explore/feeds/viewed"		, 'thumbnail':"most"			 	, 'login':"false" , 'feed':"feed_viewed" },
				  {'Title':__language__( 30012 )  ,'path':"/root/explore/feeds/recent"		, 'thumbnail':"most"			 	, 'login':"false" , 'feed':"feed_recent" },
				  {'Title':__language__( 30013 )  ,'path':"/root/explore/feeds/responded"	, 'thumbnail':"most"			 	, 'login':"false" , 'feed':"feed_responded" },
				  {'Title':__language__( 30014 )  ,'path':"/root/explore/feeds/featured"	, 'thumbnail':"featured"		 	, 'login':"false" , 'feed':"feed_featured" },
				  {'Title':__language__( 30015 )  ,'path':"/root/explore/feeds/favorites"	, 'thumbnail':"top"					, 'login':"false" , 'feed':"feed_favorites" },
				  {'Title':__language__( 30016 )  ,'path':"/root/explore/feeds/rated"		, 'thumbnail':"top"					, 'login':"false" , 'feed':"feed_rated" },
				  {'Title':__language__( 30043 )  ,'path':"/root/explore/movies"			, 'thumbnail':"movies"				, 'login':"false" , 'scraper':'movies'},
				  {'Title':__language__( 30042 )  ,'path':"/root/explore/shows"				, 'thumbnail':"shows"				, 'login':"false" , 'scraper':'shows'},
				  {'Title':__language__( 30032 )  ,'path':"/root/explore/trailers"			, 'thumbnail':"trailers"			, 'login':"false" },
				  {'Title':__language__( 30035 )  ,'path':"/root/explore/trailers/latest"   , 'thumbnail':"trailers"			, 'login':"false" , 'scraper':"latest_trailers" },
				  {'Title':__language__( 30034 )  ,'path':"/root/explore/trailers/current"  , 'thumbnail':"trailers"			, 'login':"false" , 'scraper':"current_trailers" },
				  {'Title':__language__( 30036 )  ,'path':"/root/explore/trailers/upcoming" , 'thumbnail':"trailers"			, 'login':"false" , 'scraper':"upcoming_trailers" },
				  {'Title':__language__( 30033 )  ,'path':"/root/explore/trailers/popular"  , 'thumbnail':"trailers"			, 'login':"false" , 'scraper':"popular_trailers" },
				  {'Title':__language__( 30019 )  ,'path':"/root/recommended"				, 'thumbnail':"recommended"			, 'login':"true"  , 'scraper':"recommended" },
				  {'Title':__language__( 30018 )  ,'path':"/root/contacts"		  			, 'thumbnail':"contacts"			, 'login':"true"  , 'feed':"contacts" },
				  {'Title':__language__( 30002 )  ,'path':"/root/favorites"		 			, 'thumbnail':"favorites"			, 'login':"true"  , 'feed':"favorites" },
				  {'Title':__language__( 30017 )  ,'path':"/root/playlists"		 			, 'thumbnail':"playlists"			, 'login':"true"  , 'feed':"playlists" },
				  {'Title':__language__( 30003 )  ,'path':"/root/subscriptions"	 			, 'thumbnail':"subscriptions"		, 'login':"true"  , 'feed':"subscriptions" },
				  {'Title':__language__( 30004 )  ,'path':"/root/subscriptions/new" 		, 'thumbnail':"newsubscriptions"	, 'login':"true"  , 'feed':"newsubscriptions" },
				  {'Title':__language__( 30005 )  ,'path':"/root/uploads"					, 'thumbnail':"uploads"				, 'login':"true"  , 'feed':"uploads" },
				  {'Title':__language__( 30045 )  ,'path':"/root/downloads"					, 'thumbnail':"downloads"			, 'login':"false" , 'feed':"downloads" },
				  {'Title':__language__( 30006 )  ,'path':"/root/search"					, 'thumbnail':"search"				, 'login':"false" , 'store':"searches" },
				  {'Title':__language__( 30007 )  ,'path':"/root/search/new"				, 'thumbnail':"search"				, 'login':"false" , 'action':"search" },
				  {'Title':__language__( 30008 )  ,'path':"/root/playbyid"		  			, 'thumbnail':"playbyid"			, 'login':"false" , 'action':"playbyid" },
				  {'Title':__language__( 30027 )  ,'path':"/root/login"			 			, 'thumbnail':"login"				, 'login':"false" , 'action':"settings" },
				  {'Title':__language__( 30028 )  ,'path':"/root/settings"		  			, 'thumbnail':"settings"			, 'login':"true"  , 'action':"settings" }
				  )

	#==================================== Main Entry Points===========================================
	def listMenu(self, params = {}):
		get = params.get
		cache = True
		if (get("scraper")):
			self.scrape(params)
			return
		
		if (get("options") == "contact_options"):
			self.listOptionFolder(params)
			
		if (get("login") == "true"):
			if (get('feed') == 'subscriptions' or get('feed') == 'playlists' or get('feed') == 'contacts' or get("feed") == "subscriptions_playlists" ):
				self.listUserFolder(params)				  
			elif ( get("feed") in self.feeds):
				self.listUserFolderFeeds(params)
			elif (get("feed") == "contact_option_list"):
				self.listOptionFolder(params)
			return

		if (get("feed")):
			if ( get("feed") in self.feeds):
				self.listFeedFolder(params)
			return
		
		path = get("path", "/root")
		
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
		
		if (get("store") == "searches" or get("store") == "disco_searches"):
				self.listStoredSearches(params)
				cache = False
		
		video_view = self.__settings__.getSetting("list_view") == "1"
		if (self.__dbg__):
			print self.__plugin__ + " view mode: " + self.__settings__.getSetting("list_view")
		
		if (get("scraper") == "shows" and get("category") and not video_view):
			video_view = self.__settings__.getSetting("list_view") == "0"
			
		if (video_view):
			if (self.__dbg__):
				print self.__plugin__ + " setting view mode"
			xbmc.executebuiltin("Container.SetViewMode(500)")
		
		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True, cacheToDisc=cache )

	def executeAction(self, params = {}):
		get = params.get
		if (get("action") == "playbyid"):
			self.playVideoById(params)
		if (get("action") == "search" or get("action") == "search_disco"):
			self.search(params)
		if (get("action") == "refine_user"):
			self.refineSearch(params)
		if (get("action") == "delete_refinements"):
			self.deleteRefinements(params)
		if (get("action") == "settings"):
			self.login(params)
		if (get("action") == "delete_search" or get("action") == "delete_disco"):
			self.deleteSearch(params)
		if (get("action") == "edit_search" or get("action") == "edit_disco"):
			self.editSearch(params)
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
			self.downloadVideo(params)
		if (get("action") == "list_related"):
			self.listRelated(params)
		if (get("action") == "play_video"):
			player.playVideo(params)
		if (get("action") == "change_subscription_view"):
			self.changeSubscriptionView(params)

	def listOptionFolder(self, params = {}):
		get = params.get
		if ( get('login') and self.__settings__.getSetting( "username" ) != "" ):
			auth = self.__settings__.getSetting( "auth" )
			if ( not auth ) :
				self.login()
				auth = self.__settings__.getSetting( "auth" )

		item_favorites = {'Title':self.__language__( 30020 ), 'path':get("path"), 'external':"true", 'login':"true", 'thumbnail':"favorites", 'feed':"favorites", "contact":get("contact")}
		self.addFolderListItem(params, item_favorites, 1)
		item_playlists = {'Title':self.__language__( 30023 ), 'path':get("path"), 'external':"true", 'login':"true", 'thumbnail':"playlists", 'feed':"playlists", "contact":get("contact")}
		self.addFolderListItem(params, item_playlists, 2)
		item_subscriptions = {'Title':self.__language__( 30021 ), 'path':get("path"), 'external':"true", 'login':"true", 'thumbnail':"subscriptions", 'feed':"subscriptions", "contact":get("contact")}
		self.addFolderListItem(params, item_subscriptions, 3)
		item_uploads = {'Title':self.__language__( 30022 ), 'path':get("path"), 'external':"true", 'login':"true", 'thumbnail':"uploads", 'feed':"uploads", "contact":get("contact") }
		self.addFolderListItem(params, item_uploads, 4)
		
		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True, cacheToDisc=False)

	def parseFeeds(self, params):
		get = params.get
				
		feed = self.feeds[get("feed")]
		if (feed.find("%s") > 0):
			if ( get("contact") and not (get("external") and get("channel"))):
				feed = feed % get("contact")
			elif ( get("channel")):
				feed = feed % get("channel")
				print "found channel " + feed
			elif ( get("playlist")):
				feed = feed % get("playlist")
			elif ( get("feed") == "uploads" or get("feed") == "favorites" or  get("feed") == "playlists" or get("feed") == "subscriptions" or get("feed") == "newsubscriptions"):
				feed = feed % self.__settings__.getSetting( "nick" )
		return feed
	
	def listUserFolder(self, params = {}):
		get = params.get
		if ( get('login') and self.__settings__.getSetting( "username" ) != "" ):
			auth = self.__settings__.getSetting( "auth" )
			if ( not auth ) :
				self.login()
				auth = self.__settings__.getSetting( "auth" )
				
		feed = self.parseFeeds(params)
		
		(result, status) = core.playlists(feed, params)
		if status != 200:
			feed_label = ""
			for category in self.categories:
				cat_get = category.get
				if (cat_get("feed") == get("feed")):
					feed_label = cat_get("Title")
					break
			
			if (feed_label != ""):
				self.errorHandling(feed_label, result, status)
			else:
				self.errorHandling(get("feed"), result, status)
				
			return False
			
		if ( get("feed") == "contacts"):
			item_add_user = {'Title':self.__language__( 30024 ), 'path':get("path"), 'login':"true", 'thumbnail':"add_user", 'action':"add_contact"}
			self.addFolderListItem(params, item_add_user,  1)
						
		if ( get('feed') == 'subscriptions' ):
			if (not get("page")):
				item = {"Title":self.__language__( 30004 ), "path":"/root/subscriptions/new", "thumbnail":"newsubscriptions", "login":"true", "feed":"newsubscriptions"}
				if (get("contact")):
					item["contact"] = get("contact")
				
				self.addFolderListItem(params, item)
							
		self.parseFolderList(params, result)
								
	def listUserFolderFeeds(self, params = {}):
		get = params.get
		if ( get('login') and self.__settings__.getSetting( "username" ) != "" ):
			auth = self.__settings__.getSetting( "auth" )
			if ( not auth ) :
				self.login()
				auth = self.__settings__.getSetting( "auth" )
			
		feed = self.parseFeeds(params)
		
		if ( get('login') and feed):
			( result, status ) = core.list(feed, params);
			if status != 200:
				feed_label = ""
				for category in self.categories:
					cat_get = category.get
					if (cat_get("feed") == get("feed")):
						feed_label = cat_get("Title")
						break
					
				if (feed_label != ""):
					self.errorHandling(feed_label, result, status)
				else:
					self.errorHandling(get("feed"), result, status)
				return False
		
		if ( get("channel") or get("playlist") ):
			thumbnail = result[0].get("thumbnail")
			if (thumbnail): 
				if (get("channel")):
					self.__settings__.setSetting("subscriptions_" + get("channel") + "_thumb", thumbnail)
				if (get("playlist")):
					self.__settings__.setSetting("playlists_" + get("playlist") + "_thumb", thumbnail)

		self.parseVideoList(params, result);
		
	def login(self, params = {}):
		self.__settings__.openSettings()
						
		(result, status) = core.login()
				
		if status == 200:
			self.errorHandling(self.__language__(30031), result, 303)
		else:
			self.errorHandling(self.__language__(30609), result, status)
				
		xbmc.executebuiltin( "Container.Refresh" )

	def listStoredSearches(self, params = {}):
		get = params.get
		try:
			if (get("store") == "searches"):
				searches = eval(self.__settings__.getSetting("stored_searches"))
			else:
				searches = eval(self.__settings__.getSetting("stored_disco_searches"))
		except:
			searches = []
		
		for search in searches:
			item = {}
			item["path"] = get("path")
			item["Title"] = search
			item["search"] = urllib.quote_plus(search)
			if (get("store") == "searches"):
				item["action"] = "search"
				item["thumbnail"] = self.__settings__.getSetting("search_" + search + "_thumb")
			else:
				item["action"] = "search_disco"
				item["thumbnail"] = self.__settings__.getSetting("disco_search_" + search + "_thumb")
			
			self.addFolderListItem(params, item, len(searches))

	def listFeedFolder(self, params = {}):
		get = params.get

		feed = self.feeds[get("feed")]
		
		if (get("channel")):
			feed = feed % get("channel")
		
		if (get("videoid")):
			feed = feed % get("videoid")
		
		( result, status ) = core.feeds(feed, params)
		if status != 200:
			feed_label = ""
			for category in self.categories:
				cat_get = category.get
				if (cat_get("action") == get("feed")):
					feed_label = cat_get("Title")
					break
				
			if (feed_label != ""):
				self.errorHandling(feed_label, result, status)
			else:
				self.errorHandling(get("feed"), result, status)
				
			return False
		
		if ( get("search")):
			thumbnail = result[0].get("thumbnail")
			if (thumbnail and get("search")):
				self.__settings__.setSetting("search_" + get("search") + "_thumb", thumbnail)

		self.parseVideoList(params, result);

	def scrape(self, params):
		get = params.get

		( results, status ) = scraper.scrape(params)
		if ( len(results) > 0 and status == 200 ):
			if (get("scraper") == "disco_top_artist" 
				or get("scraper") == "shows"
				or (get("scraper") == "movies" and not get("category"))
				or (get("scraper") == "movies" and get("subcategory"))
				or (get("scraper") == "categories" and not get("category"))
				):
				self.parseFolderList(params, results)
			elif( get("scraper") == "show"):
				if (results[0].get("folder") == "true") or get("folder") == "true":
					self.parseFolderList(params, results)
				else:
					self.parseVideoList(params, results)
			else:
				self.parseVideoList(params, results)
		elif ( status == 303):
			self.showMessage(self.__language__(30600), results)
		else:
			self.showMessage(self.__language__(30600), self.__language__(30606))

	#================================== Plugin Actions =========================================

	def playVideoById(self, params = {}):
		result = self.getUserInput(self.__language__(30518), '')
		params["videoid"] = result 
		if (result):
			player.playVideo(params);
						
	def downloadVideo(self, params = {}):
		get = params.get
		if (get("videoid")):
			path = self.__settings__.getSetting( "downloadPath" )
			if (not path):
				self.showMessage(self.__language__(30600), self.__language__(30611))
				self.__settings__.openSettings()
				path = self.__settings__.getSetting( "downloadPath" )

			( video, status ) = player.getVideoObject(params)
				
			if status != 200:
				if self.__dbg__:
					print self.__plugin__ + " downloadVideo got error from construct_video_url: [%s] %s" % ( status, video)
					self.errorHandling(self.__language__( 30501 ), video, status)
				return False

			item = video.get
					
			self.showMessage(self.__language__(30612), self.makeAscii(item("Title", "Unknown Title")))
			
			( video, status ) = core.downloadVideo(video)
					
			if status == 200:
				self.showMessage(self.__language__( 30604 ), self.makeAscii(item("Title")))

	def addToFavorites(self, params = {}):
		get = params.get
		
		if (get("videoid")):
			(message, status) = core.add_favorite(get("videoid"))
			if status != 200:
				self.errorHandling(self.__language__(30020), message, status)
				return False

			return True
			
	def removeFromFavorites(self, params = {}):
		get = params.get
		
		if (get("editid")):
			(message, status ) = core.delete_favorite(get('editid'))
			if status != 200:
				self.errorHandling(self.__language__(30020), message, status)
				return False

			xbmc.executebuiltin( "Container.Refresh" )
	
	def addContact(self, params = {}):
		get = params.get

		if (get("contact")):
			contact = get("contact")
		else:
			contact = self.getUserInput(self.__language__(30519), '')
			
		if (contact):
			(result, status) = core.add_contact(contact)
			if status != 200:
				self.errorHandling(self.__language__(30029), result, status)
				return False

			self.showMessage(self.__language__(30613), contact)
			xbmc.executebuiltin( "Container.Refresh" )

		return True
	
	def removeContact(self, params = {}):
		get = params.get

		if (get("contact")):
			(result, status) = core.remove_contact(get("contact"))
			if status != 200:
				self.errorHandling(self.__language__(30029), result, status)
				return False

			self.showMessage(self.__language__(30614), get("contact"))
			xbmc.executebuiltin( "Container.Refresh" )
	
	def changeSubscriptionView(self, params = {}):
		get = params.get
		
		if (get("view_mode")):  
			viewmode = ""
			if (get("external")):
				viewmode += "external_" + get("contact") + "_"
			viewmode += "view_mode_" + get("channel")
			
			self.__settings__.setSetting(viewmode, get("view_mode"))
		
		xbmc.executebuiltin( "Container.Refresh" )
	
	def addSubscription(self, params = {}):
		get = params.get
		if (get("channel")):
			(message, status) = core.add_subscription(get("channel"))
			if status != 200:
				self.errorHandling(self.__language__(30021), message, status)
				return False
			
		return True
	
	def removeSubscription(self, params = {}):
		get = params.get
		if (get("editid")):
			(message, status) = core.remove_subscription(get("editid"))
			if status != 200:
				self.errorHandling(self.__language__(30021), message, status)
				return False
												
			xbmc.executebuiltin( "Container.Refresh" )
		return True
	
	def listRelated(self, params={}):
		get = params.get
		if (get("videoid")):
			feed = self.feeds["list_related"] % get("videoid")
			(results, status) = core.list(feed, params)
			
			if status != 200:
				self.errorHandling(self.__language__(30529), results, status)
				return False
			
			self.parseVideoList(params, results)
		return True
	
	#================================== Searching =========================================
	def searchDisco(self, params = {}):
		get = params.get
		
		if (not get("search")):
			params["search"] = self.getUserInput(self.__language__(30006), '')
			
		(result, status) = scraper.searchDisco(params)
			
		if (status != 200):
			self.errorHandling(self.__language__(30006), result, status)
		else:
			self.parseVideoList(params, result)
	
	def search(self, params = {}):
		get = params.get
				
		if (get("search")):
			query = get("search")
			query = urllib.unquote_plus(query)
			if (get("action") == "search_disco"):
				self.saveSearch(query, query, "stored_disco_searches")
			else:
				self.saveSearch(query, query)
		else :
			query = self.getUserInput(self.__language__(30006), '')
			if (query):
				if (get("action") == "search_disco"):
					self.saveSearch(query, query, "stored_disco_searches")
				else:
					self.saveSearch(query, query)
				params["search"] = query
		
		if (query):
			if (get("action") == "search_disco"):
				( result, status ) = scraper.searchDisco(params)
			else:
				( result, status ) = core.search(query, get("page", "0"));
				
			if status != 200:
				self.errorHandling(self.__language__(30006), result, status)
				return False
			
			thumbnail = result[0].get('thumbnail', "")
			
			if (thumbnail and query):
				if (get("action") == "search_disco"):
					self.__settings__.setSetting("disco_search_" + query + "_thumb", thumbnail)
				else:
					self.__settings__.setSetting("search_" + query + "_thumb", thumbnail)
				
			self.parseVideoList(params, result)
			
	def deleteSearch(self, params = {}):
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
		
	def saveSearch(self, old_query, new_query, store = "stored_searches"):
		old_query = urllib.unquote_plus(old_query)
		new_query = urllib.unquote_plus(new_query)
		try:
			searches = eval(self.__settings__.getSetting(store))
		except:
			searches = []
		
		for count, search in enumerate(searches):
			if (search.lower() == old_query.lower()):
				del(searches[count])
				break

		searchCount = ( 10, 20, 30, 40, )[ int( self.__settings__.getSetting( "saved_searches" ) ) ]
		searches = [new_query] + searches[:searchCount]
		self.__settings__.setSetting(store, repr(searches))
	
	def editSearch(self, params = {}):
		get = params.get
		if (get("search")):
			old_query = urllib.unquote_plus(get("search"))
			new_query = self.getUserInput(self.__language__(30006), old_query)
			params["search"] = new_query
			
			if (get("action") == "edit_search"):
				self.saveSearch(old_query, new_query)
			else:
				params["action"] = "search_disco"
				self.saveSearch(old_query, new_query, "stored_disco_searches")
				
			self.search(params)

	def refineSearch(self, params = {}):
		get = params.get
		query = get("search")
		query = urllib.unquote_plus(query)
		
		try:
			searches = eval(self.__settings__.getSetting("stored_searches_author"))
		except :
			searches = {}
			
		if query in searches:
			author = self.getUserInput(self.__language__(30517), searches[query])
		else:
			author = self.getUserInput(self.__language__(30517), '')

		if author == "":
			if author in searches:
				del searches[query]
				xbmc.executebuiltin( "Container.Refresh" )
		elif author:
			searches[query] = author
			
			self.__settings__.setSetting("stored_searches_author", repr(searches))
			self.showMessage(self.__language__(30006), self.__language__(30616))
			xbmc.executebuiltin( "Container.Refresh" )
		
	def deleteRefinements(self, params = {}):
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
			self.showMessage(self.__language__(30006), self.__language__(30610))
			xbmc.executebuiltin( "Container.Refresh" )

	#================================== List Item manipulation =========================================	
	# is only used by List Menu
	def addListItem(self, params = {}, item_params = {}):
		get = params.get
		item = item_params.get
		
		if (not item("action")): 
			if (item("login") == "false"):
				self.addFolderListItem(params, item_params)				
			else:
				if (len(self.__settings__.getSetting( "auth" )) > 0):
					self.addFolderListItem(params, item_params)
		else :
			if (item("action") == "settings"):
				if (len(self.__settings__.getSetting( "auth" )) > 0):
					if (item("login") == "true"):
						self.addActionListItem(params, item_params)
				else:
					if (item("login") == "false"):
						self.addActionListItem(params, item_params)
			else:
				self.addActionListItem(params, item_params)
	
	# common function for adding folder items
	def addFolderListItem(self, params = {}, item_params = {}, size = 0):
		get = params.get
		item = item_params.get
		
		icon = "DefaultFolder.png"
		
		if (item("action") == "search_disco"):
			icon = self.getThumbnail("discoball")
		elif (item("action") == "search"):
			icon = self.getThumbnail("search")
		elif (item("show") or get("scraper") == "shows"):
			icon = self.getThumbnail("shows")
		
		thumbnail = item("thumbnail")
		
		cm = self.addContextMenuItems(params, item_params)
		
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
		
		icon = "default"
		if (get("scraper", "").find("trailers") > 0):
			icon = "trailers"
		icon = self.getThumbnail(icon)
		
		listitem=xbmcgui.ListItem(item("Title"), iconImage=icon, thumbnailImage=item("thumbnail") )

		url = '%s?path=%s&action=play_video&videoid=%s' % ( sys.argv[0], item("path"), item("videoid"));
			
		cm = self.addContextMenuItems(params, item_params)
				
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
		
		next = False;
		for result_params in results:
			result = result_params.get
			next = result("next") == "true"
			
			# Make sure folder items don't have next set otherwise they won't get context menu items attached
			result_params["next"] = "false"
			result_params["path"] = get("path")
			result_params["login"] = "true"
			
			if (get("feed") == "subscriptions"):
				result_params["channel"] = result("Title")
				viewmode = ""
				if (get("external")):
					viewmode += "external_" + get("contact") + "_"
					result_params["external"] = "true"
					result_params["contact"] = get("contact")
				viewmode += "view_mode_" + result("Title")
				
				if (self.__settings__.getSetting(viewmode) == "subscriptions_favorites"):
					result_params["feed"] = "subscriptions_favorites"
					result_params["view_mode"] = "subscriptions_uploads"
				elif(self.__settings__.getSetting(viewmode) == "subscriptions_playlists"):
					result_params["feed"] = "subscriptions_playlists"
					result_params["view_mode"] = "subscriptions_playlists"
				else:
					result_params["feed"] = "subscriptions_uploads"  
					result_params["view_mode"] = "subscriptions_favorites"
			
			if (result("playlistId")): 
				result_params["playlist"] = result("playlistId")
				result_params["feed"] = "playlist_root" 
			
			if (get("feed") == "contacts"):
				result_params["thumbnail"] = "user"
				result_params["contact"] = result("Title")
				result_params["options"] = "contact_options"
						
			if (result("playlist") or result("channel")):
				if (result("playlist")):
					if (self.__settings__.getSetting(get("feed") + "_" + result("playlist") + "_thumb")):
						result_params["thumbnail"] = self.__settings__.getSetting(get("feed") + "_" + result("playlist") + "_thumb")
				if (result("channel")):
					if (self.__settings__.getSetting(get("feed") + "_" + result("channel") + "_thumb")):
						result_params["thumbnail"] = self.__settings__.getSetting(get("feed") + "_" + result("channel") + "_thumb")
			
			self.addFolderListItem( params, result_params, listSize + 1)
			
		if next:
			item = {"Title":self.__language__( 30509 ), "thumbnail":"next", "next":"true", "page":str(int(get("page", "0")) + 1)} 
			for k, v in params.items():
				if (k != "thumbnail" and k != "Title" and k != "page"):
					item[k] = v
			
			self.addFolderListItem(params, item, listSize)
		
		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True, cacheToDisc=False )
	
	#parses a video list consisting of a tuple of dictionaries 
	def parseVideoList(self, params, results):
		listSize = len(results)
		get = params.get
		
		next = False
		for result_params in results:
			result_params["path"] = get("path")
			result = result_params.get
			next = result("next") == "true"

			if result("videoid") == "false":
				if self.__dbg__:
					print self.__plugin__ + " parseVideoList, got videoid false"
				continue
									
			self.addVideoListItem( params, result_params, listSize)
		
		if next:
			item = {"Title":self.__language__( 30509 ), "thumbnail":"next", "next":"true", "page":str(int(get("page", "0")) + 1)} 
			for k, v in params.items():
				if ( k != "thumbnail" and k != "Title" and k != "page"):
					item[k] = v
			
			self.addFolderListItem(params, item)
		
		video_view = int(self.__settings__.getSetting("list_view")) <= 1
		if (self.__dbg__):
			print self.__plugin__ + " view mode set to: " + self.__settings__.getSetting("list_view")
		
		if (video_view):
			if (self.__dbg__):
				print self.__plugin__ + " setting view mode"
			xbmc.executebuiltin("Container.SetViewMode(500)")
		
		xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED )
		xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
		xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RATING )
		xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE )
		xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_PROGRAM_COUNT )
		xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
		xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_GENRE )	   
		
		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True, cacheToDisc=True )

		
	#=================================== Tool Box ======================================= 
	# shows a more userfriendly notification
	def showMessage(self, heading, message):
		duration = ([5, 10, 15, 20, 25, 30][int(self.__settings__.getSetting( 'notification_length' ))]) * 1000
		xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( heading, message, duration) )

	# create the full thumbnail path for skins directory
	def getThumbnail( self, title ):
		if (not title):
			title = "DefaultFolder.png"
		
		thumbnail = os.path.join( sys.modules[ "__main__" ].__plugin__, title + ".png" )
		
		if ( not xbmc.skinHasImage( thumbnail ) ):
			thumbnail = os.path.join( self.plugin_thumbnail_path, title + ".png" )
			if ( not os.path.isfile( thumbnail ) ):
				thumbnail = "DefaultFolder.png"	
		
		return thumbnail

	# raise a keyboard for user input
	def getUserInput(self, title = "Input", default="", hidden=False):
		result = None

		# Fix for when this functions is called with default=None
		if not default:
			default = ""
			
		keyboard = xbmc.Keyboard(default, title)
		keyboard.setHiddenInput(hidden)
		keyboard.doModal()
		
		if keyboard.isConfirmed():
			result = keyboard.getText()
		
		return result

	# converts the request url passed on by xbmc to our plugin into a dict  
	def getParameters(self, parameterString):
		commands = {}
		splitCommands = parameterString[parameterString.find('?')+1:].split('&')
		
		for command in splitCommands: 
			if (len(command) > 0):
				splitCommand = command.split('=')
				name = splitCommand[0]
				value = splitCommand[1]
				commands[name] = value
		
		return commands

	# generic function for building the item url filters out many item params to reduce unicode problems
	def buildItemUrl(self, item_params = {}, url = ""):
		for k, v in item_params.items():
			if (k != "path" and k != "thumbnail" and k!= "playlistId" and k!= "next" and k != "content" and k!= "editid"
				and k!= "summary" and k!= "published" and k!="Title"):
				url += k + "=" + v + "&"
		return url

	def addContextMenuItems(self, params = {}, item_params = {}):
		cm = []
		get = params.get
		item = item_params.get

		title = self.makeAscii(item("Title"))
		url_title = urllib.quote_plus(title)
		
		if (item("videoid")): 
			if (self.pr_video_quality):
				cm.append( (self.__language__(30520), "XBMC.PlayMedia(%s?path=%s&action=play_video&quality=1080p&videoid=%s)" % ( sys.argv[0],  item("path"), item("videoid") ) ) )
				cm.append( (self.__language__(30521), "XBMC.PlayMedia(%s?path=%s&action=play_video&quality=720p&videoid=%s)" % ( sys.argv[0],  item("path"), item("videoid") ) ) )
				cm.append( (self.__language__(30522), "XBMC.PlayMedia(%s?path=%s&action=play_video&quality=SD&videoid=%s)" % ( sys.argv[0],  item("path"), item("videoid") ) ) )
			
			cm.append( ( self.__language__(30501), "XBMC.RunPlugin(%s?path=%s&action=download&videoid=%s)" % ( sys.argv[0],  item("path"), item("videoid") ) ) )

			if ( self.__settings__.getSetting( "username" ) != "" and self.__settings__.getSetting( "auth" ) ):
				if ( get("feed") == "favorites" and not get("contact") ):
					cm.append( ( self.__language__( 30506 ), 'XBMC.RunPlugin(%s?path=%s&action=remove_favorite&editid=%s&)' % ( sys.argv[0], item("path"), item("editid") ) ) )
				else:
					cm.append( ( self.__language__( 30503 ), 'XBMC.RunPlugin(%s?path=%s&action=add_favorite&videoid=%s&)' % ( sys.argv[0],  item("path"), item("videoid") ) ) )
				if (get("external") == "true" or (get("feed") != "subscriptions_favorites" and get("feed") != "subscriptions_uploads" and get("feed") != "subscriptions_playlists")):
					cm.append( ( self.__language__( 30512 ) % item("Studio"), 'XBMC.RunPlugin(%s?path=%s&channel=%s&action=add_subscription)' % ( sys.argv[0], item("path"), item("Studio") ) ) )		

			studio = self.makeAscii(item("Studio","Unknown Author"))
			url_studio = urllib.quote_plus(studio)
			
			if (get("feed") != "subscriptions_favorites" and get("feed") != "subscriptions_uploads" and get("feed") != "subscriptions_playlists"):
				cm.append( ( self.__language__( 30516 ) % studio, "XBMC.Container.Update(%s?path=%s&feed=subscriptions_uploads&view_mode=subscriptions_uploads&channel=%s)" % ( sys.argv[0],  get("path"), url_studio ) ) )
			
			if (get("action") == "search_disco"):
				cm.append( ( self.__language__( 30523 ) % title, "XBMC.Container.Update(%s?path=%s&action=search_disco&search=%s)" % ( sys.argv[0],  get("path"), url_title ) ) )
			
			cm.append( ( self.__language__( 30514 ), "XBMC.Container.Update(%s?path=%s&action=search&search=%s)" % ( sys.argv[0],  get("path"), url_title ) ) )
			cm.append( ( self.__language__( 30529 ), "XBMC.Container.Update(%s?path=%s&feed=list_related&videoid=%s)" % ( sys.argv[0],  get("path"), item("videoid") ) ) )
			cm.append( ( self.__language__( 30527 ), "XBMC.ActivateWindow(VideoPlaylist)"))
			cm.append( ( self.__language__( 30504 ), "XBMC.Action(Queue)", ) )
			cm.append( ( self.__language__( 30502 ), "XBMC.Action(Info)", ) )
		elif (item("next","false") == "false"):
			if (item("action") == "search"):
				cm.append( ( self.__language__( 30515 ), 'XBMC.Container.Update(%s?path=%s&action=edit_search&search=%s&)' % ( sys.argv[0], item("path"), item("search") ) ) )
				cm.append( ( self.__language__( 30505 ), 'XBMC.RunPlugin(%s?path=%s&action=refine_user&search=%s&)' % ( sys.argv[0], item("path"), item("search") ) ) )
				cm.append( ( self.__language__( 30508 ), 'XBMC.RunPlugin(%s?path=%s&action=delete_search&delete=%s&)' % ( sys.argv[0], item("path"), item("search") ) ) )
				try:
					searches = eval(self.__settings__.getSetting("stored_searches_author"))
				except :
					searches = {}
				
				if item("Title") in searches:
					cm.append( ( self.__language__( 30500 ), 'XBMC.RunPlugin(%s?path=%s&action=delete_refinements&search=%s&)' % ( sys.argv[0], item("path"), item("search") ) ) )

			if (item("action") == "search_disco" and not get("scraper")):
				cm.append( ( self.__language__( 30524 ), 'XBMC.Container.Update(%s?path=%s&action=edit_disco&search=%s&)' % ( sys.argv[0], item("path"), item("search") ) ) )
				cm.append( ( self.__language__( 30525 ), 'XBMC.RunPlugin(%s?path=%s&action=delete_disco&delete=%s&)' % ( sys.argv[0], item("path"), item("search") ) ) )								

			if (item("view_mode")):
				cm_url = 'XBMC.RunPlugin(%s?path=%s&channel=%s&action=change_subscription_view&view_mode=%s&' % ( sys.argv[0], item("path"), item("channel"), "%s")
				if (item("external")):
					cm_url += "external=true&contact=" + get("contact") + "&"
				cm_url +=")"
			
				if (item("feed") == "subscriptions_favorites"):
					cm.append ( (self.__language__( 30511 ), cm_url % ("subscriptions_uploads")))
					cm.append( (self.__language__( 30528 ), cm_url % ("subscriptions_playlists")))
				elif(item("feed") == "subscriptions_playlists"):
					cm.append( (self.__language__( 30511 ), cm_url % ("subscriptions_uploads"))) 
					cm.append ( (self.__language__( 30510 ), cm_url % ("subscriptions_favorites")))
				elif (item("feed") == "subscriptions_uploads"):
					cm.append ( (self.__language__( 30510 ), cm_url % ("subscriptions_favorites")))
					cm.append( (self.__language__( 30528 ), cm_url % ("subscriptions_playlists")))

			if (item("channel")):
				if ( self.__settings__.getSetting( "username" ) != "" and self.__settings__.getSetting( "auth" ) ):
					if (get("external")):
						cm.append( ( self.__language__( 30512 ) % item("channel"), 'XBMC.RunPlugin(%s?path=%s&channel=%s&action=add_subscription)' % ( sys.argv[0], item("path"), item("channel") ) ) )
					else:
						cm.append( ( self.__language__( 30513 ) % item("channel"), 'XBMC.RunPlugin(%s?path=%s&editid=%s&action=remove_subscription)' % ( sys.argv[0], item("path"), item("editid") ) ) )
					
			if (item("contact")):
				if ( self.__settings__.getSetting( "username" ) != "" and self.__settings__.getSetting( "auth" ) ):
					if (item("external")):
						cm.append( (self.__language__(30026), 'XBMC.RunPlugin(%s?path=%s&action=add_contact&)' % ( sys.argv[0], item("path") ) ) )
					else:
						cm.append( (self.__language__(30025), 'XBMC.RunPlugin(%s?path=%s&action=remove_contact&contact=%s&)' % ( sys.argv[0], item("path"), item("Title") ) ) )
							
			if ( item("feed") == "favorites"  or get("feed") == "playlists" or item("feed") == "uploads" or item("feed") == "newsubscriptions" or (item("action") == "search_disco" and not get("scraper"))):
				cm.append( ( self.__language__( 30507 ), "XBMC.Action(Queue)" ) )
			
			cm.append( ( self.__language__( 30527 ), "XBMC.ActivateWindow(MusicPlaylist)"))
		return cm

	def makeAscii(self, str):
		try:
			return str.encode('ascii')
		except:
			if self.__dbg__:
				print self.__plugin__ + " makeAscii hit except on : " + repr(str)
			s = ""
			for i in str:
				try:
					i.encode("ascii")
				except:
					continue
				else:
					s += i
			return s

	def errorHandling(self, title = "", result = "", status = 500):
		if title == "":
			title = self.__language__(30600)
		if result == "":
			result = self.__language__(30617)
			
		if ( status == 303):
			self.showMessage(title, result)
		elif ( status == 500):
			self.showMessage(title, self.__language__(30606))
		elif ( status != 0):
			self.showMessage(title, self.__language__(30617))
