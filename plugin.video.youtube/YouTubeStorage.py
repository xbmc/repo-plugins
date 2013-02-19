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
import io


class YouTubeStorage():
    def __init__(self):
        self.xbmc = sys.modules["__main__"].xbmc
        self.settings = sys.modules["__main__"].settings
        self.language = sys.modules["__main__"].language
        self.plugin = sys.modules["__main__"].plugin
        self.dbg = sys.modules["__main__"].dbg

        self.utils = sys.modules["__main__"].utils
        self.common = sys.modules["__main__"].common
        self.cache = sys.modules["__main__"].cache

        # This list contains the list options a user sees when indexing a contact
        #                label                      , external         , login         ,    thumbnail                    , feed
        self.user_options = (
                    {'Title':self.language(30020), 'external':"true", 'login':"true", 'thumbnail':"favorites",     'user_feed':"favorites"},
                    {'Title':self.language(30023), 'external':"true", 'login':"true", 'thumbnail':"playlists",     'user_feed':"playlists", 'folder':"true"},
                    {'Title':self.language(30021), 'external':"true", 'login':"true", 'thumbnail':"subscriptions", 'user_feed':"subscriptions", 'folder':"true"},
                    {'Title':self.language(30022), 'external':"true", 'login':"true", 'thumbnail':"uploads",         'user_feed':"uploads"},
                       )

    def list(self, params={}):
        self.common.log(repr(params), 5)
        get = params.get
        if get("store") == "contact_options":
            return self.getUserOptionFolder(params)
        elif get("store") == "artists":
            return self.getStoredArtists(params)
        elif get("store"):
            return self.getStoredSearches(params)
        self.common.log("Done", 5)

    def openFile(self, filepath, options="w"):
        self.common.log(repr(filepath), 5)
        if options.find("b") == -1:  # Toggle binary mode on failure
            alternate = options + "b"
        else:
            alternate = options.replace("b", "")

        try:
            return io.open(filepath, options)
        except:
            return io.open(filepath, alternate)

    def getStoredSearches(self, params={}):
        self.common.log(repr(params), 5)
        get = params.get

        searches = self.retrieveSettings(params)

        result = []
        for search in searches:
            item = {}
            item["path"] = get("path")
            item["Title"] = search
            item["search"] = urllib.quote_plus(search)

            if (get("store") == "searches"):
                item["feed"] = "search"
                item["icon"] = "search"
            elif get("store") == "disco_searches":
                item["scraper"] = "search_disco"
                item["icon"] = "discoball"

            thumbnail = self.retrieveSettings(params, "thumbnail", item)
            if thumbnail:
                item["thumbnail"] = thumbnail
            else:
                item["thumbnail"] = item["icon"]
            result.append(item)

        self.common.log("Done: " + repr(result), 5)
        return (result, 200)

    def deleteStoredSearch(self, params={}):
        self.common.log(repr(params), 5)
        get = params.get

        query = urllib.unquote_plus(get("delete"))
        searches = self.retrieveSettings(params)

        for count, search in enumerate(searches):
            if (search.lower() == query.lower()):
                del(searches[count])
                break

        self.storeSettings(params, searches)

        self.xbmc.executebuiltin("Container.Refresh")

    def saveStoredSearch(self, params={}):
        self.common.log(repr(params), 5)
        get = params.get

        if get("search"):
            searches = self.retrieveSettings(params)
            self.common.log("1: " + repr(searches), 5)

            new_query = urllib.unquote_plus(get("search"))
            old_query = new_query

            if get("old_search"):
                old_query = urllib.unquote_plus(get("old_search"))

            for count, search in enumerate(searches):
                if (search.lower() == old_query.lower()):
                    del(searches[count])
                    break

            searchCount = (10, 20, 30, 40,)[int(self.settings.getSetting("saved_searches"))] - 1
            searches = [new_query] + searches[:searchCount]
            self.common.log("2: " + repr(searches), 5)
            self.storeSettings(params, searches)
        self.common.log("Done", 5)

    def editStoredSearch(self, params={}):
        self.common.log(repr(params), 5)
        get = params.get

        if (get("search")):
            old_query = urllib.unquote_plus(get("search"))
            new_query = self.common.getUserInput(self.language(30515), old_query)
            params["search"] = new_query
            params["old_search"] = old_query

            if get("action") == "edit_disco":
                params["scraper"] = "search_disco"
                params["store"] = "disco_searches"
            else:
                params["store"] = "searches"
                params["feed"] = "search"

            self.saveStoredSearch(params)

            params["search"] = urllib.quote_plus(new_query)
            del params["old_search"]

        if get("action"):
            del params["action"]
        if get("store"):
            del params["store"]

    def getUserOptionFolder(self, params={}):
        self.common.log(repr(params), 5)
        get = params.get

        result = []
        for item in self.user_options:
            item["path"] = get("path")
            item["contact"] = get("contact")
            result.append(item)

        return (result, 200)

    def changeSubscriptionView(self, params={}):
        self.common.log(repr(params), 5)
        get = params.get

        if (get("view_mode")):
            key = self.getStorageKey(params, "viewmode")

            self.storeValue(key, get("view_mode"))

            params['user_feed'] = get("view_mode")
            if get("viewmode") == "playlists":
                params["folder"] = "true"  # No result

    def reversePlaylistOrder(self, params={}):
        self.common.log(repr(params), 5)
        get = params.get

        if (get("playlist")):
            value = "true"
            existing = self.retrieve(params, "value")
            if existing == "true":
                value = "false"  # No result

            self.store(params, value, "value")

            self.xbmc.executebuiltin("Container.Refresh")

    def getReversePlaylistOrder(self, params={}):
        self.common.log(repr(params), 5)
        get = params.get

        result = False
        if (get("playlist")):
            existing = self.retrieve(params, "value")
            if existing == "true":
                result = True

        return result

    #=================================== Storage Key ========================================
    def getStorageKey(self, params={}, type="", item={}):
        self.common.log(repr(params), 5)
        if type == "value":
            return self._getValueStorageKey(params, item)
        elif type == "viewmode":
            return self._getViewModeStorageKey(params, item)
        elif type == "thumbnail":
            return self._getThumbnailStorageKey(params, item)
        return self._getResultSetStorageKey(params)

    def _getThumbnailStorageKey(self, params={}, item={}):
        self.common.log(repr(params), 5)
        get = params.get
        iget = item.get
        key = ""

        if get("search") or iget("search"):
            key = "disco_search_"
            if get("feed") or iget("feed"):
                key = "search_"

            if get("store") == "searches":
                key = "search_"

            if get("search"):
                key += urllib.unquote_plus(get("search", ""))

            if iget("search"):
                key += urllib.unquote_plus(iget("search", ""))

        if get("user_feed"):
            key = get("user_feed")

            if get("channel"):
                key = "subscriptions_" + get("channel")

            if iget("channel"):
                key = "subscriptions_" + iget("channel")

            if get("playlist"):
                key = "playlist_" + get("playlist")

            if iget("playlist"):
                key = "playlist_" + iget("playlist")

        if key:
            key += "_thumb"

        return key

    def _getValueStorageKey(self, params={}, item={}):
        self.common.log(repr(params), 5)
        get = params.get
        iget = item.get
        key = ""

        if ((get("action") == "reverse_order" or get("user_feed") == "playlist") and (iget("playlist") or get("playlist"))):

            key = "reverse_playlist_"
            if iget("playlist"):
                key += iget("playlist")

            if get("playlist"):
                key += get("playlist")

            if (get("external")):
                key += "_external_" + get("contact")
        return key 

    def _getViewModeStorageKey(self, params={}, item={}):
        self.common.log(repr(params), 5)
        get = params.get
        iget = item.get
        key = ""

        if (get("external")):
            key = "external_" + get("contact") + "_"
        elif (iget("external")):
            key = "external_" + iget("contact") + "_"

        if get("channel"):
            key += "view_mode_" + get("channel")
        elif (iget("channel")):
            key += "view_mode_" + iget("channel")

        return key

    def _getResultSetStorageKey(self, params={}):
        self.common.log(repr(params), 5)
        get = params.get

        key = ""

        if get("scraper"):
            key = "s_" + get("scraper")

            if get("scraper") == "disco_search":
                key = "store_disco_searches"

            if get("category"):
                key += "_category_" + get("category")

        if get("user_feed"):
            key = "result_" + get("user_feed")

            if get("playlist"):
                key += "_" + get("playlist")

            if get("channel"):
                key += "_" + get("channel")

            if get("external") and not get("thumb"):
                key += "_external_" + get("contact")

        if get("feed") == "search":
            key = "store_searches"

        if get("store"):
            key = "store_" + get("store")

        return key

    #============================= Storage Functions =================================
    def store(self, params={}, results=[], type="", item={}):
        self.common.log(repr(params), 5)
        key = self.getStorageKey(params, type, item)

        self.common.log("Got key " + repr(key))

        self.common.log(repr(type), 5)
        if type == "thumbnail" or type == "viewmode" or type == "value":
            self.storeValue(key, results)
        else:
            self.storeResultSet(key, results)
        self.common.log("done", 5)

    def storeValue(self, key, value):
        self.common.log(repr(key) + " - " + repr(value), 5)
        if value:
            self.cache.set(key, value)
        self.common.log("done", 5)

    def storeResultSet(self, key, results=[], params={}):
        self.common.log(repr(params), 5)
        get = params.get

        if results:
            if get("prepend"):
                searchCount = (10, 20, 30, 40,)[int(self.settings.getSetting("saved_searches"))]
                existing = self.retrieveResultSet(key)
                existing = [results] + existing[:searchCount]
                self.cache.set(key, repr(existing))
            elif get("append"):
                existing = self.retrieveResultSet(key)
                existing.append(results)
                self.cache.set(key, repr(existing))
            else:
                value = repr(results)
                self.cache.set(key, value)
        self.common.log("done", 5)

    def storeSettings(self, params={}, results=[], type="", item={}):
        self.common.log(repr(params), 5)

        key = self.getStorageKey(params, type, item)

        self.storeResultSetSettings(key, results)

        self.common.log("done", 5)

    def storeResultSetSettings(self, key, results=[], params={}):
        self.common.log(repr(params), 5)

        if results:
            value = repr(results)
            self.settings.setSetting(key, value)

        self.common.log("done", 5)

    #============================= Retrieval Functions =================================
    def retrieve(self, params={}, type="", item={}):
        self.common.log(repr(params), 5)
        key = self.getStorageKey(params, type, item)

        if type == "thumbnail" or type == "viewmode" or type == "value":
            return self.retrieveValue(key)
        else:
            return self.retrieveResultSet(key)

    def retrieveValue(self, key):
        self.common.log(repr(key), 5)
        value = ""
        if key:
            value = self.cache.get(key)

        return value

    def retrieveResultSet(self, key):
        self.common.log(repr(key), 5)
        results = []

        value = self.cache.get(key)
        self.common.log(repr(value), 5)
        if value:
            try:
                results = eval(value)
            except:
                results = []

        return results

    def retrieveSettings(self, params={}, type="", item={}):
        self.common.log(repr(params), 5)
        key = self.getStorageKey(params, type, item)

        self.common.log("Got key " + repr(key))

        return self.retrieveResultSetSettings(key)

    def retrieveResultSetSettings(self, key):
        self.common.log(repr(key), 5)
        results = []

        value = self.settings.getSetting(key)
        self.common.log(repr(value), 5)
        if value:
            try:
                results = eval(value)
            except:
                results = []

        return results

    def updateVideoIdStatusInCache(self, pre_id, ytobjects):
        self.common.log(pre_id)
        save_data = {}
        for item in ytobjects:
            if "videoid" in item:
                save_data[item["videoid"]] = repr(item)

        self.cache.setMulti(pre_id, save_data)

    def getVideoIdStatusFromCache(self, pre_id, ytobjects):
        self.common.log(pre_id)
        load_data = []
        for item in ytobjects:
            if "videoid" in item:
                load_data.append(item["videoid"])

        res = self.cache.getMulti(pre_id, load_data)
        if len(res) != len(load_data):
            self.common.log("Length mismatch:" + repr(res) + " - " + repr(load_data))

        i = 0
        for item in ytobjects:
            if "videoid" in item:
                if i < len(res):
                    item["Overlay"] = res[i]
                i += 1 # This can NOT be enumerated because there might be missing videoids
        return ytobjects
