'''
   YouTube plugin for XBMC
   Copyright (C) 2010-2012 Tobias Ussing And Henrik Mosgaard Jensen

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
import urllib


class YouTubeNavigation():
    def __init__(self):
        self.xbmc = sys.modules["__main__"].xbmc
        self.xbmcgui = sys.modules["__main__"].xbmcgui
        self.xbmcplugin = sys.modules["__main__"].xbmcplugin

        self.settings = sys.modules["__main__"].settings
        self.language = sys.modules["__main__"].language
        self.plugin = sys.modules["__main__"].plugin
        self.dbg = sys.modules["__main__"].dbg

        self.utils = sys.modules["__main__"].utils
        self.core = sys.modules["__main__"].core
        self.common = sys.modules["__main__"].common
        self.cache = sys.modules["__main__"].cache

        self.pluginsettings = sys.modules["__main__"].pluginsettings
        self.playlist = sys.modules["__main__"].playlist
        self.login = sys.modules["__main__"].login
        self.feeds = sys.modules["__main__"].feeds
        self.player = sys.modules["__main__"].player
        self.downloader = sys.modules["__main__"].downloader
        self.storage = sys.modules["__main__"].storage
        self.scraper = sys.modules["__main__"].scraper
        self.subtitles = sys.modules["__main__"].subtitles

        # This list contains the main menu structure the user first encounters when running the plugin
        #     label                        , path                                          , thumbnail                    ,  login                  ,  feed / action
        self.categories = (
            {'Title':self.language(30044)  ,'path':"/root/explore"                         , 'thumbnail':"explore"           , 'login':"false" },
            {'Title':self.language(30041)  ,'path':"/root/explore/categories"              , 'thumbnail':"explore"           , 'login':"false" , 'feed':'feed_categories', 'folder':'true'},
            {'Title':self.language(30001)  ,'path':"/root/explore/feeds"                   , 'thumbnail':"feeds"             , 'login':"false" },
            {'Title':self.language(30009)  ,'path':"/root/explore/feeds/discussed"         , 'thumbnail':"most"              , 'login':"false" , 'feed':"feed_discussed" },
            {'Title':self.language(30010)  ,'path':"/root/explore/feeds/linked"            , 'thumbnail':"most"              , 'login':"false" , 'feed':"feed_linked" },
            {'Title':self.language(30011)  ,'path':"/root/explore/feeds/viewed"            , 'thumbnail':"most"              , 'login':"false" , 'feed':"feed_viewed" },
            {'Title':self.language(30012)  ,'path':"/root/explore/feeds/recent"            , 'thumbnail':"most"              , 'login':"false" , 'feed':"feed_recent" },
            {'Title':self.language(30013)  ,'path':"/root/explore/feeds/responded"         , 'thumbnail':"most"              , 'login':"false" , 'feed':"feed_responded" },
            {'Title':self.language(30050)  ,'path':"/root/explore/feeds/shared"            , 'thumbnail':"most"              , 'login':"false" , 'feed':"feed_shared" },
            {'Title':self.language(30014)  ,'path':"/root/explore/feeds/featured"          , 'thumbnail':"featured"          , 'login':"false" , 'feed':"feed_featured" },
            {'Title':self.language(30049)  ,'path':"/root/explore/feeds/trending"          , 'thumbnail':"featured"          , 'login':"false" , 'feed':"feed_trending" },
            {'Title':self.language(30015)  ,'path':"/root/explore/feeds/favorites"         , 'thumbnail':"top"               , 'login':"false" , 'feed':"feed_favorites" },
            {'Title':self.language(30016)  ,'path':"/root/explore/feeds/rated"             , 'thumbnail':"top"               , 'login':"false" , 'feed':"feed_rated" },
            {'Title':self.language(30052)  ,'path':"/root/explore/music"                   , 'thumbnail':"music"             , 'login':"false" , 'store':"disco_searches", "folder":"true" },
            {'Title':self.language(30040)  ,'path':"/root/explore/music/new"               , 'thumbnail':"search"            , 'login':"false" , 'scraper':"search_disco"},
            {'Title':self.language(30055)  ,'path':"/root/explore/music/top100"            , 'thumbnail':"music"             , 'login':"false" , 'scraper':'music_top100'},
            {'Title':self.language(30032)  ,'path':"/root/explore/trailers"                , 'thumbnail':"trailers"          , 'login':"false" , 'scraper':'trailers'},
            {'Title':self.language(30051)  ,'path':"/root/explore/live"                    , 'thumbnail':"live"              , 'login':"false" , 'feed':"feed_live" },
            {'Title':self.language(30019)  ,'path':"/root/recommended"                     , 'thumbnail':"recommended"       , 'login':"true"  , 'user_feed':"recommended" },
            {'Title':self.language(30008)  ,'path':"/root/watch_later"                     , 'thumbnail':"watch_later"       , 'login':"true"  , 'user_feed':"watch_later" },
            {'Title':self.language(30056)  ,'path':"/root/liked"                           , 'thumbnail':"liked"             , 'login':"true"  , 'scraper':"liked_videos" },
            {'Title':self.language(30059)  ,'path':"/root/history"                         , 'thumbnail':"history"           , 'login':"true"  , 'user_feed':"watch_history" },
            {'Title':self.language(30018)  ,'path':"/root/contacts"                        , 'thumbnail':"contacts"          , 'login':"true"  , 'user_feed':"contacts", 'folder':'true' },
            {'Title':self.language(30024)  ,'path':"/root/contacts/new"                    , 'thumbnail':"contacts"          , 'login':"true"  , 'action':"add_contact"},
            {'Title':self.language(30002)  ,'path':"/root/favorites"                       , 'thumbnail':"favorites"         , 'login':"true"  , 'user_feed':"favorites" },
            {'Title':self.language(30017)  ,'path':"/root/playlists"                       , 'thumbnail':"playlists"         , 'login':"true"  , 'user_feed':"playlists", 'folder':'true' },
            {'Title':self.language(30003)  ,'path':"/root/subscriptions"                   , 'thumbnail':"subscriptions"     , 'login':"true"  , 'user_feed':"subscriptions", 'folder':'true' },
            {'Title':self.language(30004)  ,'path':"/root/subscriptions/new"               , 'thumbnail':"newsubscriptions"  , 'login':"true"  , 'user_feed':"newsubscriptions" },
            {'Title':self.language(30005)  ,'path':"/root/uploads"                         , 'thumbnail':"uploads"           , 'login':"true"  , 'user_feed':"uploads" },
            {'Title':self.language(30045)  ,'path':"/root/downloads"                       , 'thumbnail':"downloads"         , 'login':"false" , 'feed':"downloads" },
            {'Title':self.language(30006)  ,'path':"/root/search"                          , 'thumbnail':"search"            , 'login':"false" , 'store':"searches", 'folder':'true' },
            {'Title':self.language(30007)  ,'path':"/root/search/new"                      , 'thumbnail':"search"            , 'login':"false" , 'feed':"search" },
            {'Title':self.language(30027)  ,'path':"/root/login"                           , 'thumbnail':"login"             , 'login':"false" , 'action':"settings" },
            {'Title':self.language(30028)  ,'path':"/root/settings"                        , 'thumbnail':"settings"          , 'login':"true"  , 'action':"settings" }
                                         )

    #==================================== Main Entry Points===========================================
    def listMenu(self, params={}):
        self.common.log(repr(params), 5)
        get = params.get
        cache = True

        path = get("path", "/root")
        if get("feed") not in ["search", "related"] and not get("channel") and not get("contact") and not get("playlist") and get("page", "0") == "0" and get("scraper") not in ["search_disco", "music_artist"]:
            for category in self.categories:
                cat_get = category.get
                if (cat_get("path").find(path + "/") > - 1):
                    if (cat_get("path").rfind("/") <= len(path + "/")):
                        setting = self.settings.getSetting(cat_get("path").replace("/root/explore/", "").replace("/root/", ""))
                        if not setting or setting == "true":
                            if cat_get("feed") == "downloads":
                                if (self.settings.getSetting("download_path")):
                                    self.addListItem(params, category)
                            else:
                                self.addListItem(params, category)

        if (get("feed") or get("user_feed") or get("options") or get("store") or get("scraper")):
            return self.list(params)

        video_view = self.settings.getSetting("list_view") == "1"

        if (video_view):
            self.xbmc.executebuiltin("Container.SetViewMode(500)")

        self.xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True, cacheToDisc=cache)
        self.common.log("Done", 5)

    def executeAction(self, params={}):
        self.common.log(params, 3)
        get = params.get
        if (get("action") == "settings"):
            self.login.login(params)
        if (get("action") in ["delete_search", "delete_disco"]):
            self.storage.deleteStoredSearch(params)
        if (get("action") in ["edit_search", "edit_disco"]):
            self.storage.editStoredSearch(params)
            self.listMenu(params)
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
            self.player.playVideo(params)
        if (get("action") == "queue_video"):
            self.playlist.queueVideo(params)
        if (get("action") == "change_subscription_view"):
            self.storage.changeSubscriptionView(params)
            self.list(params)
        if (get("action") == "play_all"):
            self.playlist.playAll(params)
        if (get("action") == "add_to_playlist"):
            self.playlist.addToPlaylist(params)
        if (get("action") == "remove_from_playlist"):
            self.playlist.removeFromPlaylist(params)
        if (get("action") == "delete_playlist"):
            self.playlist.deletePlaylist(params)
        if (get("action") == "reverse_order"):
            self.storage.reversePlaylistOrder(params)
        if (get("action") == "create_playlist"):
            self.playlist.createPlaylist(params)
        self.common.log("Done", 5)

    #==================================== Item Building and Listing ===========================================
    def list(self, params={}):
        self.common.log("", 5)
        get = params.get
        results = []
        if (get("feed") == "search" or get("scraper") == "search_disco"):
            if not get("search"):
                query = self.common.getUserInput(self.language(30006), '')
                if not query:
                    return False
                params["search"] = query
            if get("scraper") == "search_disco":
                params["store"] = "disco_searches"
            self.storage.saveStoredSearch(params)
            if get("scraper") == "search_disco":
                del params["store"]

        if get("scraper"):
            (results, status) = self.scraper.scrape(params)
        elif get("store"):
            (results, status) = self.storage.list(params)
            self.common.log("store returned " + repr(results))
        else:
            (results, status) = self.feeds.list(params)

        if status == 200:
            if get("folder", "false") != "false":
                self.parseFolderList(params, results)
            else:
                self.parseVideoList(params, results)
                self.common.log("Done", 5)
                return True
        else:
            self.showListingError(params)
            self.common.log("Error")
            return False

    def showListingError(self, params={}):
        self.common.log(repr(params), 5)
        get = params.get
        label = ""
        if get("external"):
            categories = self.storage.user_options
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
            label = self.language(30615)
        if label:
            self.utils.showMessage(label, self.language(30601))
        self.common.log("Done", 5)

    #================================== Plugin Actions =========================================
    def downloadVideo(self, params):
        get = params.get
        self.common.log(repr(params))
        if not self.settings.getSetting("download_path"):
            self.common.log("Download path missing. Opening settings")
            self.utils.showMessage(self.language(30600), self.language(30611))
            self.settings.openSettings()

        download_path = self.settings.getSetting("download_path")
        if not download_path:
            return

        self.common.log("path: " + repr(download_path))
        (video, status) = self.player.buildVideoObject(params)

        if "video_url" in video and download_path:
            params["Title"] = video['Title']
            params["url"] = video['video_url']
            params["download_path"] = download_path
            filename = "%s-[%s].mp4" % (''.join(c for c in video['Title'] if c not in self.utils.INVALID_CHARS), video["videoid"])

            self.subtitles.downloadSubtitle(video)
            if get("async"):
                self.downloader.download(filename, params, async=False)
            else:
                self.downloader.download(filename, params)
        else:
            if "apierror" in video:
                self.utils.showMessage(self.language(30625), video["apierror"])
            else:
                self.utils.showMessage(self.language(30625), "ERROR")

    def addToFavorites(self, params={}):
        self.common.log("", 5)
        get = params.get
        if (get("videoid")):
            (message, status) = self.core.add_favorite(params)
            if status != 200:
                self.utils.showErrorMessage(self.language(30020), message, status)
                self.common.log("Error", 5)
                return False
        self.common.log("Done", 5)
        return True

    def removeFromFavorites(self, params={}):
        self.common.log("", 5)
        get = params.get

        if (get("editid")):
            (message, status) = self.core.delete_favorite(params)
            if status != 200:
                self.utils.showErrorMessage(self.language(30020), message, status)
                return False
            self.xbmc.executebuiltin("Container.Refresh")

        self.common.log("Done", 5)
        return True

    def addContact(self, params={}):
        self.common.log("", 5)
        get = params.get

        if not get("contact"):
            contact = self.common.getUserInput(self.language(30519), '')
            params["contact"] = contact

        if (get("contact")):
            (result, status) = self.core.add_contact(params)
            if status != 200:
                self.utils.showErrorMessage(self.language(30029), result, status)
                return False
            self.utils.showMessage(self.language(30613), get("contact"))
            self.xbmc.executebuiltin("Container.Refresh")

        self.common.log("Done", 5)
        return True

    def removeContact(self, params={}):
        self.common.log("", 5)
        get = params.get

        if (get("contact")):
            (result, status) = self.core.remove_contact(params)
            if status != 200:
                self.utils.showErrorMessage(self.language(30029), result, status)
                return False

            self.utils.showMessage(self.language(30614), get("contact"))
            self.xbmc.executebuiltin("Container.Refresh")
        return True

    def addSubscription(self, params={}):
        self.common.log("", 5)
        get = params.get
        if (get("channel")):
            (message, status) = self.core.add_subscription(params)
            if status != 200:
                self.utils.showErrorMessage(self.language(30021), message, status)
                return False
        self.common.log("Done", 5)
        return True

    def removeSubscription(self, params={}):
        self.common.log("", 5)
        get = params.get
        if (get("editid")):
            (message, status) = self.core.remove_subscription(params)
            if status != 200:
                self.utils.showErrorMessage(self.language(30021), message, status)
                return False

            self.xbmc.executebuiltin("Container.Refresh")
        self.common.log("Done", 5)
        return True

    #================================== List Item manipulation =========================================
    # is only used by List Menu
    def addListItem(self, params={}, item_params={}):
        self.common.log("", 5)
        item = item_params.get

        if (not item("action")):
            if (item("login") == "false"):
                self.addFolderListItem(params, item_params)
            else:
                if (len(self.settings.getSetting("oauth2_access_token")) > 0):
                    self.addFolderListItem(params, item_params)
        else:
            if (item("action") == "settings"):
                if (len(self.settings.getSetting("oauth2_access_token")) > 0):
                    if (item("login") == "true"):
                        self.addActionListItem(params, item_params)
                else:
                    if (item("login") == "false"):
                        self.addActionListItem(params, item_params)
            elif (item("action") == "play_video"):
                self.addVideoListItem(params, item_params, 0)
            else:
                self.addActionListItem(params, item_params)
        self.common.log("Done", 5)

    # common function for adding folder items
    def addFolderListItem(self, params={}, item_params={}, size=0):
        self.common.log("", 5)
        item = item_params.get

        icon = "DefaultFolder.png"
        if item("icon"):
            icon = self.utils.getThumbnail(item("icon"))

        thumbnail = item("thumbnail")

        cm = self.addFolderContextMenuItems(params, item_params)

        if (item("thumbnail", "DefaultFolder.png").find("http://") == - 1):
            thumbnail = self.utils.getThumbnail(item("thumbnail"))

        listitem = self.xbmcgui.ListItem(item("Title"), iconImage=icon, thumbnailImage=thumbnail)
        url = '%s?path=%s&' % (sys.argv[0], item("path"))
        url = self.utils.buildItemUrl(item_params, url)

        if len(cm) > 0:
            listitem.addContextMenuItems(cm, replaceItems=False)

        listitem.setProperty("Folder", "true")
        if (item("feed") == "downloads"):
            url = self.settings.getSetting("download_path")
        self.xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=True, totalItems=size)
        self.common.log("Done", 5)

    # common function for adding action items
    def addActionListItem(self, params={}, item_params={}, size=0):
        self.common.log("", 5)
        item = item_params.get
        folder = True
        icon = "DefaultFolder.png"
        thumbnail = self.utils.getThumbnail(item("thumbnail"))
        listitem = self.xbmcgui.ListItem(item("Title"), iconImage=icon, thumbnailImage=thumbnail)

        if (item("action") == "playbyid"):
            folder = False
            listitem.setProperty('IsPlayable', 'true')

        url = '%s?path=%s&' % (sys.argv[0], item("path"))
        url += 'action=' + item("action") + '&'

        self.xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=folder, totalItems=size)
        self.common.log("Done", 5)

    # common function for adding video items
    def addVideoListItem(self, params={}, item_params={}, listSize=0):
        self.common.log("", 5)
        get = params.get
        item = item_params.get

        icon = item("icon", "default")
        if(get("scraper", "").find("music") > -1):
            icon = "music"
        elif(get("scraper", "").find("disco") > -1):
            icon = "discoball"
        elif(get("feed", "").find("live") > -1):
            icon = "live"

        icon = self.utils.getThumbnail(icon)

        listitem = self.xbmcgui.ListItem(item("Title"), iconImage=icon, thumbnailImage=item("thumbnail"))

        url = '%s?path=%s&action=play_video&videoid=%s' % (sys.argv[0], "/root/video", item("videoid"))

        if get("user_feed") == "watch_later":
            url += "&watch_later=true&playlist_entry_id=%s&" % item("playlist_entry_id")

        cm = self.addVideoContextMenuItems(params, item_params)

        listitem.addContextMenuItems(cm, replaceItems=True)

        listitem.setProperty("Video", "true")
        listitem.setProperty("IsPlayable", "true")
        listitem.setInfo(type='Video', infoLabels=item_params)
        self.xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=False, totalItems=listSize + 1)
        self.common.log("Done", 5)

    #==================================== Core Output Parsing Functions ===========================================

    # Parses a folder list consisting of a tuple of dictionaries
    def parseFolderList(self, params, results):
        self.common.log("", 5)
        listSize = len(results)
        get = params.get

        cache = True
        if get("store") or get("user_feed"):
            cache = False

        for result_params in results:
            result_params["path"] = get("path")
            self.addFolderListItem(params, result_params, listSize + 1)

        self.xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True, cacheToDisc=cache)
        self.common.log("Done", 5)

    # parses a video list consisting of a tuple of dictionaries
    def parseVideoList(self, params, results):
        self.common.log("", 5)
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
                self.addVideoListItem(params, result_params, listSize)

        video_view = int(self.settings.getSetting("list_view")) <= 1
        if (video_view):
            self.xbmc.executebuiltin("Container.SetViewMode(500)")

        self.xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=self.xbmcplugin.SORT_METHOD_UNSORTED)
        self.xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=self.xbmcplugin.SORT_METHOD_LABEL)
        self.xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=self.xbmcplugin.SORT_METHOD_VIDEO_RATING)
        self.xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=self.xbmcplugin.SORT_METHOD_DATE)
        self.xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=self.xbmcplugin.SORT_METHOD_PROGRAM_COUNT)
        self.xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=self.xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
        self.xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=self.xbmcplugin.SORT_METHOD_GENRE)

        self.xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True, cacheToDisc=True)
        self.common.log("Done", 5)

    def addVideoContextMenuItems(self, params={}, item_params={}):
        self.common.log("", 5)
        cm = []
        get = params.get
        item = item_params.get

        title = self.common.makeAscii(item("Title"))
        url_title = urllib.quote_plus(title)
        studio = self.common.makeAscii(item("Studio", "Unknown Author"))
        url_studio = urllib.quote_plus(studio)

        cm.append((self.language(30504), "XBMC.Action(Queue)",))

        if (get("playlist")):
            cm.append((self.language(30521), "XBMC.RunPlugin(%s?path=%s&action=play_all&playlist=%s&videoid=%s&)" % (sys.argv[0], item("path"), get("playlist"), item("videoid"))))

        if (get("user_feed") == "newsubscriptions" or get("user_feed") == "favorites"):
            contact = "default"
            if get("contact"):
                contact = get("contact")
            cm.append((self.language(30521), "XBMC.RunPlugin(%s?path=%s&action=play_all&user_feed=%s&contact=%s&videoid=%s&)" % (sys.argv[0], item("path"), get("user_feed"), contact, item("videoid"))))

        cm.append((self.language(30501), "XBMC.RunPlugin(%s?path=%s&action=download&videoid=%s)" % (sys.argv[0], item("path"), item("videoid"))))

        if (self.settings.getSetting("username") != "" and self.settings.getSetting("oauth2_access_token")):
            if (get("user_feed") == "favorites" and not get("contact")):
                cm.append((self.language(30506), 'XBMC.RunPlugin(%s?path=%s&action=remove_favorite&editid=%s&)' % (sys.argv[0], item("path"), item("editid"))))
            else:
                cm.append((self.language(30503), 'XBMC.RunPlugin(%s?path=%s&action=add_favorite&videoid=%s&)' % (sys.argv[0], item("path"), item("videoid"))))

            if (get("external") == "true" or (get("feed") not in ["subscriptions_favorites", "subscriptions_uploads", "subscriptions_playlists"] and (get("user_feed") != "uploads" and not get("external")))):
                cm.append((self.language(30512) % studio, 'XBMC.RunPlugin(%s?path=%s&channel=%s&action=add_subscription)' % (sys.argv[0], item("path"), url_studio)))

            if (get("playlist") and item("playlist_entry_id")):
                cm.append((self.language(30530), "XBMC.RunPlugin(%s?path=%s&action=remove_from_playlist&playlist=%s&playlist_entry_id=%s&)" % (sys.argv[0], item("path"), get("playlist"), item("playlist_entry_id"))))
            cm.append((self.language(30528), "XBMC.RunPlugin(%s?path=%s&action=add_to_playlist&videoid=%s&)" % (sys.argv[0], item("path"), item("videoid"))))

        if (get("feed") != "uploads" and get("user_feed") != "uploads"):
            cm.append((self.language(30516) % studio, "XBMC.Container.Update(%s?path=%s&feed=uploads&channel=%s)" % (sys.argv[0], get("path"), url_studio)))

        cm.append((self.language(30514), "XBMC.Container.Update(%s?path=%s&feed=search&search=%s)" % (sys.argv[0], get("path"), url_title)))
        cm.append((self.language(30527), "XBMC.Container.Update(%s?path=%s&feed=related&videoid=%s)" % (sys.argv[0], get("path"), item("videoid"))))
        cm.append((self.language(30523), "XBMC.ActivateWindow(VideoPlaylist)"))
        cm.append((self.language(30502), "XBMC.Action(Info)",))

        self.common.log("Done", 5)
        return cm

    def addFolderContextMenuItems(self, params={}, item_params={}):
        self.common.log("", 5)
        cm = []
        get = params.get
        item = item_params.get

        if (item("next", "false") == "true"):
            return cm

        if (item("user_feed") in ["favorites", "newsubscriptions", "watch_later", "recommended"]):
            cm.append((self.language(30520), "XBMC.RunPlugin(%s?path=%s&action=play_all&user_feed=%s&contact=%s&login=true&)" % (sys.argv[0], item("path"), item("user_feed"), "default")))
            cm.append((self.language(30522), "XBMC.RunPlugin(%s?path=%s&action=play_all&shuffle=true&user_feed=%s&contact=%s&login=true&)" % (sys.argv[0], item("path"), item("user_feed"), "default")))

        if item("scraper") in ["liked_videos"]:
            cm.append((self.language(30520), "XBMC.RunPlugin(%s?path=%s&action=play_all&scraper=%s&login=true&)" % (sys.argv[0], item("path"), item("scraper"))))
            cm.append((self.language(30522), "XBMC.RunPlugin(%s?path=%s&action=play_all&shuffle=true&scraper=%s&login=true&)" % (sys.argv[0], item("path"), item("scraper"))))

        if (item("playlist")):
            cm.append((self.language(30531), "XBMC.RunPlugin(%s?path=%s&action=reverse_order&playlist=%s&)" % (sys.argv[0], item("path"), item("playlist"))))
            cm.append((self.language(30520), "XBMC.RunPlugin(%s?path=%s&action=play_all&user_feed=playlist&playlist=%s&)" % (sys.argv[0], item("path"), item("playlist"))))
            cm.append((self.language(30522), "XBMC.RunPlugin(%s?path=%s&action=play_all&user_feed=playlist&shuffle=true&playlist=%s&)" % (sys.argv[0], item("path"), item("playlist"))))
            if not get("external"):
                cm.append((self.language(30539), "XBMC.RunPlugin(%s?path=%s&action=delete_playlist&playlist=%s&)" % (sys.argv[0], item("path"), item("playlist"))))

        if (item("scraper") == "music_top100"):
            cm.append((self.language(30520), "XBMC.RunPlugin(%s?path=%s&action=play_all&scraper=music_top100&)" % (sys.argv[0], item("path"))))
            cm.append((self.language(30522), "XBMC.RunPlugin(%s?path=%s&action=play_all&shuffle=true&scraper=music_top100&)" % (sys.argv[0], item("path"))))

        if (item("scraper") == "search_disco"):
            cm.append((self.language(30520), "XBMC.RunPlugin(%s?path=%s&action=play_all&scraper=search_disco&search=%s&)" % (sys.argv[0], item("path"), item("search"))))
            cm.append((self.language(30522), "XBMC.RunPlugin(%s?path=%s&action=play_all&shuffle=true&scraper=search_disco&search=%s&)" % (sys.argv[0], item("path"), item("search"))))
            if not get("scraper") == "disco_top_artist":
                cm.append((self.language(30524), 'XBMC.Container.Update(%s?path=%s&action=edit_disco&store=disco_searches&search=%s&)' % (sys.argv[0], item("path"), item("search"))))
                cm.append((self.language(30525), 'XBMC.RunPlugin(%s?path=%s&action=delete_disco&store=disco_searches&delete=%s&)' % (sys.argv[0], item("path"), item("search"))))

        if (item("feed") == "search"):
            cm.append((self.language(30515), 'XBMC.Container.Update(%s?path=%s&action=edit_search&store=searches&search=%s&)' % (sys.argv[0], item("path"), item("search"))))
            cm.append((self.language(30508), 'XBMC.RunPlugin(%s?path=%s&action=delete_search&store=searches&delete=%s&)' % (sys.argv[0], item("path"), item("search"))))

        if (item("view_mode")):
            cm_url = 'XBMC.Container.Update(%s?path=%s&channel=%s&action=change_subscription_view&view_mode=%s&' % (sys.argv[0], item("path"), item("channel"), "%s")
            if (item("external")):
                cm_url += "external=true&contact=" + get("contact") + "&"
            cm_url += ")"

            if (item("user_feed") == "favorites"):
                cm.append((self.language(30511), cm_url % ("uploads")))
                cm.append((self.language(30526), cm_url % ("playlists&folder=true")))
            elif(item("user_feed") == "playlists"):
                cm.append((self.language(30511), cm_url % ("uploads")))
                cm.append((self.language(30510), cm_url % ("favorites")))
            elif (item("user_feed") == "uploads"):
                cm.append((self.language(30510), cm_url % ("favorites")))
                cm.append((self.language(30526), cm_url % ("playlists&folder=true")))

        if (item("channel") or item("contact")):
            if (self.settings.getSetting("username") != "" and self.settings.getSetting("oauth2_access_token")):
                title = self.common.makeAscii(item("channel", ""))
                if (get("external")):
                    channel = get("channel", "")
                    if not channel:
                        channel = get("contact")
                    cm.append((self.language(30512) % title, 'XBMC.RunPlugin(%s?path=%s&channel=%s&action=add_subscription)' % (sys.argv[0], item("path"), channel)))
                elif item("editid"):
                    cm.append((self.language(30513) % title, 'XBMC.RunPlugin(%s?path=%s&editid=%s&action=remove_subscription)' % (sys.argv[0], item("path"), item("editid"))))

        if (item("contact") and not get("store")):
            if (self.pluginsettings.userHasProvidedValidCredentials()):
                if (item("external")):
                    cm.append((self.language(30026), 'XBMC.RunPlugin(%s?path=%s&action=add_contact&contact=%s&)' % (sys.argv[0], item("path"), item("Title"))))
                else:
                    cm.append((self.language(30025), 'XBMC.RunPlugin(%s?path=%s&action=remove_contact&contact=%s&)' % (sys.argv[0], item("path"), item("Title"))))

        cm.append((self.language(30523), "XBMC.ActivateWindow(VideoPlaylist)"))
        self.common.log("Done", 5)
        return cm
