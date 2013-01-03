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
import os


class YouTubeUtils:
    def __init__(self):
        self.xbmc = sys.modules["__main__"].xbmc
        self.settings = sys.modules["__main__"].settings
        self.language = sys.modules["__main__"].language
        self.common = sys.modules["__main__"].common
        self.plugin = sys.modules["__main__"].plugin
        self.dbg = sys.modules["__main__"].dbg
        self.PR_VIDEO_QUALITY = self.settings.getSetting("pr_video_quality") == "true"
        self.INVALID_CHARS = "\\/:*?\"<>|"
        self.THUMBNAIL_PATH = os.path.join(self.settings.getAddonInfo('path'), "thumbnails")

    def showMessage(self, heading, message):
        self.common.log(repr(type(heading)) + " - " + repr(type(message)))
        duration = ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10][int(self.settings.getSetting('notification_length'))]) * 1000
        self.xbmc.executebuiltin((u'XBMC.Notification("%s", "%s", %s)' % (heading, message, duration)).encode("utf-8"))

    def getThumbnail(self, title):
        if (not title):
            title = "DefaultFolder"

        thumbnail = os.path.join(sys.modules["__main__"].plugin, title + ".png")

        if (not self.xbmc.skinHasImage(thumbnail)):
            thumbnail = os.path.join(self.THUMBNAIL_PATH, title + ".png")
            if (not os.path.isfile(thumbnail)):
                thumbnail = "DefaultFolder.png"

        return thumbnail

    def showErrorMessage(self, title="", result="", status=500):
        if title == "":
            title = self.language(30600)
        if result == "":
            result = self.language(30617)

        if (status == 303):
            self.showMessage(title, result)
        else:
            self.showMessage(title, self.language(30617))

    def buildItemUrl(self, item_params={}, url=""):
        blacklist = ("path", "thumbnail", "Overlay", "icon", "next", "content", "editid", "summary", "published", "count", "Rating", "Plot", "Title", "new_results_function")
        for key, value in item_params.items():
            if key not in blacklist:
                url += key + "=" + value + "&"
        return url

    def addNextFolder(self, items=[], params={}):
        get = params.get
        item = {"Title": self.language(30509), "thumbnail": "next", "next": "true", "page": str(int(get("page", "0")) + 1)}
        for k, v in params.items():
            if (k != "thumbnail" and k != "Title" and k != "page" and k != "new_results_function"):
                item[k] = v
        items.append(item)

    def extractVID(self, items):
        if isinstance(items, str):
            items = [items]

        self.common.log(repr(items), 4)

        ret_list = []
        for item in items:
            item = item[item.find("v=") + 2:]
            if item.find("&") > -1:
                item = item[:item.find("&")]
            ret_list.append(item)

        self.common.log(repr(ret_list), 4)
        return ret_list

    def convertStringToBinary(self, value):
        if isinstance(value, unicode):
            return ''.join(format(ord(i),'0>8b') for i in value)
        else :
            return value

