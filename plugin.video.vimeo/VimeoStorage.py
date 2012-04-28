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
import io

class VimeoStorage():
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
                {'Title':self.language(30020), 'external':"true", 'login':"true", 'thumbnail':"favorites", 'api':"my_likes"},
                {'Title':self.language(30021), 'external':"true", 'login':"true", 'thumbnail':"subscriptions", 'api':"my_channels"},
                {'Title':self.language(30019), 'external':"true", 'login':"true", 'thumbnail':"network", 'api':"my_groups"},
                {'Title':self.language(30018), 'external':"true", 'login':"true", 'thumbnail':"playlists", 'api':"my_albums"},
                {'Title':self.language(30022), 'external':"true", 'login':"true", 'thumbnail':"uploads", 'api':"my_videos"},
                       )

    def list(self, params={}):
        get = params.get
        if get("store") == "contact_options":
            return self.getUserOptionFolder(params)
        elif get("store"):
            return self.getStoredSearches(params)

    def openFile(self, filepath, options="w"):
        if options.find("b") == -1:  # Toggle binary mode on failure
            alternate = options + "b"
        else:
            alternate = options.replace("b", "")

        try:
            return io.open(filepath, options)
        except:
            return io.open(filepath, alternate)

    def getStoredSearches(self, params={}):
        get = params.get
        self.common.log("")

        searches = self.retrieveSettings(params)
        
        result = []
        for search in searches:
            item = {}
            item["path"] = get("path")
            item["Title"] = search
            item["search"] = urllib.quote_plus(search)
            item["api"] = "search"
            item["icon"] = "search"

            thumbnail = self.retrieve(params, "thumbnail", item)
            if thumbnail:
                item["thumbnail"] = thumbnail
            else:
                item["thumbnail"] = item["icon"]
            result.append(item)

        return (result, 200)

    def deleteStoredSearch(self, params={}):
        get = params.get
        self.common.log("")

        query = urllib.unquote_plus(get("delete"))
        searches = self.retrieveSettings(params)

        for count, search in enumerate(searches):
            if (search.lower() == query.lower()):
                del(searches[count])
                break

        self.storeSettings(params, searches)

        self.xbmc.executebuiltin("Container.Refresh")

    def saveStoredSearch(self, params={}):
        get = params.get
        self.common.log("")

        if get("search"):
            searches = self.retrieveSettings(params)
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
            self.storeSettings(params, searches)

    def editStoredSearch(self, params={}):
        get = params.get
        self.common.log("")

        if (get("search")):
            old_query = urllib.unquote_plus(get("search"))
            new_query = self.common.getUserInput(self.language(30515), old_query)
            params["search"] = new_query
            params["old_search"] = old_query
            params["store"] = "searches"
            params["api"] = "search"

            self.saveStoredSearch(params)

            params["search"] = urllib.quote_plus(new_query)
            del params["old_search"]

        if get("action"):
            del params["action"]
        if get("store"):
            del params["store"]

    def getUserOptionFolder(self, params={}):
        get = params.get
        self.common.log("")

        result = []
        for item in self.user_options:
            item["path"] = get("path")
            item["contact"] = get("contact")
            result.append(item)

        return (result, 200)

    def reversePlaylistOrder(self, params={}):
        get = params.get
        self.common.log("")

        if (get("playlist")):
            value = "true"
            existing = self.retrieve(params, "value")
            if existing == "true":
                value = "false"  # No result

            self.store(params, value, "value")

            self.xbmc.executebuiltin("Container.Refresh")

    def getReversePlaylistOrder(self, params={}):
        get = params.get
        self.common.log("")

        result = False
        if (get("playlist")):
            existing = self.retrieve(params, "value")
            if existing == "true":
                result = True

        return result

    #=================================== Storage Key ========================================
    def getStorageKey(self, params={}, type="", item={}):

        if type == "value":
            return self._getValueStorageKey(params, item)
        elif type == "viewmode":
            return self._getViewModeStorageKey(params, item)
        elif type == "thumbnail":
            return self._getThumbnailStorageKey(params, item)

        return self._getResultSetStorageKey(params)

    def _getThumbnailStorageKey(self, params={}, item={}):
        get = params.get
        iget = item.get
        key = ""

        if get("search") or iget("search"):
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
        get = params.get
        key = ""

        if get("scraper"):
            key = "s_" + get("scraper")

            if get("category"):
                key += "_category_" + get("category")

        if get("api"):
            key = "result_" + get("api")

            if get("playlist"):
                key += "_" + get("playlist")

            if get("channel"):
                key += "_" + get("channel")

            if get("external") and not get("thumb"):
                key += "_external_" + get("contact")

        if get("api") == "search":
            key = "store_searches"

        if get("store"):
            key = "store_" + get("store")

        return key

    #============================= Storage Functions =================================
    def store(self, params={}, results=[], type="", item={}):
        key = self.getStorageKey(params, type, item)

        self.common.log("Got key " + repr(key))

        if type == "thumbnail" or type == "viewmode" or type == "value":
            self.storeValue(key, results)
        else:
            self.storeResultSet(key, results)

    def storeValue(self, key, value):
        if value:
            self.cache.set(key, value)

    def storeResultSet(self, key, results=[], params={}):
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

    def storeSettings(self, params={}, results=[], type="", item={}):
        key = self.getStorageKey(params, type, item)

        self.common.log("Got key " + repr(key))

        if type == "thumbnail" or type == "viewmode" or type == "value":
            self.storeValueSettings(key, results)
        else:
            self.storeResultSetSettings(key, results)

    def storeValueSettings(self, key, value):
        if value:
            self.settings.setSetting(key, value)

    def storeResultSetSettings(self, key, results=[], params={}):
        get = params.get

        if results:
            if get("prepend"):
                searchCount = (10, 20, 30, 40,)[int(self.settings.getSetting("saved_searches"))]
                existing = self.retrieveResultSet(key)
                existing = [results] + existing[:searchCount]
                self.settings.setSetting(key, repr(existing))
            elif get("append"):
                existing = self.retrieveResultSet(key)
                existing.append(results)
                self.settings.setSetting(key, repr(existing))
            else:
                value = repr(results)
                self.settings.setSetting(key, value)

    #============================= Retrieval Functions =================================
    def retrieve(self, params={}, type="", item={}):
        key = self.getStorageKey(params, type, item)

        self.common.log("Got key " + repr(key))

        if type == "thumbnail" or type == "viewmode" or type == "value":
            return self.retrieveValue(key)
        else:
            return self.retrieveResultSet(key)

    def retrieveValue(self, key):
        value = ""
        if key:
            value = self.cache.get(key)

        return value

    def retrieveResultSet(self, key):
        results = []

        value = self.cache.get(key)
        if value:
            try:
                results = eval(value)
            except:
                results = []

        return results

    def retrieveSettings(self, params={}, type="", item={}):
        key = self.getStorageKey(params, type, item)

        self.common.log("Got key " + repr(key))

        if type == "thumbnail" or type == "viewmode" or type == "value":
            return self.retrieveValueSettings(key)
        else:
            return self.retrieveResultSetSettings(key)

    def retrieveValueSettings(self, key):
        value = ""
        if key:
            value = self.settings.getSetting(key)

        return value

    def retrieveResultSetSettings(self, key):
        results = []

        value = self.settings.getSetting(key)
        if value:
            try:
                results = eval(value)
            except:
                results = []

        return results
