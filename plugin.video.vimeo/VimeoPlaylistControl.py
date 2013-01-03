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

class VimeoPlaylistControl():

    def __init__(self):
        self.xbmc = sys.modules["__main__"].xbmc
        self.xbmcgui = sys.modules["__main__"].xbmcgui

        self.settings = sys.modules["__main__"].settings
        self.language = sys.modules["__main__"].language
        self.plugin = sys.modules["__main__"].plugin
        self.dbg = sys.modules["__main__"].dbg

        self.common = sys.modules["__main__"].common
        self.utils = sys.modules["__main__"].utils
        self.core = sys.modules["__main__"].core

        self.feeds = sys.modules["__main__"].feeds
        self.player = sys.modules["__main__"].player

    def playAll(self, params={}):
        get = params.get
        self.common.log("")
        params["fetch_all"] = "true"
        result = []

        # fetch the video entries
        if get("album") and not get("api"):
            result = self.getUserFeed(params)
        elif get("api") in ["my_videos", "my_watch_later", "my_newsubscriptions", "my_likes"]:
            params["login"] = "true"
            result = self.getUserFeed(params)

        if len(result) == 0:
            self.common.log("no results")
            return

        self.common.log(repr(len(result)) + " video results ")

        if get("videoid"):
            video_index = -1
            for index, video in enumerate(result):
                vget = video.get
                if vget("videoid") == get("videoid"):
                    video_index = index
            if video_index > -1:
                result = result[video_index:]

        player = self.xbmc.Player()
        if (player.isPlaying()):
            player.stop()

        playlist = self.xbmc.PlayList(self.xbmc.PLAYLIST_VIDEO)
        playlist.clear()

        video_url = "%s?path=/root&action=play_video&videoid=%s"
        # queue all entries
        for entry in result:
            video = entry.get
            if video("videoid") == "false":
                continue
            listitem = self.xbmcgui.ListItem(label=video("Title"), iconImage=video("thumbnail"), thumbnailImage=video("thumbnail"))
            listitem.setProperty('IsPlayable', 'true')
            listitem.setProperty("Video", "true" )
            listitem.setInfo(type='Video', infoLabels=entry)

            playlist.add(video_url % (sys.argv[0], video("videoid") ), listitem)

        if (get("shuffle")):
            playlist.shuffle()

        self.xbmc.executebuiltin('playlist.playoffset(video , 0)')

    def getUserFeed(self, params={}):
        get = params.get

        return self.feeds.listAll(params)

    def addToAlbum(self, params={}):
        get = params.get

        result = []
        if (not get("album")):
            result = self.feeds.listAll({"api": "my_albums", "login":"true", "folder":"album" })

        selected = -1
        if result:
            list = []
            list.append(self.language(30033))
            for item in result:
                list.append(item["Title"])
            dialog = self.xbmcgui.Dialog()
            selected = dialog.select(self.language(30533), list)

        if selected == 0:
            self.createAlbum(params)
        elif selected > 0:
            params["album"] = result[selected - 1].get("album")

        if get("album"):
            self.core.addToAlbum(params)
            return True

        return False

    def createAlbum(self, params={}):
        get = params.get
        input = self.common.getUserInput(self.language(30033))

        if input and get("videoid"):

            params["title"] = input
            self.core.createAlbum(params)

            return True

        return False

    def removeFromAlbum(self, params={}):
        get = params.get

        if get("album") and get("videoid"):
            (message, status) = self.core.removeFromAlbum(params)

            if (status != 200):
                self.utils.showErrorMessage(self.language(30600), message, status)
                return False

            self.xbmc.executebuiltin("Container.Refresh")
        return True

    def deleteAlbum(self, params):
        get = params.get
        if get("album"):
            (message, status) = self.core.deleteAlbum(params)

            if status != 200:
                self.utils.showErrorMessage(self.language(30600), message, status)
                return False
            self.xbmc.executebuiltin("Container.Refresh")
        return True
