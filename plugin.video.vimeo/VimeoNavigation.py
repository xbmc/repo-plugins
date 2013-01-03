'''
   Vimeo plugin for XBMC
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
import os


class VimeoNavigation():
    def __init__(self):
        self.utils = sys.modules["__main__"].utils
        self.player = sys.modules["__main__"].player
        self.feeds = sys.modules["__main__"].feeds
        self.core = sys.modules["__main__"].core
        self.login = sys.modules["__main__"].login
        self.common = sys.modules["__main__"].common
        self.storage = sys.modules["__main__"].storage
        self.downloader = sys.modules["__main__"].downloader
        self.playlist = sys.modules["__main__"].playlist

        self.xbmc = sys.modules["__main__"].xbmc
        self.xbmcgui = sys.modules["__main__"].xbmcgui
        self.xbmcplugin = sys.modules["__main__"].xbmcplugin
        self.xbmcvfs = sys.modules["__main__"].xbmcvfs
        self.settings = sys.modules["__main__"].settings
        self.language = sys.modules["__main__"].language
        self.plugin = sys.modules["__main__"].plugin
        self.dbg = sys.modules["__main__"].dbg

        # we fill the list with category definitions, with labels from the appropriate language file
        #         Title                        , path                                           , thumbnail                         ,  login          ,  source / action
        self.categories = (
                {'Title':self.language(30001)  ,'path':"/root/explore"							, 'thumbnail':"explore"        		, 'login':"false" },
                {'Title':self.language(30013)  ,'path':"/root/explore/channels"					, 'thumbnail':"explore"             , 'login':"false" , 'api':"channels" , 'folder':'category'},
            	{'Title':self.language(30014)  ,'path':"/root/explore/groups"					, 'thumbnail':"explore"             , 'login':"false" , 'api':"groups" , 'folder':'category'},
                {'Title':self.language(30015)  ,'path':"/root/explore/categories"				, 'thumbnail':"explore"             , 'login':"false" , 'api':"categories" , 'folder':'category'},
                {'Title':self.language(30016)  ,'path':"/root/explore/hd"						, 'thumbnail':"explore"             , 'login':"false" , 'channel':"hd"},
                {'Title':self.language(30017)  ,'path':"/root/explore/staffpicks"               , 'thumbnail':"explore"             , 'login':"false" , 'channel':"staffpicks"},
                {'Title':self.language(30002)  ,'path':"/root/my_likes"                			, 'thumbnail':"favorites"           , 'login':"true"  , 'api':"my_likes"},
                {'Title':self.language(30012)  ,'path':"/root/my_contacts"                      , 'thumbnail':"contacts"            , 'login':"true"  , 'api':"my_contacts" , 'folder':'contact'},
                {'Title':self.language(30009)  ,'path':"/root/my_albums"                        , 'thumbnail':"playlists"           , 'login':"true"  , 'api':"my_albums" , 'folder':'album'},
                {'Title':self.language(30033)  ,'path':"/root/my_albums/new"                    , 'thumbnail':"playlists"           , 'login':"true"  , 'action':"create_album"},
                {'Title':self.language(30031)  ,'path':'/root/my_watch_later'                   , 'thumbnail':"watch_later"         , 'login':"true"  , 'api':"my_watch_later"},
                {'Title':self.language(30010)  ,'path':"/root/my_groups"                        , 'thumbnail':"network"             , 'login':"true"  , 'api':"my_groups" , 'folder':'group'},
                {'Title':self.language(30003)  ,'path':"/root/subscriptions"                    , 'thumbnail':"subscriptions"       , 'login':"true"  , 'api':"my_channels" , 'folder':'channel'},
                {'Title':self.language(30004)  ,'path':"/root/subscriptions/new"                , 'thumbnail':"newsubscriptions"	, 'login':"true"  , 'api':"my_newsubscriptions"},
                {'Title':self.language(30005)  ,'path':"/root/my_videos"                        , 'thumbnail':"uploads"             , 'login':"true"  , 'api':"my_videos"},
                {'Title':self.language(30032)  ,'path':"/root/downloads"                        , 'thumbnail':"downloads"           , 'login':"false" , 'feed':"downloads"},
                {'Title':self.language(30006)  ,'path':"/root/search"                           , 'thumbnail':"search"              , 'login':"false" , 'store':"searches" , 'folder':'true'},
                {'Title':self.language(30007)  ,'path':"/root/search/new"                       , 'thumbnail':"search"              , 'login':"false" , 'api':"search"},
                {'Title':self.language(30027)  ,'path':"/root/login"                            , 'thumbnail':"login"               , 'login':"false" , 'action':"settings"},
                {'Title':self.language(30028)  ,'path':"/root/settings"                         , 'thumbnail':"settings"            , 'login':"true"  , 'action':"settings"}
               )

    #==================================== Main Entry Points===========================================
    def listMenu(self, params={}):
        self.common.log(repr(params), 5)
        get = params.get
        cache = True

        path = get("path", "/root")
        if get("api") not in ["search", "related"] and not get("channel") and not get("contact") and not get("playlist") and get("page", "0") == "0":
            for category in self.categories:
                cat_get = category.get
                if (cat_get("path").find(path + "/") > - 1):
                    if (cat_get("path").rfind("/") <= len(path + "/")):
                        setting = self.settings.getSetting(cat_get("path").replace("/root/explore/", "").replace("/root/", ""))
                        if not setting or setting == "true":
                            if (cat_get("feed") == "downloads"):
                                if (self.settings.getSetting("downloadPath")):
                                    self.addListItem(params, category)
                            else:
                                self.addListItem(params, category)

        if (get("feed") or get("api") or get("options") or get("store") or get("scraper") or get("channel") or get("album") or get("group")):
            return self.list(params)

        video_view = self.settings.getSetting("list_view") == "1"

        if (video_view):
            self.xbmc.executebuiltin("Container.SetViewMode(500)")

        self.xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True, cacheToDisc=cache)
        self.common.log("Done", 5)

    def list(self, params={}):
        self.common.log("")
        get = params.get
        results = []
        
        if get("scraper"):
            (results, status) = self.scraper.scrape(params)
        else:
            (results, status) = self.feeds.list(params)

        if status == 200:
            if get("folder", "false") != "false":
                self.parseFolderList(params, results)
            else:
                self.parseVideoList(params, results)
            return True
        else:
            self.showListingError(params)
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
                (get("api") and cat_get("api") == get("api")) or
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

    def executeAction(self, params={}):
        self.common.log(repr(params))
        get = params.get
        if (get("action") == "play_video"):
            self.player.playVideo(params)
        if (get("action") in ["delete_search"]):
            self.storage.deleteStoredSearch(params)
        if (get("action") in ["edit_search"]):
            self.storage.editStoredSearch(params)
            self.listMenu(params)
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
        if (get("action") == "download"):
            self.downloadVideo(params)
        if (get("action") == "play_all"):
            self.playlist.playAll(params)
        if (get("action") == "add_to_album"):
            self.playlist.addToAlbum(params)
        if (get("action") == "remove_from_album"):
            self.playlist.removeFromAlbum(params)
        if (get("action") == "delete_album"):
            self.playlist.deleteAlbum(params)
        if (get("action") == "reverse_order"):
            self.storage.reversePlaylistOrder(params)
        if (get("action") == "create_album"):
            self.playlist.createAlbum(params)


    #================================== Plugin Actions =========================================

    def setLike(self, params={}):
        self.common.log("")
        get = params.get

        if (get("videoid")):
            (message, status) = self.core.setLike(params)
            if status != 200:
                self.utils.showErrorMessage(self.language(30020), message, status)
                return False

            if (get("action") == "remove_favorite"):
                self.xbmc.executebuiltin("Container.Refresh")
            return True

    def downloadVideo(self, params):
        self.common.log("")
        get = params.get

        if not self.settings.getSetting("downloadPath"):
            self.common.log("Download path missing. Opening settings")
            self.utils.showMessage(self.language(30600), self.language(30611))
            self.settings.openSettings()

        download_path = self.settings.getSetting("downloadPath")
        self.common.log("path: " + repr(download_path))
        (video, status) = self.player.getVideoObject(params)
        if "video_url" in video and download_path:
            params["Title"] = video['Title']
            params["url"] = video['video_url']
            params["download_path"] = download_path
            filename = u"%s-[%s].mp4" % (u''.join(c for c in video['Title'] if c not in self.utils.INVALID_CHARS), video["videoid"])
            if get("async"):
                self.downloader.download(filename, params, async=False)
            else:
                self.downloader.download(filename, params)
        elif "apierror" in video:
            self.utils.showMessage(self.language(30625), video["apierror"])
        else:
            self.utils.showMessage(self.language(30625), "ERROR")

        self.common.log("Done")

    def updateContact(self, params={}):
        self.common.log("")
        get = params.get

        if (not get("contact")):
            params["contact"] = self.common.getUserInput(self.language(30026), '')

        if (get("contact")):
            (result, status) = self.core.updateContact(params)
            if status != 200:
                self.utils.showErrorMessage(self.language(30029), result, status)
                return False

            self.utils.showMessage(self.language(30614), get("contact"))
            self.xbmc.executebuiltin("Container.Refresh")

    def updateGroup(self, params={}):
        self.common.log("")
        get = params.get

        if (get("group")):
            (result, status) = self.core.updateGroup(params)
            if status != 200:
                self.utils.showErrorMessage(self.language(30029), result, status)
                return False
            if (get("action") == "leave_group"):
                self.xbmc.executebuiltin("Container.Refresh")
        return True

    def updateSubscription(self, params={}):
        self.common.log("")
        get = params.get
        if (get("channel")):
            (message, status) = self.core.updateSubscription(params)
            if status != 200:
                self.utils.showErrorMessage(self.language(30021), message, status)
                return False
            else:
                if (get("action") == "remove_subscription"):
                    self.xbmc.executebuiltin("Container.Refresh")
        return True

    def removeWatchLater(self, params={}):
        self.common.log("")
        get = params.get

        if (get("videoid")):
            (result, status) = self.core.removeWatchLater(params)
            if status == 200:
                self.xbmc.executebuiltin("Container.Refresh")

        return True

    #================================== List Item manipulation =========================================
    # is only used by List Menu
    def addListItem(self, params={}, item_params={}):
        item = item_params.get

        if (not item("action")):
            if (item("login") == "false"):
                self.addFolderListItem(params, item_params)
            else:
                if (len(self.settings.getSetting("userid")) > 0):
                    self.addFolderListItem(params, item_params)
        else:
            if (item("action") == "settings"):
                if (len(self.settings.getSetting("userid")) > 0):
                    if (item("login") == "true"):
                        self.addActionListItem(params, item_params)
                else:
                    if (item("login") == "false"):
                        self.addActionListItem(params, item_params)
            else:
                self.addActionListItem(params, item_params)

    # common function for adding folder items
    def addFolderListItem(self, params={}, item_params={}, size=0):
        self.common.log("", 5)
        item = item_params.get

        icon = "DefaultFolder.png"
        if item("icon"):
            icon = self.utils.getThumbnail(item("icon"))

        thumbnail = item("thumbnail", "DefaultFolder.png")
        if (thumbnail.find("http://") == -1):
                thumbnail = self.utils.getThumbnail(thumbnail)

        cm = self.addFolderContextMenuItems(params, item_params)

        listitem = self.xbmcgui.ListItem(item("Title"), iconImage=icon, thumbnailImage=thumbnail)
        url = '%s?path=%s&' % (sys.argv[0], item("path"))
        url += self.utils.buildItemUrl(item_params)

        if len(cm) > 0:
                listitem.addContextMenuItems(cm, replaceItems=False)
        listitem.setProperty("Folder", "true")

        if (item("feed") == "downloads"):
                url = self.settings.getSetting("downloadPath")
        self.xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=True, totalItems=size)

    # common function for adding action items
    def addActionListItem(self, params={}, item_params={}, size=0):
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

    # common function for adding video items
    def addVideoListItem(self, params={}, item_params={}, listSize=0):
        get = params.get
        item = item_params.get

        icon = item("icon","default")
        icon = self.utils.getThumbnail(icon)

        listitem = self.xbmcgui.ListItem(item("Title"), iconImage=icon, thumbnailImage=item("thumbnail"))

        url = '%s?path=%s&action=play_video&videoid=%s' % (sys.argv[0], item("path"), item("videoid"))
        cm = self.addVideoContextMenuItems(params, item_params)

        listitem.addContextMenuItems(cm, replaceItems=True)

        listitem.setProperty("Video", "true")
        listitem.setProperty("IsPlayable", "true")
        listitem.setInfo(type='Video', infoLabels=item_params)

        self.xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=False, totalItems=listSize + 1)

    #==================================== Core Output Parsing Functions ===========================================
    #parses a folder list consisting of a tuple of dictionaries
    def parseFolderList(self, params, results):
        self.common.log("")
        listSize = len(results)
        get = params.get

        for result_params in results:
            result = result_params.get

            if (get("api") == "my_contacts"):
                result_params["feed"] = "contact_option_list"

            result_params["path"] = get("path")
            
            self.addFolderListItem(params, result_params, listSize)

        cache = False

        if (get("scraper")):
            cache = True

        self.xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True, cacheToDisc=cache)

    #parses a video list consisting of a tuple of dictionaries
    def parseVideoList(self, params, results):
        self.common.log(str(len(results)))
        listSize = len(results)
        get = params.get

        for result_params in results:
            result_params["path"] = get("path")
            result = result_params.get

            if result("videoid") == "false":
                continue

            if get("api") == "my_watch_later":
                result_params["index"] = str(results.index(result_params) + 1)

            if result("next") == "true":
                self.addFolderListItem(params, result_params, listSize)
            else:
                self.addVideoListItem(params, result_params, listSize)

        video_view = int(self.settings.getSetting("list_view")) <= 1
        if (video_view):
            self.xbmc.executebuiltin("Container.SetViewMode(500)")

        if (video_view):
            self.common.log("setting view mode")
            self.xbmc.executebuiltin("Container.SetViewMode(500)")

        self.xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=self.xbmcplugin.SORT_METHOD_UNSORTED)
        self.xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=self.xbmcplugin.SORT_METHOD_LABEL)
        self.xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=self.xbmcplugin.SORT_METHOD_VIDEO_RATING)
        self.xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=self.xbmcplugin.SORT_METHOD_DATE)
        self.xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=self.xbmcplugin.SORT_METHOD_PROGRAM_COUNT)
        self.xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=self.xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
        self.xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=self.xbmcplugin.SORT_METHOD_GENRE)

        self.xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True, cacheToDisc=True)

    def addVideoContextMenuItems(self, params={}, item_params={}):
        cm = []
        get = params.get
        item = item_params.get

        title = item("Title", "Unknown Title")
        title = self.common.makeAscii(title)

        if (self.settings.getSetting("userid")):
            if (get("api") == "my_likes" and not get("contact")):
                cm.append((self.language(30504) % title, 'XBMC.RunPlugin(%s?path=%s&action=remove_favorite&videoid=%s&)' % (sys.argv[0], get("path"), item("videoid"))))
            else:
                cm.append((self.language(30503) % title, 'XBMC.RunPlugin(%s?path=%s&action=add_favorite&videoid=%s&)' % (sys.argv[0], get("path"), item("videoid"))))

        if (get("api") in ["my_videos", "my_watch_later", "my_newsubscriptions", "my_likes"]):
            cm.append((self.language(30532), 'XBMC.RunPlugin(%s?path=%s&action=play_all&api=%s&videoid=%s&)' % (sys.argv[0], get("path"), get("api"), item("videoid"))))

        if (item("contact")):
            author = self.common.makeAscii(item("Studio","Unknown user"))
            cm.append((self.language(30536) % author, "XBMC.Container.Update(%s?path=%s&api=my_videos&contact=%s)" % (sys.argv[0], get("path"), item("contact") )))

        if (get("album")):
            if self.settings.getSetting("userid") and not get("external"):
                cm.append((self.language(30534), 'XBMC.RunPlugin(%s?path=%s&action=remove_from_album&album=%s&videoid=%s&)' % (sys.argv[0], get("path"), get("album"), item("videoid"))))
            cm.append((self.language(30532), 'XBMC.RunPlugin(%s?path=%s&action=play_all&album=%s&videoid=%s&)' % (sys.argv[0], get("path"), get("album"), item("videoid"))))
        elif (self.settings.getSetting("userid")):
            cm.append((self.language(30533), 'XBMC.RunPlugin(%s?path=%s&action=add_to_album&videoid=%s&)' % (sys.argv[0], get("path"), item("videoid"))))

        if (get("api") == "my_watch_later"):
            cm.append((self.language(30529), "XBMC.RunPlugin(%s?path=%s&action=remove_watch_later&videoid=%s)" % (sys.argv[0], get("path"), item("videoid"))))
        else:
            cm.append((self.language(30530), "XBMC.RunPlugin(%s?path=%s&action=add_watch_later&videoid=%s)" % (sys.argv[0], get("path"), item("videoid"))))

        cm.append((self.language(30500), "XBMC.RunPlugin(%s?path=%s&action=download&videoid=%s)" % (sys.argv[0], get("path"), item("videoid"))))
        cm.append((self.language(30507), "XBMC.Container.Update(%s?path=%s&action=search&search=%s)" % (sys.argv[0], get("path"), urllib.quote_plus(self.common.makeAscii(title)))))
        cm.append((self.language(30502), "XBMC.Action(Queue)",))
        cm.append((self.language(30501), "XBMC.Action(Info)",))

        return cm

    def addFolderContextMenuItems(self, params={}, item_params={}):
        cm = []
        get = params.get
        item = item_params.get

        if (item("next", "false") == "true"):
            return cm

        title = item("Title", "Unknown Title")
        title = self.common.makeAscii(title)

        if (item("channel") and self.settings.getSetting("userid")):
            if (get("external") or get("api") != "my_channels"):
                cm.append((self.language(30512) % title, 'XBMC.RunPlugin(%s?path=%s&channel=%s&action=add_subscription)' % (sys.argv[0], get("path"), item("channel"))))
            else:
                cm.append((self.language(30513) % title, 'XBMC.RunPlugin(%s?path=%s&channel=%s&action=remove_subscription)' % (sys.argv[0], get("path"), item("channel"))))

        if (item("group") and self.settings.getSetting("userid")):
            if (item("external") or get("api") != "my_groups"):
                cm.append((self.language(30510) % title, 'XBMC.RunPlugin(%s?path=%s&group=%s&action=join_group)' % (sys.argv[0], get("path"), item("group"))))
            else:
                cm.append((self.language(30511) % title, 'XBMC.RunPlugin(%s?path=%s&group=%s&action=leave_group)' % (sys.argv[0], get("path"), item("group"))))

        if (item("api") in ["my_videos", "my_watch_later", "my_newsubscriptions", "my_likes"]):
            cm.append((self.language(30531), 'XBMC.RunPlugin(%s?path=%s&action=play_all&api=%s&)' % (sys.argv[0], get("path"), item("api"))))

        if (item("album")):
            cm.append((self.language(30531), 'XBMC.RunPlugin(%s?path=%s&action=play_all&album=%s&)' % (sys.argv[0], get("path"), item("album"))))

        if (item("api") == "my_likes"  or item("album") or item("api") == "my_videos"):
            cm.append((self.language(30514), "XBMC.Action(Queue)"))

        if (item("album") and self.settings.getSetting("userid") and not item("external")):
            cm.append((self.language(30535), 'XBMC.RunPlugin(%s?path=%s&action=delete_album&album=%s&)' % (sys.argv[0], get("path"), item("album"))))

        if (item("search")):
            cm.append((self.language(30508), 'XBMC.RunPlugin(%s?path=%s&action=delete_search&store=searches&delete=%s&)' % (sys.argv[0], item("path"), item("search"))))
            cm.append((self.language(30506), 'XBMC.Container.Update(%s?path=%s&action=edit_search&store=searches&search=%s&)' % (sys.argv[0], item("path"), item("search"))))

        return cm
