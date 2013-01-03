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


class YouTubePlaylistControl():

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
        self.scraper = sys.modules["__main__"].scraper
        self.player = sys.modules["__main__"].player

    def playAll(self, params={}):
        get = params.get
        self.common.log("")
        params["fetch_all"] = "true"
        result = []

        # fetch the video entries
        if get("scraper") == "search_disco":
            (result, status) = self.scraper.searchDisco(params)
            print repr(result)
        elif get("scraper") == "liked_videos":
            (result, status) = self.getLikedVideos(params)
        elif get("scraper") == "music_top100":
            result = self.getYouTubeTop100(params)
        elif get("playlist"):
            params["user_feed"] = "playlist"
            result = self.getUserFeed(params)
        elif get("user_feed") in ["recommended", "watch_later", "newsubscriptions", "favorites"]:
            params["login"] = "true"
            result = self.getUserFeed(params)
        elif get("video_list"):
            (ytobjects, status) = self.core.getBatchDetails(get("video_list").split(","))
            result = ytobjects

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

    def queueVideo(self, params={}):
        get = params.get
        self.common.log("Queuing videos: " + get("videoid"))

        items = []
        videoids = get("videoid")

        if videoids.find(','):
            items = videoids.split(',')
        else:
            items.append(videoids)

        (videos, status) = self.core.getBatchDetails(items, params)

        if status != 200:
            self.common.log("construct video url failed contents of video item " + repr(videos))

            self.utils.showErrorMessage(self.language(30603), "apierror", status)
            return False

        playlist = self.xbmc.PlayList(self.xbmc.PLAYLIST_VIDEO)

        video_url = "%s?path=/root&action=play_video&videoid=%s"
        # queue all entries
        for entry in videos:
            video = entry.get
            if video("videoid") == "false":
                continue
            listitem = self.xbmcgui.ListItem(label=video("Title"), iconImage=video("thumbnail"), thumbnailImage=video("thumbnail"))
            listitem.setProperty('IsPlayable', 'true')
            listitem.setProperty("Video", "true" )
            listitem.setInfo(type='Video', infoLabels=entry)

            playlist.add(video_url % (sys.argv[0], video("videoid") ), listitem)

    def getUserFeed(self, params={}):
        get = params.get

        if get("user_feed") == "playlist":
            if not get("playlist"):
                return False
        elif get("user_feed") in ["newsubscriptions", "favorites"]:
            if not get("contact"):
                return False

        return self.feeds.listAll(params)

    def getYouTubeTop100(self, params={}):
        (result, status) = self.scraper.scrapeYouTubeTop100(params)

        if status == 200:
            (result, status) = self.core.getBatchDetails(result, params)

        return result

    def getLikedVideos(self, params={}):
        get = params.get
        if not get("scraper") or not get("login"):
            return False

        return self.scraper.scrapeUserLikedVideos(params)

    def addToPlaylist(self, params={}):
        get = params.get

        result = []
        if (not get("playlist")):
            params["user_feed"] = "playlists"
            params["login"] = "true"
            params["folder"] = "true"
            result = self.feeds.listAll(params)

        selected = -1
        if result:
            list = []
            list.append(self.language(30529))
            for item in result:
                list.append(item["Title"])
            dialog = self.xbmcgui.Dialog()
            selected = dialog.select(self.language(30528), list)

        if selected == 0:
            self.createPlaylist(params)
            if get("title"):
                result = self.feeds.listAll(params)
                for item in result:
                    if get("title") == item["Title"]:
                        params["playlist"] = item["playlist"]
                        break
        elif selected > 0:
            params["playlist"] = result[selected - 1].get("playlist")

        if get("playlist"):
            self.core.add_to_playlist(params)
            return True

        return False

    def createPlaylist(self, params={}):
        input = self.common.getUserInput(self.language(30529))
        if input:
            params["title"] = input
            self.core.add_playlist(params)
            return True
        return False

    def removeFromPlaylist(self, params={}):
        get = params.get

        if get("playlist") and get("playlist_entry_id"):
            (message, status) = self.core.remove_from_playlist(params)

            if (status != 200):
                self.utils.showErrorMessage(self.language(30600), message, status)
                return False

            self.xbmc.executebuiltin("Container.Refresh")
        return True

    def deletePlaylist(self, params):
        get = params.get
        if get("playlist"):
            (message, status) = self.core.del_playlist(params)
            print "called " + repr(status)
            if status != 200:
                self.utils.showErrorMessage(self.language(30600), message, status)
                return False
            self.xbmc.executebuiltin("Container.Refresh")
        return True
