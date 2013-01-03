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
import os
import string


class BlipTVUtils:
    def __init__(self):
        self.xbmc = sys.modules["__main__"].xbmc
        self.language = sys.modules["__main__"].language
        self.plugin = sys.modules["__main__"].plugin
        self.dbg = sys.modules["__main__"].dbg
        self.common = sys.modules["__main__"].common

        self.VALID_CHARS = "-_.() %s%s" % (string.ascii_letters, string.digits)
        self.INVALID_CHARS = "\\/:*?\"<>|"
        self.USERAGENT = "Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1"
        self.settings = sys.modules["__main__"].settings
        self.THUMBNAIL_PATH = os.path.join(self.settings.getAddonInfo('path'), "thumbnails")

    # Shows a more user-friendly notification
    def showMessage(self, heading, message):
        duration = ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10][int(self.settings.getSetting('notification_length'))]) * 1000
        self.xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % (heading, message, duration))

    # Resolves the full thumbnail path for the plugins skins directory
    def getThumbnail(self, title):
        if (not title):
            title = "DefaultFolder"

        thumbnail = os.path.join(sys.modules["__main__"].plugin, title + ".png")

        if (not self.xbmc.skinHasImage(thumbnail)):
            thumbnail = os.path.join(self.THUMBNAIL_PATH, title + ".png")
            if (not os.path.isfile(thumbnail)):
                thumbnail = "DefaultFolder.png"

        return thumbnail

    # Standardised error handler
    def showErrorMessage(self, title="", result="", status=500):
        if title == "":
            title = self.language(30600)
        if result == "":
            result = self.language(30617)

        if (status == 303):
            self.showMessage(title, result)
        else:
            self.showMessage(title, self.language(30617))

    # generic function for building the item url filters out many item params to reduce unicode problems
    def buildItemUrl(self, item_params={}, url=""):
        blacklist = ("path", "thumbnail", "Overlay", "icon", "next", "content", "editid", "summary", "published", "count", "Rating", "Plot", "Title", "new_results_function")
        for key, value in item_params.items():
            if key not in blacklist:
                url += key + "=" + value + "&"
        return url

    # Adds a default next folder to a result set
    def addNextFolder(self, items=[], params={}):
        get = params.get
        item = {"Title": self.language(30509), "thumbnail": "next", "next": "true", "page": str(int(get("page", "0")) + 1)}
        for k, v in params.items():
            if (k != "thumbnail" and k != "Title" and k != "page" and k != "new_results_function"):
                item[k] = v
        items.append(item)
