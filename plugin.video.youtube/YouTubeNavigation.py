'''
   YouTube plugin for XBMC
   Copyright (C) 2010 Tobias Ussing And Henrik Mosgaard Jensen

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
import os
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import YouTubeCore

core = YouTubeCore.YouTubeCore();
    
class YouTubeNavigation:     
    __settings__ = sys.modules[ "__main__" ].__settings__
    __language__ = sys.modules[ "__main__" ].__language__
    __plugin__ = sys.modules[ "__main__"].__plugin__    
    __dbg__ = sys.modules[ "__main__" ].__dbg__
                 
    plugin_thumbnail_path = os.path.join( os.getcwd(), "thumbnails" )

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
    feeds['recommended'] = "http://www.youtube.com/videos?r=1";

    # we fill the list with category definitions, with labels from the appropriate language file
    #               label                         , path                            , thumbnail                      ,  login          ,  feed / action
    categories = (
                  {'label':__language__( 30001 )  ,'path':"/root/feeds"             , 'thumbnail':"feeds"            , 'login':"false" , 'feed':"" },
                  {'label':__language__( 30019 )  ,'path':"/root/recommended"       , 'thumbnail':"recommended"      , 'login':"true"  , 'scraper':"recommended" },
                  {'label':__language__( 30018 )  ,'path':"/root/contacts"          , 'thumbnail':"contacts"         , 'login':"true"  , 'feed':"contacts" },
                  {'label':__language__( 30002 )  ,'path':"/root/favorites"         , 'thumbnail':"favorites"        , 'login':"true"  , 'feed':"favorites" },
                  {'label':__language__( 30017 )  ,'path':"/root/playlists"         , 'thumbnail':"playlists"        , 'login':"true"  , 'feed':"playlists" },
                  {'label':__language__( 30003 )  ,'path':"/root/subscriptions"     , 'thumbnail':"subscriptions"    , 'login':"true"  , 'feed':"subscriptions" },
                  {'label':__language__( 30004 )  ,'path':"/root/subscriptions/new" , 'thumbnail':"newsubscriptions" , 'login':"true"  , 'feed':"newsubscriptions" },
                  {'label':__language__( 30005 )  ,'path':"/root/uploads"           , 'thumbnail':"uploads"          , 'login':"true"  , 'feed':"uploads" },
                  {'label':__language__( 30006 )  ,'path':"/root/search"            , 'thumbnail':"search"           , 'login':"false" , 'feed':"searches" },
                  {'label':__language__( 30007 )  ,'path':"/root/search/new"        , 'thumbnail':"search"           , 'login':"false" , 'action':"search" },
                  {'label':__language__( 30008 )  ,'path':"/root/playbyid"          , 'thumbnail':"playbyid"         , 'login':"false" , 'action':"playbyid" },
                  {'label':__language__( 30009 )  ,'path':"/root/feeds/discussed"   , 'thumbnail':"most"             , 'login':"false" , 'feed':"feed_discussed" },
                  {'label':__language__( 30010 )  ,'path':"/root/feeds/linked"      , 'thumbnail':"most"             , 'login':"false" , 'feed':"feed_linked" },
                  {'label':__language__( 30011 )  ,'path':"/root/feeds/viewed"      , 'thumbnail':"most"             , 'login':"false" , 'feed':"feed_viewed" },
                  {'label':__language__( 30012 )  ,'path':"/root/feeds/recent"      , 'thumbnail':"most"             , 'login':"false" , 'feed':"feed_recent" },
                  {'label':__language__( 30013 )  ,'path':"/root/feeds/responded"   , 'thumbnail':"most"             , 'login':"false" , 'feed':"feed_responded" },
                  {'label':__language__( 30014 )  ,'path':"/root/feeds/featured"    , 'thumbnail':"featured"         , 'login':"false" , 'feed':"feed_featured" },
                  {'label':__language__( 30015 )  ,'path':"/root/feeds/favorites"   , 'thumbnail':"top"              , 'login':"false" , 'feed':"feed_favorites" },
                  {'label':__language__( 30016 )  ,'path':"/root/feeds/rated"       , 'thumbnail':"top"              , 'login':"false" , 'feed':"feed_rated" },
                  {'label':__language__( 30027 )  ,'path':"/root/login"             , 'thumbnail':"login"            , 'login':"false" , 'action':"settings" },
                  {'label':__language__( 30028 )  ,'path':"/root/settings"          , 'thumbnail':"settings"         , 'login':"true"  , 'action':"settings" }
                  )

    #==================================== Main Entry Points===========================================
    def listMenu(self, params = {}):
        get = params.get

        if (get("scraper")):
            self.scrapeVideos(params)
            return
        
        if (get("login")):
            if ( get('feed') == 'subscriptions' or get('feed') == 'playlists' or get('feed') == 'contacts' ):
                self.listUserFolder(params)                  
            elif ( get("feed") in self.feeds):
                self.listUserFolderFeeds(params)
            elif (get("feed") == "contact_option_list"):
                self.listOptionFolder(params)
            return

        if (get("feed")):
            if ( get("feed") in self.feeds):
                self.listFeedFolder(params)
            elif (get("feed") == "searches"):
                self.listStoredSearches(params)
            return
        
        path = get("path", "/root")
        
        for category in self.categories:
            cat_get = category.get 
            if (cat_get("path").find(path +"/") > -1 ):
                if (cat_get("path").rfind("/") <= len(path +"/")):
                    if self.__settings__.getSetting( cat_get("path").replace("/root/", "") ) != "true":
                        self.addListItem(params, category)
        
        xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True, cacheToDisc=True )

    def executeAction(self, params = {}):
        get = params.get
        if (get("action") == "playbyid"):
            self.playVideoById(params)
        if (get("action") == "search"):
            self.search(params)
        if (get("action") == "refine_user"):
            self.refineSearch(params)
        if (get("action") == "delete_refinements"):
            self.deleteRefinements(params)
        if (get("action") == "settings"):
            self.login(params)
        if (get("action") == "delete"):
            self.deleteSearchQuery(params)
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
        if (get("action") == "play_video"):
            self.playVideo(params)
        if (get("action") == "change_subscription_view"):
            self.changeSubscriptionView(params)

    def listOptionFolder(self, params = {}):
        get = params.get
        if ( get('login') and self.__settings__.getSetting( "username" ) != "" ):
            auth = self.__settings__.getSetting( "auth" )
            if ( not auth ) :
                self.login()
                auth = self.__settings__.getSetting( "auth" )

        item_favorites = {'label':self.__language__( 30020 ), 'path':get("path"), 'external':"true", 'login':"true", 'thumbnail':"favorites", 'feed':"favorites", "contact":get("contact")}
        self.addFolderListItem(params, item_favorites, 1)
        item_playlists = {'label':self.__language__( 30023 ), 'path':get("path"), 'external':"true", 'login':"true", 'thumbnail':"playlists", 'feed':"playlists", "contact":get("contact")}
        self.addFolderListItem(params, item_playlists, 2)
        item_subscriptions = {'label':self.__language__( 30021 ), 'path':get("path"), 'external':"true", 'login':"true", 'thumbnail':"subscriptions", 'feed':"subscriptions", "contact":get("contact")}
        self.addFolderListItem(params, item_subscriptions, 3)
        item_uploads = {'label':self.__language__( 30022 ), 'path':get("path"), 'external':"true", 'login':"true", 'thumbnail':"uploads", 'feed':"uploads", "contact":get("contact") }
        self.addFolderListItem(params, item_uploads, 4)
        
        xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True, cacheToDisc=False)

    def parseFeeds(self, params):
        get = params.get
                
        feed = self.feeds[get("feed")]
        if (feed.find("%s") > 0):
            if ( get("contact")):
                feed = feed % get("contact")
            elif ( get("channel")):
                feed = feed % get("channel")
            elif ( get("playlist")):
                feed = feed % get("playlist")
            elif ( get("feed") == "uploads" or get("feed") == "favorites" or  get("feed") == "playlists" or get("feed") == "subscriptions" or get("feed") == "newsubscriptions"):
                feed = feed % self.__settings__.getSetting( "nick" )
        return feed
    
    def listUserFolder(self, params = {}):
        print self.__plugin__ + " listUserFolder"
        get = params.get
        if ( get('login') and self.__settings__.getSetting( "username" ) != "" ):
            auth = self.__settings__.getSetting( "auth" )
            if ( not auth ) :
                self.login()
                auth = self.__settings__.getSetting( "auth" )
                
        feed = self.parseFeeds(params)
                        
        (result, status) = core.playlists(feed, get("page", "0"))
        if status != 200:
            feed_label = ""
            for category in self.categories:
                cat_get = category.get
                if (cat_get("feed") == get("feed")):
                    feed_label = cat_get("label")
                    break
                
                if (feed_label != ""):
                    self.errorHandling(feed_label, result, status)
                else:
                    self.errorHandling(get("feed"), result, status)
                return False
            
        if ( get("feed") == "contacts"):
            item_add_user = {'label':self.__language__( 30024 ), 'path':get("path"), 'login':"true", 'thumbnail':"add_user", 'action':"add_contact"}
            self.addFolderListItem(params, item_add_user,  1)
                        
        if ( get('feed') == 'subscriptions' ) :
            item = {"label":self.__language__( 30004 ), "path":"/root/subscriptions/new", "thumbnail":"newsubscriptions", "login":"true", "feed":"newsubscriptions"}
            if (get("contact")):
                item["contact"] = get("contact")
                            
            self.addFolderListItem(params, item)
                            
        self.parseFolderList(get("path"), params, result)
                                
    def listUserFolderFeeds(self, params = {}):
        print self.__plugin__ + " listUserFolderFeeds"
        get = params.get
        if ( get('login') and self.__settings__.getSetting( "username" ) != "" ):
            auth = self.__settings__.getSetting( "auth" )
            if ( not auth ) :
                self.login()
                auth = self.__settings__.getSetting( "auth" )
            
        feed = self.parseFeeds(params)
        
        if ( get('login') and feed):
            ( result, status ) = core.list(feed, get("page", "0"));
            if status != 200:
                feed_label = ""
                for category in self.categories:
                    cat_get = category.get
                    if (cat_get("feed") == get("feed")):
                        feed_label = cat_get("label")
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

        self.parseVideoList(get("path"), params, result);
            
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
        search_item = {'label':self.__language__( 30007 ),'path':"/root/search/new", 'thumbnail':"search", 'action':"search" }
        self.addActionListItem(params, search_item)
        try:
            searches = eval(self.__settings__.getSetting("stored_searches"))
        except:
            searches = []
               
        for search in searches:
            item = {}
            item["label"] = search
            item["search"] = search
            item["action"] = "search"
            item["path"] = get("path")
            item["thumbnail"] = self.__settings__.getSetting("search_" + search + "_thumb") 
            self.addFolderListItem(params, item, len(searches))
            
        xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True, cacheToDisc=False )
        return True

    def listFeedFolder(self, params = {}):
        get = params.get

        feed = self.feeds[get("feed")]
                                    
        ( result, status ) = core.feeds(feed, get("page", "0"))
        if status != 200:
            feed_label = ""
            for category in self.categories:
                cat_get = category.get
                if (cat_get("action") == get("feed")):
                    feed_label = cat_get("label")
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

        self.parseVideoList(get("path"), params, result);

    def scrapeVideos(self, params):
        get = params.get
        if (get("scraper") in self.feeds):
            feed = self.feeds[get("scraper")]
            ( results, status ) = core.scrapeVideos(feed, params)

            if ( results ):
                self.parseVideoList(get("path"), params, results)
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
        (video, status) = core.construct_video_url(params);
        if status != 200:
            self.errorHandling(self.__language__(30603), video, status)
            return False

        if ( 'swf_config' in video ):
            video['video_url'] += " swfurl=%s swfvfy=1" % video['swf_config']

        listitem=xbmcgui.ListItem(label=video['Title'], iconImage=video['thumbnail'], thumbnailImage=video['thumbnail'], path=video['video_url']);
        
        listitem.setInfo(type='Video', infoLabels=video)
        
        if self.__dbg__:
            print self.__plugin__ + " - Playing video: " + video['Title'] + " - " + get('videoid') + " - " + video['video_url']

        xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=listitem)
        
        self.__settings__.setSetting( "vidstatus-" + video['videoid'], "7" )

    def refineSearch(self, params = {}):
        get = params.get
        query = get("search")
        try:
            searches = eval(self.__settings__.getSetting("stored_searches_author"))
        except :
            searches = {}
            
        if query in searches:
            author = self.getUserInput('Search on author', searches[query])
        else:
            author = self.getUserInput('Search on author', '')

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
        try:
            searches = eval(self.__settings__.getSetting("stored_searches_author"))
        except :
            searches = {}
            
        if query in searches:
            del searches[query]
            self.__settings__.setSetting("stored_searches_author", repr(searches))
            self.showMessage(self.__language__(30006), self.__language__(30610))
            xbmc.executebuiltin( "Container.Refresh" )
                                                                                            
    def search(self, params = {}):
        get = params.get
        if (get("search")):
            query = get("search")
            self.saveSearchQuery(query)
        else :
            query = self.getUserInput('Search', '')
            if (query):
                self.saveSearchQuery(query)
                params["search"] = query
        
        if (query):
            ( result, status ) = core.search(query, get("page", "0"));
            if status != 200:
                self.errorHandling(self.__language__(30006), result, status)
                return False

            thumbnail = result[0].get("thumbnail")
            if (thumbnail and query):
                self.__settings__.setSetting("search_" + query + "_thumb", thumbnail)
            self.parseVideoList(get("path"), params, result)
                        
    def downloadVideo(self, params = {}):
        get = params.get
        if (get("videoid")):
            path = self.__settings__.getSetting( "downloadPath" )
            if (not path):
                self.showMessage(self.__language__(30600), self.__language__(30611))
                self.__settings__.openSettings()
                path = self.__settings__.getSetting( "downloadPath" )

            self.showMessage(self.__language__(30612), urllib.unquote_plus(get("title", "Unknown Title")))

            ( video, status ) = core.downloadVideo(path, params);
            if status != 200 :
                self.errorHandling(self.__language__( 30501 ), video, status)
                return False

            self.showMessage(self.__language__( 30604 ), urllib.unquote_plus(video['Title']) )

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
        
        if (get("editurl")):
            (message, status ) = core.delete_favorite(get('editurl'))
            if status != 200:
                self.errorHandling(self.__language__(30020), message, status)
                return False

            xbmc.executebuiltin( "Container.Refresh" )

    def deleteSearchQuery(self, params = {}):
        get = params.get
        query = get("delete")
        
        try:
            searches = eval(self.__settings__.getSetting("stored_searches"))
        except:
            searches = []
            
        for count, search in enumerate(searches):
            if (search.lower() == query.lower()):
                del(searches[count])
                self.deleteRefinements({'search': query})
                break
            
        self.__settings__.setSetting("stored_searches", repr(searches))
        xbmc.executebuiltin( "Container.Refresh" )
        
    def saveSearchQuery(self, query):
        try:
            searches = eval(self.__settings__.getSetting("stored_searches"))
        except:
            searches = []
            
        for count, search in enumerate(searches):
            if (search.lower() == query.lower()):
                del(searches[count])
                break
        
        searchCount = ( 10, 20, 30, 40, )[ int( self.__settings__.getSetting( "saved_searches" ) ) ]
        searches = [query] + searches[:searchCount]
        self.__settings__.setSetting("stored_searches", repr(searches))
    
    def addContact(self, params = {}):
        get = params.get

        if (get("contact")):
            contact = get("contact")
        else:
            contact = self.getUserInput('Contact', '')
            
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
        if (get("editurl")):
            (message, status) = core.remove_subscription(get("editurl"))
            if status != 200:
                self.errorHandling(self.__language__(30021), message, status)
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
            else :
                self.addActionListItem(params, item_params)
 
    # common function for adding folder items
    def addFolderListItem(self, params = {}, item_params = {}, size = 0):
        get = params.get
        item = item_params.get
        
        icon = "DefaultFolder.png"
        thumbnail = item("thumbnail")
        cm = []
        
        if (item("thumbnail", "DefaultFolder.png").find("http://") == -1):    
            thumbnail = self.getThumbnail(item("thumbnail"))
            
        listitem=xbmcgui.ListItem( item("label"), iconImage=icon, thumbnailImage=thumbnail )
        url = '%s?path=%s&' % ( sys.argv[0], item("path") )
        
        if (item("search")):
            url += "search=" + item("search") + "&"
            cm.append( ( self.__language__( 30508 ), 'XBMC.RunPlugin(%s?path=%s&action=delete&delete=%s&)' % ( sys.argv[0], item("path"), item("search") ) ) )
            cm.append( ( self.__language__( 30505 ), 'XBMC.RunPlugin(%s?path=%s&action=refine_user&search=%s&)' % ( sys.argv[0], item("path"), item("search") ) ) )
            
            try:
                searches = eval(self.__settings__.getSetting("stored_searches_author"))
            except :
                searches = {}
                
            if item("search") in searches:                            
                cm.append( ( self.__language__( 30500 ), 'XBMC.RunPlugin(%s?path=%s&action=delete_refinements&search=%s&)' % ( sys.argv[0], item("path"), item("search") ) ) )                        
            
        if (item("playlist")):
            url += "playlist=" + item("playlist") + "&"
            cm.append( ( self.__language__( 30507 ), "XBMC.Action(Queue)" ) )
        
        if (item("action")):
            url += "action=" + item("action") + "&"
        
        if (item("feed")):   
            url += "feed=" + item("feed") + "&"
        
        if (item("external")):
            url += "external=true&"
            
        if (item("view_mode")):
            cm_url = 'XBMC.RunPlugin(%s?path=%s&channel=%s&action=change_subscription_view&view_mode=%s&' % ( sys.argv[0], item("path"), item("channel"), item("view_mode") )
            if (item("external")):
                cm_url += "external=true&contact=" + get("contact") + "&"
            cm_url +=")"
            
            if (item("feed") == "subscriptions_favorites"):
                cm.append( (self.__language__( 30511 ), cm_url) )
            elif (item("feed") == "subscriptions_uploads"):
                cm.append ( (self.__language__( 30510 ), cm_url) )
                    
            if (get("external")):
                cm.append( ( self.__language__( 30512 ) % item("channel"), 'XBMC.RunPlugin(%s?path=%s&channel=%s&action=add_subscription)' % ( sys.argv[0], item("path"), item("channel") ) ) )
            else:
                cm.append( ( self.__language__( 30513 ) % item("channel"), 'XBMC.RunPlugin(%s?path=%s&editurl=%s&action=remove_subscription)' % ( sys.argv[0], item("path"), item("editurl") ) ) )
                
        if (item("login") == "true"):
            url += "login=true&"
        
        if (item("contact")):
            url += "contact=" + item("contact") + "&"
            if (item("external")):
                cm.append( (self.__language__(30026), 'XBMC.RunPlugin(%s?path=%s&action=add_contact&)' % ( sys.argv[0], item("path") ) ) )
            else:
                cm.append( (self.__language__(30025), 'XBMC.RunPlugin(%s?path=%s&action=remove_contact&contact=%s&)' % ( sys.argv[0], item("path"), item("contact") ) ) )
    
        if (item("page")):
            url += "page=" + item("page") + "&"

        if ( item("feed") == "favorites"  or item("feed") == "playlists" or item("feed") == "uploads" ):
            cm.append( ( self.__language__( 30507 ), "XBMC.Action(Queue)" ) )
            
        if (item("channel")):
            url += "channel=" + item("channel") + "&"
            
        if (item("scraper")):
            url += "scraper=" + item("scraper") + "&"

        if len(cm) > 0:
            listitem.addContextMenuItems( cm, replaceItems=True )
        listitem.setProperty( "Folder", "true" )
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=True, totalItems=size)
    
    # common function for adding action items
    def addActionListItem(self, params = {}, item_params = {}, size = 0):
        get = params.get
        item = item_params.get
        folder = False
        icon = "DefaultFolder.png"
        thumbnail = self.getThumbnail(item("thumbnail"))
        listitem=xbmcgui.ListItem( item("label"), iconImage=icon, thumbnailImage=thumbnail )
        
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

        icon = item("thumbnail", "DefaultFolder.png")
        listitem=xbmcgui.ListItem(item("label"), iconImage=icon, thumbnailImage=item("thumbnail") )

        url = '%s?path=%s&action=play_video&videoid=%s' % ( sys.argv[0], item("path"), item("videoid"));
            
        cm = []
        
        if ( get("feed") == "favorites" and not get("contact") ):
            if ( item('videoid') ):
                cm.append( ( self.__language__( 30506 ), 'XBMC.RunPlugin(%s?path=%s&action=remove_favorite&editurl=%s&)' % ( sys.argv[0], item("path"), item("editurl") ) ) )
        else:
            cm.append( ( self.__language__( 30503 ), 'XBMC.RunPlugin(%s?path=%s&action=add_favorite&videoid=%s&)' % ( sys.argv[0],  item("path"), item("videoid") ) ) )

        cm.append( ( self.__language__(30501), "XBMC.RunPlugin(%s?path=%s&action=download&videoid=%s&title=%s)" % ( sys.argv[0],  item("path"), item("videoid"), urllib.quote_plus(item("label").decode("ascii", "ignore") ) ) ) )
        cm.append( ( self.__language__( 30512 ) % item("Studio"), 'XBMC.RunPlugin(%s?path=%s&channel=%s&action=add_subscription)' % ( sys.argv[0], item("path"), item("Studio") ) ) )
        cm.append( ( self.__language__( 30504 ), "XBMC.Action(Queue)", ) )
        cm.append( ( self.__language__( 30502 ), "XBMC.Action(Info)", ) )
        
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
            
            feed = result("playlistId", "")
            
            if ( feed == "" ):
                feed = result("Title", "")
                
            result_params["label"] = result("Title")
            
            if (get("feed") == "contacts"):
                result_params["thumbnail"] = "user"
            
            if (get("feed") == "subscriptions"):
                viewmode = ""
                if (get("external")):
                    viewmode += "external_" + get("contact") + "_"
                    result_params["external"] = "true"
                viewmode += "view_mode_" + result("Title")
                
                if (self.__settings__.getSetting(viewmode) == "subscriptions_favorites"):
                    result_params["feed"] = "subscriptions_favorites"
                    result_params["view_mode"] = "subscriptions_uploads"
                else:
                    result_params["feed"] = "subscriptions_uploads"  
                    result_params["view_mode"] = "subscriptions_favorites"
                
                result_params["channel"] = result("Title")
            else:
                result_params["feed"] = feed
                result_params["action"] = feed
            
            if (result("playlistId")): 
                result_params["playlist"] = result("playlistId")
                result_params["feed"] = "playlist_root"
                result_params["action"] = ""
            
            if (get("feed") == "contacts"):
                result_params["contact"] = result("Title")
                result_params["feed"] = "contact_option_list"
                result_params["action"] = ""
            
            result_params["login"] = "true"
            result_params["path"] = path
                        
            if (result("playlist") or result("channel")):
                if (result("playlist")):
                    if (self.__settings__.getSetting(get("feed") + "_" + result("playlist") + "_thumb")):
                        result_params["thumbnail"] = self.__settings__.getSetting(get("feed") + "_" + result("playlist") + "_thumb")
                if (result("channel")):
                    if (self.__settings__.getSetting(get("feed") + "_" + result("channel") + "_thumb")):
                        result_params["thumbnail"] = self.__settings__.getSetting(get("feed") + "_" + result("channel") + "_thumb")
            
            self.addFolderListItem( params, result_params, listSize + 1)
            
        if next:
            item = {"path":get("path"), "label":self.__language__( 30509 ), "thumbnail":"next", "login": get("login"), "page":str(int(get("page", "0")) + 1)} 
            if (get("feed")):
                item["feed"] = get("feed")
            if (get("contact")):
                item["contact"] = get("contact")
            if (get("playlist")):
                item["playlist"] = get("playlist")
            if (get("action")):
                item["action"] = get("action")
            if (get("channel")):
                item["channel"] = get("channel")
            if (get("search")):
                item["action"] = "search"
                item["search"] = get("search")
            if (get("scraper")):
                item["scraper"] = get("scraper")
                                 
            self.addFolderListItem(params, item, listSize)
        
        xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True, cacheToDisc=False )
    
    #parses a video list consisting of a tuple of dictionaries 
    def parseVideoList(self, path, params, results):
        listSize = len(results)
        get = params.get
        
        next = False
        for result_params in results:
            result = result_params.get
            next = result("next") == "true"
            
            if ( result('reasonCode') ):
                if result('reasonCode') == 'requesterRegion':
                    continue;
            result_params["label"] = result("Title")
            result_params["path"] = path
            self.addVideoListItem( params, result_params, listSize)
        
        if next:
            item = {"path":get("path"), "label":self.__language__( 30509 ), "thumbnail":"next", "login": get("login"), "page":str(int(get("page", "0")) + 1)} 
            if (get("feed")):
                item["feed"] = get("feed")
            if (get("contact")):
                item["contact"] = get("contact")
            if (get("playlist")):
                item["playlist"] = get("playlist")
            if (get("action")):
                item["action"] = get("action")
            if (get("channel")):
                item["channel"] = get("channel")
            if (get("search")):
                item["action"] = "search"
                item["search"] = get("search")
            if (get("scraper")):
                item["scraper"] = get("scraper")
            
            self.addFolderListItem(params, item)
        
        
        video_view = self.__settings__.getSetting("video_view")
        
        if (video_view):
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
