'''
   Vimeo plugin for XBMC
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
	
class VimeoNavigation:	 

	def __init__(self):
		self.scraper = sys.modules[ "__main__" ].scraper
		self.utils = sys.modules[ "__main__" ].utils
		self.core = sys.modules["__main__"].core
		self.login = sys.modules["__main__"].login
		
		self.xbmc = sys.modules["__main__"].xbmc
		self.xbmcgui = sys.modules["__main__"].xbmcgui
		self.xbmcplugin = sys.modules["__main__"].xbmcplugin

		self.settings = sys.modules[ "__main__" ].settings
		self.language = sys.modules[ "__main__" ].language
		self.plugin = sys.modules[ "__main__"].plugin	
		self.dbg = sys.modules[ "__main__" ].dbg
		
		self.plugin_thumbnail_path = os.path.join( self.settings.getAddonInfo('path'), "thumbnails" )
		
		self.scraper_sorts = (
			{"Title":self.language(30517), "sort":"plays", "categories":"true"},
			{"Title":self.language(30518), "sort":"relevant", "categories":"true"},
			{"Title":self.language(30519), "sort":"comments", "categories":"true"},
			{"Title":self.language(30520), "sort":"likes", "categories":"true"},
			{"Title":self.language(30521), "sort":"alphabetic", "categories":"true"},
			{"Title":self.language(30524), "sort":"featured", "groups":"true", "channels":"true"},
			{"Title":self.language(30525), "sort":"clips", "groups":"true", "channels":"true"},
			{"Title":self.language(30526), "sort":"recent", "groups":"true", "channels":"true"},
			{"Title":self.language(30521), "sort":"name", "groups":"true", "channels":"true"},
			{"Title":self.language(30527), "sort":"members", "groups":"true"},
			{"Title":self.language(30528), "sort":"subscribed", "channels":"true"},
			{"Title":self.language(30523), "sort":"newest", "common":"true"},
			{"Title":self.language(30522), "sort":"oldest", "common":"true"}			  
			)
	
		self.feeds = {};
		self.feeds['scraper_channels'] = "http://vimeo.com/channels"
		self.feeds['scraper_groups'] = "http://vimeo.com/groups"
		self.feeds['scraper_categories'] = "http://vimeo.com/categories"
	
		# we fill the list with category definitions, with labels from the appropriate language file
		#			   Title						 , path							, thumbnail					  ,  login		  ,  source / action
		self.categories = (
			{'Title':self.language( 30001 )  ,'path':"/root/explore"		   	, 'thumbnail':"explore"		  	, 'login':"false"  },
			{'Title':self.language( 30013 )  ,'path':"/root/explore/channels"  , 'thumbnail':"explore"		  	, 'login':"false" , 'scraper':"channels"},
			{'Title':self.language( 30014 )  ,'path':"/root/explore/groups"	, 'thumbnail':"explore"		  	, 'login':"false" , 'scraper':"groups" },
			{'Title':self.language( 30015 )  ,'path':"/root/explore/categories", 'thumbnail':"explore"		  	, 'login':"false" , 'scraper':"categories" },
			{'Title':self.language( 30016 )  ,'path':"/root/explore/hd"		, 'thumbnail':"explore"		  	, 'login':"false" , 'channel':"hd" },
			{'Title':self.language( 30017 )  ,'path':"/root/explore/staffpicks", 'thumbnail':"explore"		  	, 'login':"false" , 'channel':"staffpicks" },
			{'Title':self.language( 30002 )  ,'path':"/root/my_likes"		  	, 'thumbnail':"favorites"		, 'login':"true"  , 'api':"my_likes" },
			{'Title':self.language( 30012 )  ,'path':"/root/my_contacts"	   	, 'thumbnail':"contacts"		, 'login':"true"  , 'api':"my_contacts" },
			{'Title':self.language( 30009 )  ,'path':"/root/my_albums"		 	, 'thumbnail':"playlists"		, 'login':"true"  , 'api':"my_albums" },
			{'Title':self.language( 30031 )  ,'path':'/root/my_watch_later'	, 'thumbnail':"watch_later"		, 'login':"true"  , 'api':"my_watch_later" },
			{'Title':self.language( 30010 )  ,'path':"/root/my_groups"		 	, 'thumbnail':"network"		  	, 'login':"true"  , 'api':"my_groups" },
			{'Title':self.language( 30003 )  ,'path':"/root/subscriptions"	 	, 'thumbnail':"subscriptions"	, 'login':"true"  , 'api':"my_channels" },
			{'Title':self.language( 30004 )  ,'path':"/root/subscriptions/new" , 'thumbnail':"newsubscriptions", 'login':"true"  , 'api':"my_newsubscriptions"},
			{'Title':self.language( 30005 )  ,'path':"/root/my_videos"		 	, 'thumbnail':"uploads"		  	, 'login':"true"  , 'api':"my_videos" },
			{'Title':self.language( 30032 )  ,'path':"/root/downloads"			, 'thumbnail':"downloads"		, 'login':"false" , 'feed':"downloads" },
			{'Title':self.language( 30006 )  ,'path':"/root/search"			, 'thumbnail':"search"		   	, 'login':"false" , 'feed':"searches" },
			{'Title':self.language( 30007 )  ,'path':"/root/search/new"		, 'thumbnail':"search"		   	, 'login':"false" , 'action':"search" },
			{'Title':self.language( 30008 )  ,'path':"/root/playbyid"		  	, 'thumbnail':"playbyid"		, 'login':"false" , 'action':"playbyid" },
			{'Title':self.language( 30027 )  ,'path':"/root/login"			 	, 'thumbnail':"login"			, 'login':"false" , 'action':"settings" },
			{'Title':self.language( 30028 )  ,'path':"/root/settings"		  	, 'thumbnail':"settings"		, 'login':"true"  , 'action':"settings" }
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
					setting = self.settings.getSetting( cat_get("path").replace("/root/", "") )
					
					if not setting or setting == "true":
						if (get("feed") == "downloads"):
							if (self.settings.getSetting("downloadPath")):
								self.addListItem(params, category)
						else:
							self.addListItem(params, category)
		
		video_view = self.settings.getSetting("list_view") == "1"
		if (self.dbg):
			print self.plugin + " view mode: " + self.settings.getSetting("list_view")
				
		if (video_view):
			if (self.dbg):
				print self.plugin + " setting view mode"
			self.xbmc.executebuiltin("Container.SetViewMode(500)")
		
		self.xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True, cacheToDisc=True )

	def listVideoFeed(self, params = {}):
		get = params.get
		(results, status) = self.core.listVideoFeed(params)		
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
			self.login.login(params)
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
		if ( get('login') == "true" and self.settings.getSetting( "user_email" ) != "" ):
			auth = self.settings.getSetting( "userid" )
			if ( not auth ) :
				self.login()
				auth = self.settings.getSetting( "userid" )

		item_favorites = {'Title':self.language( 30020 ), 'path':get("path"), 'external':"true", 'login':"true", 'thumbnail':"favorites", 'api':"my_likes", "contact":get("contact")}
		self.addFolderListItem(params, item_favorites, 1)
		item_subscriptions = {'Title':self.language( 30021 ), 'path':get("path"), 'external':"true", 'login':"true", 'thumbnail':"subscriptions", 'api':"my_channels", "contact":get("contact")}
		self.addFolderListItem(params, item_subscriptions, 3)
		item_favorites = {'Title':self.language( 30019 ), 'path':get("path"), 'external':"true", 'login':"true", 'thumbnail':"network", 'api':"my_groups", "contact":get("contact")}
		self.addFolderListItem(params, item_favorites, 1)
		item_playlists = {'Title':self.language( 30018 ), 'path':get("path"), 'external':"true", 'login':"true", 'thumbnail':"playlists", 'api':"my_albums", "contact":get("contact")}
		self.addFolderListItem(params, item_playlists, 2)
		item_uploads = {'Title':self.language( 30022 ), 'path':get("path"), 'external':"true", 'login':"true", 'thumbnail':"uploads", 'api':"my_videos", "contact":get("contact") }
		self.addFolderListItem(params, item_uploads, 4)
		
		self.xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True, cacheToDisc=False)
	
	def listUserFolder(self, params = {}):
		get = params.get
		status = 500
		if ( get('login') == "true" and self.settings.getSetting( "user_email" ) != "" ):
			auth = self.settings.getSetting( "userid" )
			if ( not auth ) :
				self.login()
				auth = self.settings.getSetting( "userid" )
		
		(result, status) = self.core.getUserData(params)
		
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
		#	item_add_user = {'Title':self.language( 30024 ), 'path':get("path"), 'login':"true", 'thumbnail':"add_user", 'action':"add_contact"}
		#	self.addFolderListItem(params, item_add_user,  1)
						
		if ( get('api') == 'my_channels' ) :
			item = {"Title":self.language( 30004 ), "path":"/root/subscriptions/new", "thumbnail":"newsubscriptions", "login":"true", "api":"my_newsubscriptions"}
			if (get("contact")):
				item["contact"] = get("contact")
			
			self.addFolderListItem(params, item)
							
		self.parseFolderList(get("path"), params, result)
								
	def listUserFeed(self, params = {}):
		if self.dbg:
			print self.plugin + " listUserFolderFeeds"
		
		get = params.get
		if ( get('login') == "true" and self.settings.getSetting( "user_email" ) != "" ):
			auth = self.settings.getSetting( "userid" )
			if ( not auth ) :
				self.login()
				auth = self.settings.getSetting( "userid" )
		
		(result, status) = self.core.getUserData(params)
		
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
		
	def listStoredSearches(self, params = {}):
		get = params.get
		search_item = {'Title':self.language( 30007 ),'path':"/root/search/new", 'thumbnail':"search", 'action':"search" }
		self.addActionListItem(params, search_item)
		try:
			searches = eval(self.settings.getSetting("stored_searches"))
		except:
			searches = []
		
		for search in searches:
			item = {}
			item["Title"] = search
			item["search"] = urllib.quote_plus(search)
			item["action"] = "search"
			item["path"] = get("path")
			item["thumbnail"] = self.settings.getSetting("search_" + search + "_thumb") 
			self.addFolderListItem(params, item, len(searches))
			
		self.xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True, cacheToDisc=False )
		return True

	def scrapeVideos(self, params):
		get = params.get

		if ("scraper_" + get("scraper") in self.feeds):
			feed = self.feeds["scraper_" + get("scraper")]

			( results, status ) = self.scraper.scrape(feed, params)
			
			if ( results ):
				if (get("scraper") == "categories" and get("category")):
					self.parseVideoList(get("path"), params, results)
				elif (get("scraper") == "my_likes" or get("scraper") == "my_videos" or get("scraper") == "my_album"):
					self.parseVideoList(get("path"), params, results)
				else:
					self.parseFolderList(get("path"), params, results)
					
			elif ( status == 303):
				self.utils.showMessage(self.language(30600), results)
			else:
				self.utils.showMessage(self.language(30600), self.language(30606))

	#================================== Plugin Actions =========================================

	def playVideoById(self, params = {}):
		result = self.utils.getUserInput('VideoID', '')
		params["videoid"] = result 
		if (result):
			self.playVideo(params);
		
	def playVideo(self, params = {}):
		get = params.get
		(video, status) = self.core.construct_video_url(get('videoid'));
		if status != 200:
			self.errorHandling(self.language(30603), video, status)
			return False

		if ( 'swf_config' in video ):
			video['video_url'] += " swfurl=%s swfvfy=1" % video['swf_config']

		listitem=self.xbmcgui.ListItem(label=video['Title'], iconImage=video['thumbnail'], thumbnailImage=video['thumbnail'], path=video['video_url']);
		listitem.setInfo(type='Video', infoLabels=video)
		
		if self.dbg:
			print self.plugin + " - Playing video: " + self.makeAscii(video['Title']) + " - " + get('videoid') + " - " + video['video_url']

		self.xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=listitem)
		self.settings.setSetting( "vidstatus-" + get('videoid'), "7" )
	
	
	def downloadVideo(self, params = {}):
		get = params.get
		if (get("videoid")):
			path = self.settings.getSetting( "downloadPath" )
			if (not path):
				self.utils.showMessage(self.language(30600), self.language(30611))
				self.settings.openSettings()
				path = self.settings.getSetting( "downloadPath" )

			( video, status )  = self.core.construct_video_url(get("videoid"))

			if status != 200:
				if self.dbg:
					print self.plugin + " downloadVideo got error from construct_video_url: [%s] %s" % ( status, video)
				self.errorHandling(self.language( 30501 ), video, status)
				return False

			item = video.get
			
			self.utils.showMessage(self.language(30612), item("Title", "Unknown Title"))

			( video, status ) = self.core.downloadVideo(video)

			if status == 200:
				self.utils.showMessage(self.language( 30604 ), video['Title'])

	def setLike(self, params = {}):
		get = params.get
		
		if (get("videoid")):
			(message, status) = self.core.setLike(params)
			if status != 200:
				self.errorHandling(self.language(30020), message, status)
				return False
			
			if (get("action") == "remove_favorite"):
				self.xbmc.executebuiltin( "Container.Refresh" )
			return True			
		
	def changeScraperSorting(self, params = {}):
		get = params.get
		if (get("category") and get("scraper") and get("sort")):
			self.settings.setSetting("scraper_" + get("scraper") + "_sort_" + get("category"), get("sort"), )
			print self.plugin + "Changed Scraper List Sorting"
		
		self.xbmc.executebuiltin( "Container.Refresh" )
		return
	
	def updateContact(self, params = {}):
		get = params.get

		if (not get("contact")):
			params["contact"] = self.utils.getUserInput('Contact', '')
		
		if (get("contact")):
			(result, status) = self.core.updateContact(params)
			if status != 200:
				self.errorHandling(self.language(30029), result, status)
				return False

			self.utils.showMessage(self.language(30614), get("contact"))
			self.xbmc.executebuiltin( "Container.Refresh" )

	def updateGroup(self, params = {}):
		get = params.get
			
		if (get("group")):
			(result, status) = self.core.updateGroup(params)
			if status != 200:
				self.errorHandling(self.language(30029), result, status)
				return False
			if (get("action") == "leave_group"):
				self.xbmc.executebuiltin( "Container.Refresh" )
		return True
				
	def updateSubscription(self, params = {}):
		get = params.get
		if (get("channel")):
			(message, status) = self.core.updateSubscription(params)
			if status != 200:
				self.errorHandling(self.language(30021), message, status)
				return False
			else:
				if (get("action") == "remove_subscription"):
					self.xbmc.executebuiltin( "Container.Refresh" )
		return True
	
	def removeWatchLater(self, params = {}):
		get = params.get
		
		if (get("videoid")):
			(result, status) = self.core.removeWatchLater(params)
			if status != 200:
				return False
			else:
				self.xbmc.executebuiltin( "Container.Refresh" )
		
		return True
	#================================== Searching =========================================
	def search(self, params = {}):
		get = params.get
		if (get("search")):
			query = get("search")
			query = urllib.unquote_plus(query)
			self.saveSearchQuery(query, query)
		else :
			query = self.utils.getUserInput('Search', '')
			if (query):
				self.saveSearchQuery(query,query)
				params["search"] = query
		
		if (query):
			( result, status ) = self.core.search(query, get("page", "0"));
			if status != 200:
				self.errorHandling(self.language(30006), result, status)
				return False
			
			thumbnail = result[0].get('thumbnail')
			
			if (thumbnail and query):
				self.settings.setSetting("search_" + query + "_thumb", thumbnail)
				
			self.parseVideoList(get("path"), params, result)
			
	def deleteSearch(self, params = {}):
		get = params.get
		query = get("delete")
		query = urllib.unquote_plus(query)
		try:
			searches = eval(self.settings.getSetting("stored_searches"))
		except:
			searches = []
			
		for count, search in enumerate(searches):
			if (search.lower() == query.lower()):
				del(searches[count])
				break
		
		self.settings.setSetting("stored_searches", repr(searches))
		self.xbmc.executebuiltin( "Container.Refresh" )
		
	def saveSearchQuery(self, old_query, new_query):
		old_query = urllib.unquote_plus(old_query)
		new_query = urllib.unquote_plus(new_query)
		try:
			searches = eval(self.settings.getSetting("stored_searches"))
		except:
			searches = []
		
		for count, search in enumerate(searches):
			if (search.lower() == old_query.lower()):
				del(searches[count])
				break

		searchCount = ( 10, 20, 30, 40, )[ int( self.settings.getSetting( "saved_searches" ) ) ]
		searches = [new_query] + searches[:searchCount]
		self.settings.setSetting("stored_searches", repr(searches))
	
	def editSearch(self, params = {}):
		get = params.get
		if (get("search")):
			old_query = urllib.unquote_plus(get("search"))
			new_query = self.utils.getUserInput('Search', old_query)
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
				if (len(self.settings.getSetting( "userid" )) > 0):
					self.addFolderListItem(params, item_params)
		else :
			if (item("action") == "settings"):
				if (len(self.settings.getSetting( "userid" )) > 0):
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

		thumbnail = item("thumbnail", "DefaultFolder.png")
		if (thumbnail.find("http://") == -1):	
			thumbnail = self.utils.getThumbnail(thumbnail)
				
		cm = self.addContextMenuItems(params, item_params)			
		

		listitem=self.xbmcgui.ListItem( item("Title"), iconImage=icon, thumbnailImage=thumbnail )
		url = '%s?path=%s&' % ( sys.argv[0], item("path") )
		
		url += self.buildItemUrl(item_params)	
		
		if len(cm) > 0:
			listitem.addContextMenuItems( cm, replaceItems=True )
		listitem.setProperty( "Folder", "true" )
		
		if (item("feed") == "downloads"):
			url = self.settings.getSetting("downloadPath")
		self.xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=True, totalItems=size)
	
	# common function for adding action items
	def addActionListItem(self, params = {}, item_params = {}, size = 0):
		get = params.get
		item = item_params.get
		folder = False
		icon = "DefaultFolder.png"
		
		thumbnail = item("thumbnail", "default")
		if (item("thumbnail", "DefaultFolder.png").find("http://") == -1):	
			thumbnail = self.utils.getThumbnail(item("thumbnail"))

		listitem=self.xbmcgui.ListItem( item("Title"), iconImage=icon, thumbnailImage=thumbnail )
		
		if (item("action") == "search" or item("action") == "settings"):
			folder = True
		else:
			listitem.setProperty('IsPlayable', 'true');
			
		url = '%s?path=%s&' % ( sys.argv[0], item("path") )
		url += 'action=' + item("action") + '&'
			
		self.xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=folder, totalItems=size)
	
	# common function for adding video items
	def addVideoListItem(self, params = {}, item_params = {}, listSize = 0):
		get = params.get
		item = item_params.get
		
		icon = "default"
		icon = self.utils.getThumbnail(icon)
		
		listitem=self.xbmcgui.ListItem(item("Title"), iconImage=icon, thumbnailImage=item("thumbnail") )

		url = '%s?path=%s&action=play_video&videoid=%s' % ( sys.argv[0], item("path"), item("videoid"));
		cm = self.addContextMenuItems(params, item_params)

		listitem.addContextMenuItems( cm, replaceItems=True )
		
		listitem.setProperty( "Video", "true" )
		listitem.setProperty( "IsPlayable", "true");
		listitem.setInfo(type='Video', infoLabels=item_params)
		
		self.xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=False, totalItems=listSize + 1)
		
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
					if (self.settings.getSetting("scraper_" + get("scraper") + "_sort_" + result("category"))):
						result_params["sort"] = self.settings.getSetting("scraper_" + get("scraper") + "_sort_" + result("category"))
						
			if (get("api") == "my_contacts"):
				result_params["feed"] = "contact_option_list"
							
			result_params["path"] = path
						
			self.addFolderListItem( params, result_params, listSize + 1)
			
		if next:
			item = {"Title":self.language( 30509 ), "thumbnail":"next", "page":str(int(get("page", "0")) + 1)} 
			for k, v in params.items():
				if ( k != "thumbnail" and k != "Title" and k != "page"):
					item[k] = v
			
			self.addFolderListItem(params, item, listSize)
		
		cache = False
		
		if (get("scraper")):
			cache = True
		
		self.xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True, cacheToDisc=cache )
	
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
			item = {"Title":self.language( 30509 ), "thumbnail":"next", "page":str(int(get("page", "0")) + 1)} 
			for k, v in params.items():
				if ( k != "thumbnail" and k != "Title" and k != "page"):
					item[k] = v
			
			self.addFolderListItem(params, item)
		
		video_view = self.settings.getSetting("list_view") == "1"
		if (self.dbg):
			print self.plugin + " view mode: " + self.settings.getSetting("list_view")
		
		if (not video_view):
			video_view = self.settings.getSetting("list_view") == "0"
		
		if (video_view):
			if (self.dbg):
				print self.plugin + " setting view mode"
			self.xbmc.executebuiltin("Container.SetViewMode(500)")
		
		self.xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=self.xbmcplugin.SORT_METHOD_UNSORTED )
		self.xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=self.xbmcplugin.SORT_METHOD_LABEL )
		self.xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=self.xbmcplugin.SORT_METHOD_VIDEO_RATING )
		self.xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=self.xbmcplugin.SORT_METHOD_DATE )
		self.xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=self.xbmcplugin.SORT_METHOD_PROGRAM_COUNT )
		self.xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=self.xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
		self.xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=self.xbmcplugin.SORT_METHOD_GENRE )	   

		self.xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True, cacheToDisc=True )

		
	#=================================== Tool Box ======================================= 
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
			if (self.settings.getSetting( "userid" )):	
				if ( get("api") == "my_likes" and not get("contact") ):
					cm.append( ( self.language( 30504 ) % title, 'XBMC.RunPlugin(%s?path=%s&action=remove_favorite&videoid=%s&)' % ( sys.argv[0], get("path"), item("videoid") ) ) )
				else:
					cm.append( ( self.language( 30503 ) % title, 'XBMC.RunPlugin(%s?path=%s&action=add_favorite&videoid=%s&)' % ( sys.argv[0],  get("path"), item("videoid") ) ) )
			
			if (get("api") == "my_watch_later"):
				cm.append( (self.language(30529) , "XBMC.RunPlugin(%s?path=%s&action=remove_watch_later&videoid=%s)" % ( sys.argv[0],  get("path"), item("videoid") ) ) )
			else:
				cm.append( (self.language(30530) , "XBMC.RunPlugin(%s?path=%s&action=add_watch_later&videoid=%s)" % ( sys.argv[0],  get("path"), item("videoid") ) ) )
			
			cm.append( ( self.language( 30500 ), "XBMC.RunPlugin(%s?path=%s&action=download&videoid=%s)" % ( sys.argv[0],  get("path"), item("videoid") ) ) )
			cm.append( ( self.language( 30507 ), "XBMC.Container.Update(%s?path=%s&action=search&search=%s)" % ( sys.argv[0],  get("path"), urllib.quote_plus( title ) ) ) )
			cm.append( ( self.language( 30502 ), "XBMC.Action(Queue)", ) )
			cm.append( ( self.language( 30501 ), "XBMC.Action(Info)", ) )
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
					if (self.settings.getSetting("scraper_" + get("scraper") + "_sort_" + item("category"))):
						default = self.settings.getSetting("scraper_" + get("scraper") + "_sort_" + item("category") )
						
				cm_url = 'XBMC.RunPlugin(%s?path=%s&action=change_scraper_sort&scraper=%s&category=%s&sort=' % ( sys.argv[0], item("path"), get("scraper"), item("category"))
				for sort in self.scraper_sorts:
					sget = sort.get
					if (sget("sort") != default and (sget(get("scraper")) or sget("common"))):
						cm.append( ( sget("Title"), cm_url + sget("sort") + "&)" ) ) 
						
			if (item("channel") and self.settings.getSetting( "userid" )):
				if (item("external") or get("scraper")):
					cm.append( ( self.language( 30512 ) % title, 'XBMC.RunPlugin(%s?path=%s&channel=%s&action=add_subscription)' % ( sys.argv[0], get("path"), item("channel") ) ) )
				else:
					cm.append( ( self.language( 30513 ) % title, 'XBMC.RunPlugin(%s?path=%s&channel=%s&action=remove_subscription)' % ( sys.argv[0], get("path"), item("channel") ) ) )

			if (item("group") and self.settings.getSetting( "userid" )):
				if (item("external") or get("scraper")):
					cm.append( ( self.language( 30510 ) % title, 'XBMC.RunPlugin(%s?path=%s&group=%s&action=join_group)' % ( sys.argv[0], get("path"), item("group") ) ) )
				else:
					cm.append( ( self.language( 30511 ) % title, 'XBMC.RunPlugin(%s?path=%s&group=%s&action=leave_group)' % ( sys.argv[0], get("path"), item("group") ) ) )
			
			if ( item("api") == "my_likes"  or item("album") or item("api") == "my_videos" ):
				cm.append( ( self.language( 30514 ), "XBMC.Action(Queue)" ) )
			
			if (item("search")):
				cm.append( ( self.language( 30508 ), 'XBMC.RunPlugin(%s?path=%s&action=delete_search&delete=%s&)' % ( sys.argv[0], item("path"), item("search") ) ) )
				cm.append( ( self.language( 30506 ), 'XBMC.Container.Update(%s?path=%s&action=edit_search&search=%s&)' % ( sys.argv[0], item("path"), item("search") ) ) )
		
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
			if self.dbg:
				print self.plugin + " makeAscii hit except on : " + repr(str)
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
			title = self.language(30600)
		if result == "":
			result = self.language(30617)
			
		if ( status == 303):
			self.utils.showMessage(title, result)
		elif ( status == 500):
			self.utils.showMessage(title, self.language(30606))
		else:
			self.utils.showMessage(title, self.language(30617))
