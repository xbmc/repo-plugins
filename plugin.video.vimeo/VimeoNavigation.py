import sys, urllib
import os
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import VimeoScraperCore
import VimeoCore
		
scraper = VimeoScraperCore.VimeoScraperCore()
core = VimeoCore.VimeoCore();
	
class VimeoNavigation:	 
	__settings__ = sys.modules[ "__main__" ].__settings__
	__language__ = sys.modules[ "__main__" ].__language__
	__plugin__ = sys.modules[ "__main__"].__plugin__	
	__dbg__ = sys.modules[ "__main__" ].__dbg__
	
	plugin_thumbnail_path = os.path.join( __settings__.getAddonInfo('path'), "thumbnails" )
	
	scraper_sorts = (
			 {"Title":__language__(30517), "sort":"plays", "categories":"true"},
			 {"Title":__language__(30518), "sort":"relevant", "categories":"true"},
			 {"Title":__language__(30519), "sort":"comments", "categories":"true"},
			 {"Title":__language__(30520), "sort":"likes", "categories":"true"},
			 {"Title":__language__(30521), "sort":"alphabetic", "categories":"true"},
			 {"Title":__language__(30524), "sort":"featured", "groups":"true", "channels":"true"},
			 {"Title":__language__(30525), "sort":"clips", "groups":"true", "channels":"true"},
			 {"Title":__language__(30526), "sort":"recent", "groups":"true", "channels":"true"},
			 {"Title":__language__(30521), "sort":"name", "groups":"true", "channels":"true"},
			 {"Title":__language__(30527), "sort":"members", "groups":"true"},
			 {"Title":__language__(30528), "sort":"subscribed", "channels":"true"},
			 {"Title":__language__(30523), "sort":"newest", "common":"true"},
			 {"Title":__language__(30522), "sort":"oldest", "common":"true"}			  
			 )
	
	feeds = {};
	feeds['scraper_channels'] = "http://vimeo.com/channels"
	feeds['scraper_groups'] = "http://vimeo.com/groups"
	feeds['scraper_categories'] = "http://vimeo.com/categories"
	
	# we fill the list with category definitions, with labels from the appropriate language file
	#			   Title						 , path							, thumbnail					  ,  login		  ,  source / action
	categories = (
				  {'Title':__language__( 30001 )  ,'path':"/root/explore"		   	, 'thumbnail':"explore"		  	, 'login':"false"  },
				  {'Title':__language__( 30013 )  ,'path':"/root/explore/channels"  , 'thumbnail':"explore"		  	, 'login':"false" , 'scraper':"channels"},
				  {'Title':__language__( 30014 )  ,'path':"/root/explore/groups"	, 'thumbnail':"explore"		  	, 'login':"false" , 'scraper':"groups" },
				  {'Title':__language__( 30015 )  ,'path':"/root/explore/categories", 'thumbnail':"explore"		  	, 'login':"false" , 'scraper':"categories" },
				  {'Title':__language__( 30016 )  ,'path':"/root/explore/hd"		, 'thumbnail':"explore"		  	, 'login':"false" , 'channel':"hd" },
				  {'Title':__language__( 30017 )  ,'path':"/root/explore/staffpicks", 'thumbnail':"explore"		  	, 'login':"false" , 'channel':"staffpicks" },
				  {'Title':__language__( 30002 )  ,'path':"/root/my_likes"		  	, 'thumbnail':"favorites"		, 'login':"true"  , 'api':"my_likes" },
				  {'Title':__language__( 30012 )  ,'path':"/root/my_contacts"	   	, 'thumbnail':"contacts"		, 'login':"true"  , 'api':"my_contacts" },
				  {'Title':__language__( 30009 )  ,'path':"/root/my_albums"		 	, 'thumbnail':"playlists"		, 'login':"true"  , 'api':"my_albums" },
				  {'Title':__language__( 30031 )  ,'path':'/root/my_watch_later'	, 'thumbnail':"watch_later"		, 'login':"true"  , 'api':"my_watch_later" },
				  {'Title':__language__( 30010 )  ,'path':"/root/my_groups"		 	, 'thumbnail':"network"		  	, 'login':"true"  , 'api':"my_groups" },
				  {'Title':__language__( 30003 )  ,'path':"/root/subscriptions"	 	, 'thumbnail':"subscriptions"	, 'login':"true"  , 'api':"my_channels" },
				  {'Title':__language__( 30004 )  ,'path':"/root/subscriptions/new" , 'thumbnail':"newsubscriptions", 'login':"true"  , 'api':"my_newsubscriptions"},
				  {'Title':__language__( 30005 )  ,'path':"/root/my_videos"		 	, 'thumbnail':"uploads"		  	, 'login':"true"  , 'api':"my_videos" },
				  {'Title':__language__( 30032 )  ,'path':"/root/downloads"			, 'thumbnail':"downloads"		, 'login':"false" , 'feed':"downloads" },
				  {'Title':__language__( 30006 )  ,'path':"/root/search"			, 'thumbnail':"search"		   	, 'login':"false" , 'feed':"searches" },
				  {'Title':__language__( 30007 )  ,'path':"/root/search/new"		, 'thumbnail':"search"		   	, 'login':"false" , 'action':"search" },
				  {'Title':__language__( 30008 )  ,'path':"/root/playbyid"		  	, 'thumbnail':"playbyid"		, 'login':"false" , 'action':"playbyid" },
				  {'Title':__language__( 30027 )  ,'path':"/root/login"			 	, 'thumbnail':"login"			, 'login':"false" , 'action':"settings" },
				  {'Title':__language__( 30028 )  ,'path':"/root/settings"		  	, 'thumbnail':"settings"		, 'login':"true"  , 'action':"settings" }
				  )
	
	#==================================== Main Entry Points===========================================
	def listMenu(self, params = {}):
		get = params.get

		if (get("channel") or get("group") or get("album")):
			self.listVideoFeed(params)
			return
					
		if (get("contact") and not get("external")):
			self.listOptionFolder(params)
			
		if (get("scraper")):
			self.scrapeVideos(params)
			return
		
		if (get("login") == "true"):
			
			if ( get("api") and get("api") != "my_likes" and get("api") != "my_watch_later"  and get("api") != "my_videos" and get("api") != "my_newsubscriptions"):
				self.listUserFolder(params)
			elif ( get("api") == "my_likes" or get("api") == "my_watch_later" or get("api") == "my_videos" or get("api") == "my_newsubscriptions"):
				self.listUserFeed(params)
			elif (get("contact")):
				self.listOptionFolder(params)
			return

		if (get("feed")):
			if (get("feed") == "searches"):
				self.listStoredSearches(params)
			return
		
		path = get("path", "/root")
		size = len(self.categories);
		
		for category in self.categories:
			cat_get = category.get 
			if (cat_get("path").find(path +"/") > -1 ):
				if (cat_get("path").rfind("/") <= len(path +"/")):
					setting = self.__settings__.getSetting( cat_get("path").replace("/root/", "") )
					
					if not setting or setting == "true":
						if (get("feed") == "downloads"):
							if (self.__settings__.getSetting("downloadPath")):
								self.addListItem(params, category)
						else:
							self.addListItem(params, category)
		
		video_view = self.__settings__.getSetting("list_view") == "1"
		if (self.__dbg__):
			print self.__plugin__ + " view mode: " + self.__settings__.getSetting("list_view")
				
		if (video_view):
			if (self.__dbg__):
				print self.__plugin__ + " setting view mode"
			xbmc.executebuiltin("Container.SetViewMode(500)")
		
		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True, cacheToDisc=True )

	def listVideoFeed(self, params = {}):
		get = params.get
		(results, status) = core.listVideoFeed(params)		
		self.parseVideoList(get("path"), params, results)
		return
			
	def executeAction(self, params = {}):
		get = params.get
		if (get("action") == "playbyid"):
			self.playVideoById(params)
		if (get("action") == "play_video"):
			self.playVideo(params)
		if (get("action") == "search"):
			self.search(params)
		if (get("action") == "delete_search"):
			self.deleteSearch(params)
		if (get("action") == "edit_search"):
			self.editSearch(params)
		if (get("action") == "remove_watch_later"):
			self.removeWatchLater(params)
		if (get("action") == "settings"):
			self.login(params)
		if (get("action") == "remove_favorite" or get("action") == "add_favorite"):
			self.setLike(params)
		if (get("action") == "remove_contact" or get("action") == "add_contact"):
			self.updateContact(params)
		if (get("action") == "join_group" or get("action") == "leave_group"):
			self.updateGroup(params)
		if (get("action") == "remove_subscription" or get("action") == "add_subscription"):
			self.updateSubscription(params)
		if (get("action") == "change_scraper_sort"):
			self.changeScraperSorting(params)
		if (get("action") == "download"):
			self.downloadVideo(params)

	def listOptionFolder(self, params = {}):
		get = params.get
		if ( get('login') == "true" and self.__settings__.getSetting( "user_email" ) != "" ):
			auth = self.__settings__.getSetting( "userid" )
			if ( not auth ) :
				self.login()
				auth = self.__settings__.getSetting( "userid" )

		item_favorites = {'Title':self.__language__( 30020 ), 'path':get("path"), 'external':"true", 'login':"true", 'thumbnail':"favorites", 'api':"my_likes", "contact":get("contact")}
		self.addFolderListItem(params, item_favorites, 1)
		item_subscriptions = {'Title':self.__language__( 30021 ), 'path':get("path"), 'external':"true", 'login':"true", 'thumbnail':"subscriptions", 'api':"my_channels", "contact":get("contact")}
		self.addFolderListItem(params, item_subscriptions, 3)
		item_favorites = {'Title':self.__language__( 30019 ), 'path':get("path"), 'external':"true", 'login':"true", 'thumbnail':"network", 'api':"my_groups", "contact":get("contact")}
		self.addFolderListItem(params, item_favorites, 1)
		item_playlists = {'Title':self.__language__( 30018 ), 'path':get("path"), 'external':"true", 'login':"true", 'thumbnail':"playlists", 'api':"my_albums", "contact":get("contact")}
		self.addFolderListItem(params, item_playlists, 2)
		item_uploads = {'Title':self.__language__( 30022 ), 'path':get("path"), 'external':"true", 'login':"true", 'thumbnail':"uploads", 'api':"my_videos", "contact":get("contact") }
		self.addFolderListItem(params, item_uploads, 4)
		
		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True, cacheToDisc=False)
	
	def listUserFolder(self, params = {}):
		get = params.get
		status = 500
		if ( get('login') == "true" and self.__settings__.getSetting( "user_email" ) != "" ):
			auth = self.__settings__.getSetting( "userid" )
			if ( not auth ) :
				self.login()
				auth = self.__settings__.getSetting( "userid" )
		
		(result, status) = core.getUserData(params)
		
		if status != 200:
			feed_label = ""
			for category in self.categories:
				cat_get = category.get
				if (cat_get("api") == get("api")):
					feed_label = cat_get("Title")
					break
				
				if (feed_label != ""):
					self.errorHandling(feed_label, result, status)
				else:
					self.errorHandling(get("feed"), result, status)
				return False

		# Disable add contacts
		#if ( get("api") == "my_contacts"):
		#	item_add_user = {'Title':self.__language__( 30024 ), 'path':get("path"), 'login':"true", 'thumbnail':"add_user", 'action':"add_contact"}
		#	self.addFolderListItem(params, item_add_user,  1)
						
		if ( get('api') == 'my_channels' ) :
			item = {"Title":self.__language__( 30004 ), "path":"/root/subscriptions/new", "thumbnail":"newsubscriptions", "login":"true", "api":"my_newsubscriptions"}
			if (get("contact")):
				item["contact"] = get("contact")
			
			self.addFolderListItem(params, item)
							
		self.parseFolderList(get("path"), params, result)
								
	def listUserFeed(self, params = {}):
		if self.__dbg__:
			print self.__plugin__ + " listUserFolderFeeds"
		
		get = params.get
		if ( get('login') == "true" and self.__settings__.getSetting( "user_email" ) != "" ):
			auth = self.__settings__.getSetting( "userid" )
			if ( not auth ) :
				self.login()
				auth = self.__settings__.getSetting( "userid" )
		
		(result, status) = core.getUserData(params)
		
		if status != 200:
			feed_label = ""
				
			for category in self.categories:
				cat_get = category.get
				if (cat_get("api") == get("api")):
					feed_label = cat_get("Title")
					break
				
			if (feed_label != ""):
				self.errorHandling(feed_label, result, status)
			else:
				self.errorHandling(get("feed"), result, status)
			return False
		
		self.parseVideoList(get("path"), params, result);
			
	def login(self, params = {}):
		self.__settings__.openSettings()
		(result, status ) = core.login()
		self.showMessage( self.__language__( 30029 ), result);
		xbmc.executebuiltin( "Container.Refresh" )

	def listStoredSearches(self, params = {}):
		get = params.get
		search_item = {'Title':self.__language__( 30007 ),'path':"/root/search/new", 'thumbnail':"search", 'action':"search" }
		self.addActionListItem(params, search_item)
		try:
			searches = eval(self.__settings__.getSetting("stored_searches"))
		except:
			searches = []
		
		for search in searches:
			item = {}
			item["Title"] = search
			item["search"] = urllib.quote_plus(search)
			item["action"] = "search"
			item["path"] = get("path")
			item["thumbnail"] = self.__settings__.getSetting("search_" + search + "_thumb") 
			self.addFolderListItem(params, item, len(searches))
			
		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True, cacheToDisc=False )
		return True

	def scrapeVideos(self, params):
		get = params.get

		if ("scraper_" + get("scraper") in self.feeds):
			feed = self.feeds["scraper_" + get("scraper")]

			( results, status ) = scraper.scrape(feed, params)
			
			if ( results ):
				if (get("scraper") == "categories" and get("category")):
					self.parseVideoList(get("path"), params, results)
				elif (get("scraper") == "my_likes" or get("scraper") == "my_videos" or get("scraper") == "my_album"):
					self.parseVideoList(get("path"), params, results)
				else:
					self.parseFolderList(get("path"), params, results)
					
			elif ( status == 303):
				self.showMessage(self.__language__(30600), results)
			else:
				self.showMessage(self.__language__(30600), self.__language__(30606))

	#================================== Plugin Actions =========================================

	def playVideoById(self, params = {}):
		result = self.getUserInput('VideoID', '')
		params["videoid"] = result 
		if (result):
			self.playVideo(params);
		
	def playVideo(self, params = {}):
		get = params.get
		(video, status) = core.construct_video_url(get('videoid'));
		if status != 200:
			self.errorHandling(self.__language__(30603), video, status)
			return False

		if ( 'swf_config' in video ):
			video['video_url'] += " swfurl=%s swfvfy=1" % video['swf_config']

		listitem=xbmcgui.ListItem(label=video['Title'], iconImage=video['thumbnail'], thumbnailImage=video['thumbnail'], path=video['video_url']);
		listitem.setInfo(type='Video', infoLabels=video)
		
		if self.__dbg__:
			print self.__plugin__ + " - Playing video: " + self.makeAscii(video['Title']) + " - " + get('videoid') + " - " + video['video_url']

		xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=listitem)
		self.__settings__.setSetting( "vidstatus-" + get('videoid'), "7" )
	
	
	def downloadVideo(self, params = {}):
		get = params.get
		if (get("videoid")):
			path = self.__settings__.getSetting( "downloadPath" )
			if (not path):
				self.showMessage(self.__language__(30600), self.__language__(30611))
				self.__settings__.openSettings()
				path = self.__settings__.getSetting( "downloadPath" )

			( video, status )  = core.construct_video_url(get("videoid"))

			if status != 200:
				if self.__dbg__:
					print self.__plugin__ + " downloadVideo got error from construct_video_url: [%s] %s" % ( status, video)
				self.errorHandling(self.__language__( 30501 ), video, status)
				return False

			item = video.get
			
			self.showMessage(self.__language__(30612), item("Title", "Unknown Title"))

			( video, status ) = core.downloadVideo(video)

			if status == 200:
				self.showMessage(self.__language__( 30604 ), video['Title'])

	def setLike(self, params = {}):
		get = params.get
		
		if (get("videoid")):
			(message, status) = core.setLike(params)
			if status != 200:
				self.errorHandling(self.__language__(30020), message, status)
				return False
			
			if (get("action") == "remove_favorite"):
				xbmc.executebuiltin( "Container.Refresh" )
			return True			
		
	def changeScraperSorting(self, params = {}):
		get = params.get
		if (get("category") and get("scraper") and get("sort")):
			self.__settings__.setSetting("scraper_" + get("scraper") + "_sort_" + get("category"), get("sort"), )
			print self.__plugin__ + "Changed Scraper List Sorting"
		
		xbmc.executebuiltin( "Container.Refresh" )
		return
	
	def updateContact(self, params = {}):
		get = params.get

		if (not get("contact")):
			params["contact"] = self.getUserInput('Contact', '')
			
		if (get("contact")):
			(result, status) = core.updateContact(params)
			if status != 200:
				self.errorHandling(self.__language__(30029), result, status)
				return False

			self.showMessage(self.__language__(30614), get("contact"))
			xbmc.executebuiltin( "Container.Refresh" )

	def updateGroup(self, params = {}):
		get = params.get
			
		if (get("group")):
			(result, status) = core.updateGroup(params)
			if status != 200:
				self.errorHandling(self.__language__(30029), result, status)
				return False
			if (get("action") == "leave_group"):
				xbmc.executebuiltin( "Container.Refresh" )
		return True
				
	def updateSubscription(self, params = {}):
		get = params.get
		if (get("channel")):
			(message, status) = core.updateSubscription(params)
			if status != 200:
				self.errorHandling(self.__language__(30021), message, status)
				return False
			else:
				if (get("action") == "remove_subscription"):
					xbmc.executebuiltin( "Container.Refresh" )
		return True
	
	def removeWatchLater(self, params = {}):
		get = params.get
		
		if (get("videoid")):
			(result, status) = core.removeWatchLater(params)
			if status != 200:
				return False
			else:
				xbmc.executebuiltin( "Container.Refresh" )
		
		return True
	#================================== Searching =========================================
	def search(self, params = {}):
		get = params.get
		if (get("search")):
			query = get("search")
			query = urllib.unquote_plus(query)
			self.saveSearchQuery(query, query)
		else :
			query = self.getUserInput('Search', '')
			if (query):
				self.saveSearchQuery(query,query)
				params["search"] = query
		
		if (query):
			( result, status ) = core.search(query, get("page", "0"));
			if status != 200:
				self.errorHandling(self.__language__(30006), result, status)
				return False
			
			thumbnail = result[0].get('thumbnail')
			
			if (thumbnail and query):
				self.__settings__.setSetting("search_" + query + "_thumb", thumbnail)
				
			self.parseVideoList(get("path"), params, result)
			
	def deleteSearch(self, params = {}):
		get = params.get
		query = get("delete")
		query = urllib.unquote_plus(query)
		try:
			searches = eval(self.__settings__.getSetting("stored_searches"))
		except:
			searches = []
			
		for count, search in enumerate(searches):
			if (search.lower() == query.lower()):
				del(searches[count])
				break
		
		self.__settings__.setSetting("stored_searches", repr(searches))
		xbmc.executebuiltin( "Container.Refresh" )
		
	def saveSearchQuery(self, old_query, new_query):
		old_query = urllib.unquote_plus(old_query)
		new_query = urllib.unquote_plus(new_query)
		try:
			searches = eval(self.__settings__.getSetting("stored_searches"))
		except:
			searches = []
		
		for count, search in enumerate(searches):
			if (search.lower() == old_query.lower()):
				del(searches[count])
				break

		searchCount = ( 10, 20, 30, 40, )[ int( self.__settings__.getSetting( "saved_searches" ) ) ]
		searches = [new_query] + searches[:searchCount]
		self.__settings__.setSetting("stored_searches", repr(searches))
	
	def editSearch(self, params = {}):
		get = params.get
		if (get("search")):
			old_query = urllib.unquote_plus(get("search"))
			new_query = self.getUserInput('Search', old_query)
			self.saveSearchQuery(old_query, new_query)
			params["search"] = new_query
			self.search(params)
	
	#================================== List Item manipulation =========================================	
	# is only used by List Menu
	def addListItem(self, params = {}, item_params = {}):
		get = params.get
		item = item_params.get
		
		if (not item("action")):
			if (item("login") == "false"):
				self.addFolderListItem(params, item_params)				
			else:			 
				if (len(self.__settings__.getSetting( "userid" )) > 0):
					self.addFolderListItem(params, item_params)
		else :
			if (item("action") == "settings"):
				if (len(self.__settings__.getSetting( "userid" )) > 0):
					if (item("login") == "true"):
						self.addActionListItem(params, item_params)
				else:
					if (item("login") == "false"):
						self.addActionListItem(params, item_params)
			else :
				self.addActionListItem(params, item_params)
	
	# common function for adding folder items
	def addFolderListItem(self, params = {}, item_params = {}, size = 0):		
		get = params.get
		item = item_params.get
		
		icon = "DefaultFolder.png"
		if (get("scraper")):		
			icon = "default"
			icon = self.getThumbnail(icon)
		
		thumbnail = item("thumbnail", "default")
		
		cm = self.addContextMenuItems(params, item_params)			
		
		if (thumbnail.find("http://") == -1):	
			thumbnail = self.getThumbnail(thumbnail)

		listitem=xbmcgui.ListItem( item("Title"), iconImage=icon, thumbnailImage=thumbnail )
		url = '%s?path=%s&' % ( sys.argv[0], item("path") )
		
		url += self.buildItemUrl(item_params)	
		
		if len(cm) > 0:
			listitem.addContextMenuItems( cm, replaceItems=True )
		listitem.setProperty( "Folder", "true" )
		
		if (item("feed") == "downloads"):
			url = self.__settings__.getSetting("downloadPath")
		xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=True, totalItems=size)
	
	# common function for adding action items
	def addActionListItem(self, params = {}, item_params = {}, size = 0):
		get = params.get
		item = item_params.get
		folder = False
		icon = "DefaultFolder.png"
		
		thumbnail = self.getThumbnail(item("thumbnail"))
		listitem=xbmcgui.ListItem( item("Title"), iconImage=icon, thumbnailImage=thumbnail )
		
		if (item("action") == "search" or item("action") == "settings"):
			folder = True
		else:
			listitem.setProperty('IsPlayable', 'true');
			
		url = '%s?path=%s&' % ( sys.argv[0], item("path") )
		url += 'action=' + item("action") + '&'
			
		xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=folder, totalItems=size)
	
	# common function for adding video items
	def addVideoListItem(self, params = {}, item_params = {}, listSize = 0):
		get = params.get
		item = item_params.get
		
		icon = "default"
		icon = self.getThumbnail(icon)
		
		listitem=xbmcgui.ListItem(item("Title"), iconImage=icon, thumbnailImage=item("thumbnail") )

		url = '%s?path=%s&action=play_video&videoid=%s' % ( sys.argv[0], item("path"), item("videoid"));
		cm = self.addContextMenuItems(params, item_params)

		listitem.addContextMenuItems( cm, replaceItems=True )
		
		listitem.setProperty( "Video", "true" )
		listitem.setProperty( "IsPlayable", "true");
		listitem.setInfo(type='Video', infoLabels=item_params)
		
		xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=False, totalItems=listSize + 1)
		
	#==================================== Core Output Parsing Functions ===========================================
	#parses a folder list consisting of a tuple of dictionaries
	def parseFolderList(self, path, params, results):
		listSize = len(results)
		get = params.get
		
		next = False;
		for result_params in results:
			result = result_params.get
			next = result("next") == "true"
			
			if (get("scraper") and not (get("group") or get("channel") or get("category"))):
				if (result("category")):
					if (self.__settings__.getSetting("scraper_" + get("scraper") + "_sort_" + result("category"))):
						result_params["sort"] = self.__settings__.getSetting("scraper_" + get("scraper") + "_sort_" + result("category"))
						
			if (get("api") == "my_contacts"):
				result_params["feed"] = "contact_option_list"
							
			result_params["path"] = path
						
			self.addFolderListItem( params, result_params, listSize + 1)
			
		if next:
			item = {"Title":self.__language__( 30509 ), "thumbnail":"next", "page":str(int(get("page", "0")) + 1)} 
			for k, v in params.items():
				if ( k != "thumbnail" and k != "Title" and k != "page"):
					item[k] = v
			
			self.addFolderListItem(params, item, listSize)
		
		cache = False
		
		if (get("scraper")):
			cache = True
		
		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True, cacheToDisc=cache )
	
	#parses a video list consisting of a tuple of dictionaries 
	def parseVideoList(self, path, params, results):
		listSize = len(results)
		get = params.get
		
		next = False
		for result_params in results:
			result = result_params.get
			item_params = {}
			next = result("next") == "true"
			
			if ( result('reasonCode') ):
				if result('reasonCode') == 'requesterRegion':
					continue;
			
			result_params["path"] = path

			self.addVideoListItem( params, result_params, listSize)
		
		if next:
			item = {"Title":self.__language__( 30509 ), "thumbnail":"next", "page":str(int(get("page", "0")) + 1)} 
			for k, v in params.items():
				if ( k != "thumbnail" and k != "Title" and k != "page"):
					item[k] = v
			
			self.addFolderListItem(params, item)
		
		video_view = self.__settings__.getSetting("list_view") == "1"
		if (self.__dbg__):
			print self.__plugin__ + " view mode: " + self.__settings__.getSetting("list_view")
		
		if (not video_view):
			video_view = self.__settings__.getSetting("list_view") == "0"
		
		if (video_view):
			if (self.__dbg__):
				print self.__plugin__ + " setting view mode"
			xbmc.executebuiltin("Container.SetViewMode(500)")
		
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
	def getUserInput(self, title, default="", hidden=False):
		result = None

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
	
	def addContextMenuItems(self, params = {}, item_params = {}):
		cm = []
		get = params.get
		item = item_params.get

		title = self.makeAscii(item("Title", "Unknown Title"))		
		if (item("videoid")):
			if (self.__settings__.getSetting( "userid" )):	
				if ( get("api") == "my_likes" and not get("contact") ):
					cm.append( ( self.__language__( 30504 ) % title, 'XBMC.RunPlugin(%s?path=%s&action=remove_favorite&videoid=%s&)' % ( sys.argv[0], get("path"), item("videoid") ) ) )
				else:
					cm.append( ( self.__language__( 30503 ) % title, 'XBMC.RunPlugin(%s?path=%s&action=add_favorite&videoid=%s&)' % ( sys.argv[0],  get("path"), item("videoid") ) ) )
			
			if (get("api") == "my_watch_later"):
				cm.append( (self.__language__(30529) , "XBMC.RunPlugin(%s?path=%s&action=remove_watch_later&videoid=%s)" % ( sys.argv[0],  get("path"), item("videoid") ) ) )
			else:
				cm.append( (self.__language__(30530) , "XBMC.RunPlugin(%s?path=%s&action=add_watch_later&videoid=%s)" % ( sys.argv[0],  get("path"), item("videoid") ) ) )
			
			cm.append( ( self.__language__( 30500 ), "XBMC.RunPlugin(%s?path=%s&action=download&videoid=%s)" % ( sys.argv[0],  get("path"), item("videoid") ) ) )
			cm.append( ( self.__language__( 30507 ), "XBMC.Container.Update(%s?path=%s&action=search&search=%s)" % ( sys.argv[0],  get("path"), urllib.quote_plus( title ) ) ) )
			cm.append( ( self.__language__( 30502 ), "XBMC.Action(Queue)", ) )
			cm.append( ( self.__language__( 30501 ), "XBMC.Action(Info)", ) )
		elif (not item("next")):
			if (get("scraper") and not (get("group") or get("channel") or get("category"))):
				default = "newest"
				if (get("scraper") == "groups"):
					default = "members"
				if (get("scraper") == "channels"):
					default = "subscribed"
				if (get("scraper") == "categories"):
					default = "relevant"
				
				if (item("category")):
					if (self.__settings__.getSetting("scraper_" + get("scraper") + "_sort_" + item("category"))):
						default = self.__settings__.getSetting("scraper_" + get("scraper") + "_sort_" + item("category") )
						
				cm_url = 'XBMC.RunPlugin(%s?path=%s&action=change_scraper_sort&scraper=%s&category=%s&sort=' % ( sys.argv[0], item("path"), get("scraper"), item("category"))
				for sort in self.scraper_sorts:
					sget = sort.get
					if (sget("sort") != default and (sget(get("scraper")) or sget("common"))):
						cm.append( ( sget("Title"), cm_url + sget("sort") + "&)" ) ) 
						
			if (item("channel") and self.__settings__.getSetting( "userid" )):
				if (item("external") or get("scraper")):
					cm.append( ( self.__language__( 30512 ) % title, 'XBMC.RunPlugin(%s?path=%s&channel=%s&action=add_subscription)' % ( sys.argv[0], get("path"), item("channel") ) ) )
				else:
					cm.append( ( self.__language__( 30513 ) % title, 'XBMC.RunPlugin(%s?path=%s&channel=%s&action=remove_subscription)' % ( sys.argv[0], get("path"), item("channel") ) ) )

			if (item("group") and self.__settings__.getSetting( "userid" )):
				if (item("external") or get("scraper")):
					cm.append( ( self.__language__( 30510 ) % title, 'XBMC.RunPlugin(%s?path=%s&group=%s&action=join_group)' % ( sys.argv[0], get("path"), item("group") ) ) )
				else:
					cm.append( ( self.__language__( 30511 ) % title, 'XBMC.RunPlugin(%s?path=%s&group=%s&action=leave_group)' % ( sys.argv[0], get("path"), item("group") ) ) )
			
			if ( item("api") == "my_likes"  or item("album") or item("api") == "my_videos" ):
				cm.append( ( self.__language__( 30514 ), "XBMC.Action(Queue)" ) )
			
			if (item("search")):
				cm.append( ( self.__language__( 30508 ), 'XBMC.RunPlugin(%s?path=%s&action=delete_search&delete=%s&)' % ( sys.argv[0], item("path"), item("search") ) ) )
				cm.append( ( self.__language__( 30506 ), 'XBMC.Container.Update(%s?path=%s&action=edit_search&search=%s&)' % ( sys.argv[0], item("path"), item("search") ) ) )
		
		return cm
	
	def buildItemUrl(self, item_params = {}, url = ""):
		for k, v in item_params.items():
			if (k != "path" and k != "thumbnail" and k!= "playlistId" and k!= "next" and k != "content" and k!= "editurl"
				and k!= "summary" and k!= "published" and k!= "Description" and k!="Title"):	 
				url += k + "=" + v + "&"
		return url
	
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
		else:
			self.showMessage(title, self.__language__(30617))