'''
   BlipTV plugin for XBMC
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
import urllib


class BlipTVNavigation:
    def __init__(self):
        self.settings = sys.modules["__main__"].settings
        self.plugin = sys.modules["__main__"].plugin
        self.language = sys.modules["__main__"].language
        self.dbg = sys.modules["__main__"].dbg

        self.player = sys.modules["__main__"].player
        self.downloader = sys.modules["__main__"].downloader
        self.storage = sys.modules["__main__"].storage
        self.scraper = sys.modules["__main__"].scraper
        self.common = sys.modules["__main__"].common
        self.utils = sys.modules["__main__"].utils
        self.xbmc = sys.modules["__main__"].xbmc
        self.xbmcgui = sys.modules["__main__"].xbmcgui
        self.xbmcplugin = sys.modules["__main__"].xbmcplugin

        # This list contains the main menu structure the user first encounters when running the plugin
        #                           label                                                  , path                                                                                , thumbnail                                        ,  scraper / action
        self. categories = (
            {'Title':self.language(30016)  ,'path':"/root/explore"                                                         , 'thumbnail':"explore"                },
            {'Title':self.language(30001)  ,'path':"/root/explore/browse"                                        , 'thumbnail':"explore"                , 'scraper': 'browse_shows' },
            {'Title':self.language(30002)  ,'path':"/root/explore/staffpicks"                                , 'thumbnail':"explore"                , 'scraper': 'staff_picks' },
            {'Title':self.language(30003)  ,'path':"/root/explore/favorites"                                , 'thumbnail':"explore"                , 'scraper': 'favorites' },
            {'Title':self.language(30004)  ,'path':"/root/explore/newshows"                                        , 'thumbnail':"explore"                , 'scraper': 'new_shows' },
            {'Title':self.language(30005)  ,'path':"/root/explore/popularshows"                                , 'thumbnail':"explore"                , 'scraper': 'popular_shows' },
            {'Title':self.language(30006)  ,'path':"/root/explore/trendingshow"                                , 'thumbnail':"explore"                , 'scraper': 'trending_shows' },
            {'Title':self.language(30007)  ,'path':"/root/explore/newepisodes"                                , 'thumbnail':"explore"                , 'scraper': 'new_episodes' },
            {'Title':self.language(30008)  ,'path':"/root/explore/popularepisodes"                        , 'thumbnail':"explore"                , 'scraper': 'popular_episodes' },
            {'Title':self.language(30009)  ,'path':"/root/explore/trendingepisodes"                        , 'thumbnail':"explore"                , 'scraper': 'trending_episodes' },
            {'Title':self.language(30010)  ,'path':"/root/my_favorites"                                                , 'thumbnail':"explore"                , 'store':   'favorites', 'folder':"true" },
            {'Title':self.language(30011)  ,'path':"/root/my_favorites/search"                                , 'thumbnail':"search"                , 'scraper': 'show_search', 'folder':"true" },
            {'Title':self.language(30012)  ,'path':"/root/downloads"                                                , 'thumbnail':"downloads"        , 'feed':    'downloads' },
            {'Title':self.language(30013)  ,'path':"/root/search"                                                        , 'thumbnail':"search"                , 'store':"searches", 'folder':'true' },
            {'Title':self.language(30014)  ,'path':"/root/search/new"                                                , 'thumbnail':"search"                , 'scraper': 'search'},                                  
            {'Title':self.language(30015)  ,'path':"/root/settings"                                                          , 'thumbnail':"settings"        , 'action':"settings" }
                                 )

    #==================================== Main Entry Points===========================================
    def listMenu(self, params={}):
        self.common.log("")
        get = params.get
        cache = True

        path = get("path", "/root")
        if not get("scraper") == "search" and not get("scraper") == "show_search" and get("page", "0") == "0" and not get("show"):
            for category in self.categories:
                cat_get = category.get
                if (cat_get("path").find(path + "/") > -1):
                    if (cat_get("path").rfind("/") <= len(path + "/")):
                        if (get("feed") == "downloads"):
                            if (self.settings.getSetting("downloadPath")):
                                self.addListItem(params, category)
                        else:
                            self.addListItem(params, category)

        if (get("store") or get("scraper")):
            return self.list(params)

        video_view = self.settings.getSetting("list_view") == "1"

        if (video_view):
            self.xbmc.executebuiltin("Container.SetViewMode(500)")

        self.xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True, cacheToDisc=cache)

    def executeAction(self, params={}):
        self.common.log("")
        get = params.get
        if (get("action") == "settings"):
            self.settings.openSettings()
        if (get("action") == "delete_search"):
            self.storage.deleteStoredSearch(params)
        if (get("action") == "edit_search"):
            self.storage.editStoredSearch(params)
            self.listMenu(params)
        if (get("action") == "add_favorite"):
            self.scraper.addShowToMyFavorites(params)
        if (get("action") == "delete_favorite"):
            self.storage.deleteFromMyFavoriteShows(params)
        if (get("action") == "download"):
            video = self.player.getVideoObject(params)
            if "video_url" in video:
                params["url"] = video['video_url']
                params["download_path"] = self.settings.getSetting("downloadPath")
                filename = "%s-[%s].mp4" % (''.join(c for c in video['Title'].decode("utf-8") if c not in self.utils.INVALID_CHARS), video["videoid"])
                self.downloader.download(filename, params)
            else:
                if "apierror" in video:
                    self.utils.showMessage(self.language(30625), video["apierror"])
                else:
                    self.utils.showMessage(self.language(30625), "ERROR")

        if (get("action") == "play_video"):
            self.player.playVideo(params)

    #==================================== Item Building and Listing ===========================================
    def list(self, params={}):
        self.common.log("list: " + repr(params))
        get = params.get
        results = []

        if get("scraper") in ["search", "show_search"]:
            if not get("search"):
                if get("scraper") == "search":
                    query = self.common.getUserInput(self.language(30013), '')
                else:
                    query = self.common.getUserInput(self.language(30011), '')
                    if not query:
                        return False
                params["search"] = query

                self.storage.saveSearch(params)

        if get("scraper"):
            results = self.scraper.scrape(params)
        elif get("store"):
            results = self.storage.list(params)

        if len(results) > 0:
            if get("folder"):
                self.common.log("found folder list")
                self.parseFolderList(params, results)
            else:
                self.common.log("found video list")
                self.parseVideoList(params, results)
            return True
        else:
            label = ""

            for category in self.categories:
                cat_get = category.get
                if (
                    (get("feed") and cat_get("feed") == get("feed")) or
                    (get("scraper") and cat_get("scraper") == get("scraper"))
                    ):
                    label = cat_get("Title")

                if label:
                    self.utils.showMessage(label, self.language(30601))
        return False
    #================================== List Item manipulation =========================================
    # is only used by List Menu
    def addListItem(self, params={}, item_params={}):
        self.common.log("")
        # get = params.get
        item = item_params.get

        if item("action") == "play_video":
            self.addVideoListItem(params, item_params, 0)
        elif item("action"):
            self.addActionListItem(params, item_params)
        else:
            self.addFolderListItem(params, item_params)

    # common function for adding folder items
    def addFolderListItem(self, params={}, item_params={}, size=0):
        # self.common.log("")
        # get = params.get
        item = item_params.get

        icon = "DefaultFolder.png"
        if item("icon"):
            icon = item("icon")

        thumbnail = item("thumbnail")

        if not item("thumbnail"):
            thumbnail = icon

        cm = self.addFolderContextMenuItems(params, item_params)

        if (item("thumbnail", "DefaultFolder.png").find("http://") == -1):
            thumbnail = self.utils.getThumbnail(item("thumbnail"))

        listitem = self.xbmcgui.ListItem(item("Title"), iconImage=icon, thumbnailImage=thumbnail)
        url = '%s?path=%s&' % (sys.argv[0], item("path"))
        url = self.utils.buildItemUrl(item_params, url)

        if len(cm) > 0:
            listitem.addContextMenuItems(cm, replaceItems=False)

        listitem.setProperty("Folder", "true")
        if (item("feed") == "downloads"):
            url = self.settings.getSetting("downloadPath")
        self.xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=True, totalItems=size)

    # common function for adding action items
    def addActionListItem(self, params={}, item_params={}, size=0):
        self.common.log("")
        item = item_params.get
        folder = True
        icon = "DefaultFolder.png"
        thumbnail = self.utils.getThumbnail(item("thumbnail"))
        listitem = self.xbmcgui.ListItem(item("Title"), iconImage=icon, thumbnailImage=thumbnail)
        if item("action") == "playbyid":
            listitem.setProperty("IsPlayable", "true")

        url = '%s?path=%s&' % (sys.argv[0], item("path"))
        url += 'action=' + item("action") + '&'

        self.xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=folder, totalItems=size)

    # common function for adding video items
    def addVideoListItem(self, params={}, item_params={}, listSize=0):
        item = item_params.get
        icon = item("icon", "default")
        icon = self.utils.getThumbnail(icon)

        listitem = self.xbmcgui.ListItem(item("Title", "Unknown Title"), iconImage=icon, thumbnailImage=item("thumbnail", ""))
        url = '%s?path=%s&action=play_video&videoid=%s' % (sys.argv[0], "/root/video", item("videoid"))
        cm = self.addVideoContextMenuItems(params, item_params)

        listitem.addContextMenuItems(cm, replaceItems=True)
        listitem.setProperty("Video", "true")
        listitem.setProperty("IsPlayable", "true")
        listitem.setInfo(type='Video', infoLabels=item_params)

        self.xbmcplugin.setContent(handle=int(sys.argv[1]), content="movies")
        self.xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=False, totalItems=listSize + 1)

    #==================================== Core Output Parsing Functions ===========================================

    # parses a folder list consisting of a tuple of dictionaries
    def parseFolderList(self, params, results):
        self.common.log("")
        listSize = len(results)
        get = params.get

        cache = True
        if get("store") or get("user_feed"):
            cache = False

        for result_params in results:
            result_params["path"] = get("path")
            self.addFolderListItem(params, result_params, listSize + 1)

        self.xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True, cacheToDisc=cache)

    # parses a video list consisting of a tuple of dictionaries
    def parseVideoList(self, params, results):
        self.common.log("")
        listSize = len(results)
        get = params.get

        for result_params in results:
            result_params["path"] = get("path")
            result = result_params.get

            if result("videoid") == "false":
                continue

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

    def addVideoContextMenuItems(self, params={}, item_params={}):
        cm = []
        get = params.get
        item = item_params.get

        title = self.common.makeAscii(item("Title", "Unknown Title"))
        url_title = urllib.quote_plus(title)
        # studio = self.common.makeAscii(item("Studio", "Unknown Author"))
        # url_studio = urllib.quote_plus(studio)

        cm.append((self.language(30504), "XBMC.Action(Queue)",))

        cm.append((self.language(30501), "XBMC.RunPlugin(%s?path=%s&action=download&videoid=%s)" % (sys.argv[0], item("path"), item("videoid"))))
        cm.append((self.language(30514), "XBMC.Container.Update(%s?path=%s&feed=search&search=%s&scraper=search)" % (sys.argv[0], get("path"), url_title)))
        cm.append((self.language(30523), "XBMC.ActivateWindow(VideoPlaylist)"))
        cm.append((self.language(30502), "XBMC.Action(Info)",))

        return cm

    def addFolderContextMenuItems(self, params={}, item_params={}):
        self.common.log("")
        cm = []
        get = params.get
        item = item_params.get

        if (item("next", "false") == "true"):
            return cm

        if (item("show") and get("store") == "favorites"):
            cm.append((self.language(30506), 'XBMC.RunPlugin(%s?path=%s&action=delete_favorite&show=%s&)' % (sys.argv[0], item("path"), item("show"))))

        if (item("show") and not get("store")):
            cm.append((self.language(30503), 'XBMC.RunPlugin(%s?path=%s&action=add_favorite&show=%s&)' % (sys.argv[0], item("path"), item("show"))))

        if (item("scraper") == "search"):
            cm.append((self.language(30515), 'XBMC.Container.Update(%s?path=%s&action=edit_search&search=%s&)' % (sys.argv[0], item("path"), item("search"))))
            cm.append((self.language(30508), 'XBMC.RunPlugin(%s?path=%s&action=delete_search&delete=%s&)' % (sys.argv[0], item("path"), item("search"))))

        cm.append((self.language(30523), "XBMC.ActivateWindow(VideoPlaylist)"))
        return cm
