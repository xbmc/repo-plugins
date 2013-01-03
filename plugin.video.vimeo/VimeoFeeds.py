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

class VimeoFeeds():
    urls = {}
    
    def __init__(self):
        self.settings = sys.modules["__main__"].settings
        self.language = sys.modules["__main__"].language
        self.plugin = sys.modules["__main__"].plugin
        self.dbg = sys.modules["__main__"].dbg
        self.utils = sys.modules["__main__"].utils
        self.storage = sys.modules["__main__"].storage
        self.core = sys.modules["__main__"].core
        self.login = sys.modules["__main__"].login
        self.common = sys.modules["__main__"].common
    
    def list(self, params={}):
        self.common.log("")
        get = params.get
        result = []

        if get("store"):
            return self.storage.list(params)
                        
        if get("login") == "true":
            if (not self.login._getAuth()):
                self.common.log("Login required but auth wasn't set!")
                return (self.language(30609), 303)
        
        if (get("api") == "search"):
            if not get("search"):
                query = self.common.getUserInput(self.language(30006), '')
                if not query:
                    return ([], 200)
                params["search"] = query
            self.storage.saveStoredSearch(params)

        (result, status) = self.core.list(params)

        if get("api"):
            params["path"] = get("path") + "/" + get("api")

        if status != 200 or len(result) == 0:
            status = 303
            return (result, status)
        
        if len(result) > 0:
            thumbnail = result[0].get('thumbnail', "")
            self.storage.store(params, thumbnail, "thumbnail")

        self.common.log("Done", 4)
        return (result, 200)

    def listFolder(self, params={}):
        self.common.log("")
        get = params.get
        result = []

        page = int(get("page", "0"))

        if (page != 0):
            result = self.storage.retrieve(params)
        elif not get("page"):
            result = self.listAll(params)

            if len(result) == 0:
                return (result, 303)

            self.storage.store(params, result)

        per_page = (10, 15, 20, 25, 30, 40, 50)[int(self.settings.getSetting("perpage"))]
        next = 'false'
        if (len(result) > 0):
            if (per_page * (page + 1) < len(result)):
                next = 'true'

        result = result[(per_page * page):(per_page * (page + 1))]

        if next == "true":
            self.utils.addNextFolder(result, params)
        
        return (result, 200)

    def listAll(self, params={}):
        self.common.log("")
        get = params.get
        params["fetch_all"] = "true"

        if get("login") == "true":
            if (not self.login._getAuth()):
                self.common.log("Login required but auth wasn't set!")
                return (self.language(30609), 303)

        (vobjects, status) = self.core.list(params)

        if status != 200:
            return []

        next = len(vobjects) > 0

        page = 0
        while next:
            page += 1
            params["page"] = str(page)
            (temp_objects, status) = self.core.list(params)

            if status != 200:
                break

            next = len(temp_objects) > 0

            vobjects += temp_objects
            if get("action") == "play_all" and len(vobjects) >= 250:
                break

        if get("api"):
            if get("api") and get("action") != "play_all":
                vobjects.sort(key=lambda item: item["Title"].lower(), reverse=False)
            else:
                if (self.storage.getReversePlaylistOrder(params)):
                    vobjects.reverse()
        
        return vobjects