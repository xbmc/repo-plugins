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


class YouTubeScraper():
    urls = {}
    urls['disco_main'] = "http://www.youtube.com/disco"
    urls['disco_search'] = "http://www.youtube.com/disco?action_search=1&query=%s"
    urls['main'] = "http://www.youtube.com"
    urls['trailers'] = "http://www.youtube.com/trailers"
    urls['liked_videos'] = "http://www.youtube.com/my_liked_videos"
    urls['music'] = "http://www.youtube.com/music"
    urls['playlist'] = "http://www.youtube.com/view_play_list?p=%s"

    def __init__(self):
        self.settings = sys.modules["__main__"].settings
        self.language = sys.modules["__main__"].language
        self.plugin = sys.modules["__main__"].plugin
        self.dbg = sys.modules["__main__"].dbg

        self.utils = sys.modules["__main__"].utils
        self.core = sys.modules["__main__"].core
        self.common = sys.modules["__main__"].common
        self.cache = sys.modules["__main__"].cache

        self.feeds = sys.modules["__main__"].feeds
        self.storage = sys.modules["__main__"].storage

#=================================== User Scraper ============================================

    def scrapeUserLikedVideos(self, params):
        self.common.log("")

        url = self.createUrl(params)

        result = self.core._fetchPage({"link": url, "login": "true"})

        liked_playlist = self.common.parseDOM(result["content"], "button", {"id": "vm-playlist-play-all"}, ret="href")[0]

        if (liked_playlist.rfind("list=") > 0):
            liked_playlist = liked_playlist[liked_playlist.rfind("list=") + len("list="):]
            if liked_playlist.rfind("&") > 0:
                liked_playlist = liked_playlist[:liked_playlist.rfind("&")]

            return self.feeds.listPlaylist({"user_feed": "playlist", "playlist" : liked_playlist, "fetch_all":"true", "login":"true"})

        return ([], 303)

#================================= trailers ===========================================

    def scraperTop100Trailers(self, params):
        self.common.log("" + repr(params))
        url = self.createUrl(params)

        result = self.core._fetchPage({"link":url})

        trailers_playlist = self.common.parseDOM(result["content"], "a", attrs={"class":"yt-playall-link .*?"}, ret="href")[0]

        if trailers_playlist.find("list=") > 0:
            trailers_playlist = trailers_playlist[trailers_playlist.find("list=") + len("list="):]
            if (trailers_playlist.rfind("&") > 0):
                trailers_playlist = trailers_playlist[:trailers_playlist.rfind("&")]

            return self.feeds.listPlaylist({"user_feed": "playlist", "playlist" : trailers_playlist})

        return ([], 303)

#=================================== Music ============================================

    def searchDisco(self, params={}):
        self.common.log("")

        url = self.createUrl(params)
        result = self.core._fetchPage({"link": url})

        if (result["content"].find("list=") != -1):
            result["content"] = result["content"].replace("\u0026", "&")
            mix_list_id = result["content"][result["content"].find("list=") + 5:]
            if (mix_list_id.find("&") != -1):
                mix_list_id = mix_list_id[:mix_list_id.find("&")]
            elif (mix_list_id.find('"') != -1):
                mix_list_id = mix_list_id[:mix_list_id.find('"')]

            return self.feeds.listPlaylist({"playlist": mix_list_id, "user_feed": "playlist", "fetch_all":"true"})

        return ([], 303)

    def scrapeYouTubeTop100(self, params={}):
        self.common.log("")

        url = self.createUrl(params)

        result = self.core._fetchPage({"link": url})

        if result["status"] == 200:
            list_url = self.common.parseDOM(result["content"], "a", attrs={"id": 'popular-tracks'}, ret="href")[0]
            return self.scrapeWeeklyTop100Playlist(list_url)

        self.common.log("Done")
        return ([], 303)

    def scrapeWeeklyTop100Playlist(self, list_url):
        self.common.log("")
        url = self.urls["main"] + list_url

        result = self.core._fetchPage({"link":url })

        if result["status"] == 200:
            playlist = self.common.parseDOM(result["content"], "ol", attrs={"id": 'watch7-playlist-tray'})
            print repr(playlist)
            videos = self.common.parseDOM(playlist, "li", attrs={"class": 'video-list-item.*?'}, ret="data-video-id")

            return(videos, result["status"])

        return ([], 303)
        #================================== Common ============================================
    def getNewResultsFunction(self, params={}):
        get = params.get

        function = ""
        if (get("scraper") == "search_disco"):
            function = self.searchDisco

        if (get("scraper") in ["liked_videos", "watched_history"]):
            function = self.scrapeUserLikedVideos

        if (get("scraper") == "music_top100"):
            params["batch"] = "true"
            function = self.scrapeYouTubeTop100

        if get("scraper") == "trailers":
            function = self.scraperTop100Trailers

        if function:
            params["new_results_function"] = function

        return True

    def createUrl(self, params={}):
        get = params.get
        page = str(int(get("page", "0")) + 1)
        url = ""

        if (get("scraper") in self.urls):
            url = self.urls[get("scraper")]
            if url.find('%s') > 0:
                url = url % page
            elif url.find('?') > -1:
                url += "&p=" + page
            else:
                url += "?p=" + page

        if get("scraper") == "music_top100":
            url = self.urls["disco_main"]

        if get("scraper") == "trailers":
            url = self.urls["trailers"]

        if (get("scraper") in "search_disco"):
            url = self.urls["disco_search"] % urllib.quote_plus(get("search"))

        return url

    def paginator(self, params={}):
        self.common.log(repr(params))
        get = params.get

        status = 303
        result = []
        next = 'false'
        page = int(get("page", "0"))
        per_page = (10, 15, 20, 25, 30, 40, 50,)[int(self.settings.getSetting("perpage"))]

        if get("page"):
            del params["page"]

        if (get("scraper") == "shows" and get("show")):
            (result, status) = params["new_results_function"](params)
        else:
            (result, status) = self.cache.cacheFunction(params["new_results_function"], params)

        self.common.log("paginator new result count " + str(repr(len(result[0:50]))))

        if len(result) == 0:
            if get("scraper") not in ["music_top100"]:
                return (result, 303)
            result = self.storage.retrieve(params)
            if len(result) > 0:
                status = 200
        elif get("scraper") in ["music_top100"]:
            self.storage.store(params, result)

        if not get("folder"):
            if (per_page * (page + 1) < len(result)):
                next = 'true'

            if (get("fetch_all") != "true"):
                result = result[(per_page * page):(per_page * (page + 1))]

            if len(result) == 0:
                return (result, status)

        if get("batch") == "thumbnails":
            (result, status) = self.core.getBatchDetailsThumbnails(result, params)
        elif get("batch"):
            (result, status) = self.core.getBatchDetails(result, params)

        if get("batch"):
            del params["batch"]
        if page > 0:
            params["page"] = str(page)

        if not get("page") and (get("scraper") == "search_disco"):
            thumbnail = result[0].get("thumbnail")
            self.storage.store(params, thumbnail, "thumbnail")

        if next == "true":
            self.utils.addNextFolder(result, params)

        return (result, status)

    def scrape(self, params={}):
        get = params.get
        if get("scraper") == "trailers":
            return self.scraperTop100Trailers(params)

        self.getNewResultsFunction(params)

        result = self.paginator(params)
        self.common.log(repr(result), 5)
        return result
