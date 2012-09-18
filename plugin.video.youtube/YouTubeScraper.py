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
    urls['current_trailers'] = "http://www.youtube.com/trailers?s=trit&p=%s&hl=en"
    urls['disco_main'] = "http://www.youtube.com/disco"
    urls['disco_mix_list'] = "http://www.youtube.com/watch?v=%s&feature=disco&playnext=1&list=%s"
    urls['disco_search'] = "http://www.youtube.com/disco?action_search=1&query=%s"
    urls['game_trailers'] = "http://www.youtube.com/trailers?s=gtcs"
    urls['main'] = "http://www.youtube.com"
    urls['movies'] = "http://www.youtube.com/ytmovies"
    urls['popular_game_trailers'] = "http://www.youtube.com/trailers?s=gtp&p=%s&hl=en"
    urls['popular_trailers'] = "http://www.youtube.com/trailers?s=trp&p=%s&hl=en"
    urls['show_single_list'] = "http://www.youtube.com/channel_ajax?action_more_single_playlist_videos=1&page=%s&list_id=%s"
    urls['show_list'] = "http://www.youtube.com/show"
    urls['shows'] = "http://www.youtube.com/shows"
    urls['trailers'] = "http://www.youtube.com/trailers?s=tr"
    urls['latest_trailers'] = "http://www.youtube.com/trailers?s=tr"
    urls['latest_game_trailers'] = "http://www.youtube.com/trailers?s=gtcs"
    urls['upcoming_game_trailers'] = "http://www.youtube.com/trailers?s=gtcs&p=%s&hl=en"
    urls['upcoming_trailers'] = "http://www.youtube.com/trailers?s=tros&p=%s&hl=en"
    urls['watched_history'] = "http://www.youtube.com/my_history"
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

#=================================== Trailers ============================================
    def scrapeTrailersListFormat(self, params={}):
        self.common.log("")
        url = self.createUrl(params)
        result = self.core._fetchPage({"link": url})

        trailers = self.common.parseDOM(result["content"], "div", attrs={"id": "recent-trailers-container"})

        items = []
        if (len(trailers) > 0):
            ahref = self.common.parseDOM(trailers, "a", attrs={"class": " yt-uix-hovercard-target", "id": ".*?"}, ret="href")

            thumbs = self.common.parseDOM(trailers, "span", attrs={"class": "video-thumb .*?"})

            athumbs = self.common.parseDOM(thumbs, "img", ret="data-thumb")

            videos = self.utils.extractVID(ahref)

            for index, videoid in enumerate(videos):
                items.append((videoid, athumbs[index]))

        self.common.log("Done")
        return (items, result["status"])

    def scrapeTrailersGridFormat(self, params={}):
        self.common.log("")
        items = []
        next = True
        page = 0

        while next:
            params["page"] = str(page)
            url = self.createUrl(params)
            result = self.core._fetchPage({"link": url})

            page += 1

            next = False
            if result["status"] == 200:
                pagination = self.common.parseDOM(result["content"], "div", {"class": "yt-uix-pager"})
                if (len(pagination) > 0):
                    tmp = str(pagination)
                    if (tmp.find("Next") > 0):
                        next = True

                trailers = self.common.parseDOM(result["content"], "div", attrs={"id": "popular-column"})

                if len(trailers) > 0:
                    ahref = self.common.parseDOM(trailers, "a", attrs={"class": 'ux-thumb-wrap.*?'}, ret="href")

                    thumbs = self.common.parseDOM(trailers, "span", attrs={"class": "video-thumb .*?"})

                    athumbs = self.common.parseDOM(thumbs, "img", ret="data-thumb")

                    videos = self.utils.extractVID(ahref)

                    for index, videoid in enumerate(videos):
                        items.append((videoid, athumbs[index]))

        del params["page"]
        self.common.log("Done")
        return (items, result["status"])

#=================================== User Scraper ============================================

    def scrapeUserVideoFeed(self, params):
        self.common.log("")

        url = self.createUrl(params)

        result = self.core._fetchPage({"link": url, "login": "true"})
        liked = self.common.parseDOM(result["content"], "div", {"id": "vm-video-list-container"})
        print "liked videos " + repr(liked)
        items = []

        if (len(liked) > 0):
            vidlist = self.common.parseDOM(liked, "li", {"class": "vm-video-item "}, ret="id")
            for videoid in vidlist:
                videoid = videoid[videoid.rfind("video-") + 6:]
                items.append(videoid)

        self.common.log("Done")
        if len(liked) > 0:
            return (items, result["status"])
        else:
            return ([], 303)  # Something else

#=================================== Shows ============================================

    def extractListId(self, result):
        list = self.common.parseDOM(result["content"], "a", attrs={"class": "play-all.*?"}, ret="href")[0]
        if list.find("list=") > 0:
            list = list[list.find("list=") + len("list="):]
            list = list[:list.find("&")]
        return list

    def scrapeShowEpisodes(self, params={}):
        get = params.get
        self.common.log(repr(params))

        if not get("season"):
            url = self.createUrl(params)
            result = self.core._fetchPage({"link": url})
            listId = self.extractListId(result)
        else:
            listId = get("season")

        nexturl = self.urls["show_single_list"]

        videos = []
        fetch = True
        start = 1
        while fetch:
            fetch = False
            url = nexturl % (start, listId)
            result = self.core._fetchPage({"link": url})

            if result["status"] == 200:
                result["content"] = result["content"].replace("\\u0026", "&")
                result["content"] = result["content"].replace("\\/", "/")
                result["content"] = result["content"].replace('\\"', '"')
                result["content"] = result["content"].replace("\\u003c", "<")
                result["content"] = result["content"].replace("\\u003e", ">")
                more_videos = self.common.parseDOM(result["content"], "button", ret="data-video-ids")

                if more_videos:
                    fetch = True
                    videos += more_videos
                    start += 1

        self.common.log("Done")
        return (videos, result["status"])

        # If the show contains more than one season the function will return a list of folder items,
        # otherwise a paginated list of video items is returned

    def scrapeShow(self, params={}):
        get = params.get
        self.common.log("")

        url = self.createUrl(params)
        result = self.core._fetchPage({"link": url})

        if ((result["content"].find('single-playlist channel-module') > 0) or get("season")):
            self.common.log("scrapeShow parsing videolist for single season")
            return self.cache.cacheFunction(self.scrapeShowEpisodes, params)

        params["folder"] = "true"
        del params["batch"]
        self.common.log("Done")
        return self.cache.cacheFunction(self.scrapeShowSeasons, result["content"], params)

    def extractMultipleListIds(self, seasons):
        season_list = self.common.parseDOM(seasons, "a", attrs={"class": "yt-uix-tile-link"}, ret="href")
        for i, season in enumerate(season_list):
            if season.find("list=") > 0:
                season = season[season.find("list=") + len("list="):]
                season = season[:season.find("&")]
            season_list[i] = season
        return season_list

    def scrapeShowSeasons(self, html, params={}):
        get = params.get
        params["folder"] = "true"
        self.common.log("scrapeShowSeasons : " + repr(params))

        yobjects = []

        seasons = self.common.parseDOM(html, "div", attrs={"class": "playlists-wide channel-module.*?"})
        if (len(seasons) > 0):
            params["folder"] = "true"

            season_list = self.extractMultipleListIds(seasons)
            atitle = self.common.parseDOM(seasons, "a", attrs={"class": "yt-uix-tile-link"})

            self.common.log(repr(season_list))

            if len(season_list) == len(atitle) and len(atitle) > 0:
                for i in range(0, len(atitle)):
                    item = {}

                    item["Title"] = atitle[i]
                    item["season"] = season_list[i]
                    item["thumbnail"] = "shows"
                    item["scraper"] = "shows"
                    item["icon"] = "shows"
                    item["show"] = get("show")
                    yobjects.append(item)

        if (len(yobjects) > 0):
            self.common.log("Done")
            return (yobjects, 200)

        self.common.log("Failed")
        return ([], 303)

    def scrapeShowsGrid(self, params={}):
        self.common.log("")

        next = "true"
        items = []
        page = 0

        while next == "true":
            next = "false"
            params["page"] = str(page)

            url = self.createUrl(params)
            result = self.core._fetchPage({"link": url})

            showcont = self.common.parseDOM(result["content"], "ul", {"class": "browse-item-list"})
            showcont = "".join(showcont)
            shows = self.common.parseDOM(showcont, "div", {"class": "browse-item show-item.*?"})

            if (len(shows) > 0):
                page += 1
                next = "true"

                for show in shows:
                    ahref = self.common.parseDOM(show, "a", attrs={"title": ".*?"}, ret="href")
                    acont = self.common.parseDOM(show, "a", ret="title")
                    athumb = self.common.parseDOM(show, "img", attrs={"alt": ""}, ret="src")
                    acount = self.common.parseDOM(show, "span", {"class": "browse-item-info"})

                    item = {}

                    count = self.common.stripTags(acount[0].replace("\n", "").replace(",", ", "))
                    title = acont[0] + " (" + count + ")"
                    title = self.common.replaceHTMLCodes(title)
                    item['Title'] = title

                    show_url = ahref[0]
                    if (show_url.find("?p=") > 0):
                        show_url = show_url[show_url.find("?p=") + 1:]
                    else:
                        show_url = show_url.replace("/show/", "")
                    show_url = urllib.quote_plus(show_url)
                    item['show'] = show_url

                    item['icon'] = "shows"
                    item['scraper'] = "shows"

                    thumbnail = athumb[0]
                    if (thumbnail.find("_thumb.") > 0):
                        thumbnail = thumbnail.replace("_thumb.", ".")

                    item["thumbnail"] = thumbnail

                    print "adding item: " + repr(item) + " show " + repr(show)

                    items.append(item)

        del params["page"]

        self.common.log("Done" + repr(items), 3)

        return (items, result["status"])

#=================================== Music ============================================

    def searchDisco(self, params={}):
        self.common.log("")

        items = []

        url = self.createUrl(params)
        result = self.core._fetchPage({"link": url})

        if (result["content"].find("list=") != -1):
            result["content"] = result["content"].replace("\u0026", "&")
            mix_list_id = result["content"][result["content"].find("list=") + 5:]
            if (mix_list_id.find("&") != -1):
                mix_list_id = mix_list_id[:mix_list_id.find("&")]
            elif (mix_list_id.find('"') != -1):
                mix_list_id = mix_list_id[:mix_list_id.find('"')]
            params["mix_list_id"] = mix_list_id

            video_id = result["content"][result["content"].find("v=") + 2:]
            params["disco_videoid"] = video_id[:video_id.find("&")]

            url = self.createUrl(params)
            result = self.core._fetchPage({"link": url})

            mix_list = self.common.parseDOM(result["content"], "div", {"id": "playlist-bar"}, ret="data-video-ids")

            if (len(mix_list) > 0):
                items = mix_list[0].split(",")

        self.common.log("Done")
        return (items, result["status"])

    def scrapeYouTubeTop100(self, params={}):
        self.common.log("")

        url = self.createUrl(params)
        result = self.core._fetchPage({"link": url})

        items = []
        if result["status"] == 200:
            videos = self.common.parseDOM(result["content"], "div", attrs={"id": 'weekly-hits'})
            items = self.common.parseDOM(videos, "button", attrs={"type": "button", "class": "addto-button.*?"}, ret="data-video-ids")
        self.common.log("Done")
        return (items, result["status"])

#=================================== Movies ============================================

    def scrapeMovieSubCategory(self, params={}):
        self.common.log("scrapeMovieSubCategory : " + repr(params))

        url = self.createUrl(params)
        result = self.core._fetchPage({"link": url})

        ytobjects = []

        dom_pages = self.common.parseDOM(result["content"], "div", {"class": "yt-uix-slider-title"})
        for item in dom_pages:
            ahref = self.common.parseDOM(item, "a", ret="href")
            acont = self.common.parseDOM(item, "a")
            if len(ahref) == len(acont) and len(ahref) > 0:
                item = {}
                cat = ahref[0]
                title = acont[0].replace("&raquo;", "").strip()
                item['Title'] = self.common.replaceHTMLCodes(title)
                cat = urllib.quote_plus(cat)
                item['category'] = cat
                item['scraper'] = "movies"
                item["thumbnail"] = "movies"
                ytobjects.append(item)

        self.common.log("Done")
        return (ytobjects, result["status"])

    def scrapeMoviesGrid(self, params={}):
        self.common.log("")

        next = "true"
        items = []
        page = 0

        while next == "true":
            next = "false"
            params["page"] = str(page)

            url = self.createUrl(params)
            result = self.core._fetchPage({"link": url})

            pagination = self.common.parseDOM(result["content"], "div", attrs={"class": "yt-uix-pager"})

            if (len(pagination) > 0):
                tmp = str(pagination)
                if (tmp.find("Next") > 0):
                    next = "true"

            videos = self.common.parseDOM(result["content"],"div", {"id":"browse-main-column"})
            videoids = self.common.parseDOM(videos, "button", {"class": "addto-button.*?"}, ret="data-video-ids")
            thumbs = self.common.parseDOM(videos, "img", attrs={"data-thumb": ".*?"}, ret="data-thumb")

            page += 1
            self.common.log("Found " + str(len(videoids)) + " videoids: " + repr(videoids))
            self.common.log("Found " + str(len(thumbs)) + " thumbs: " + repr(thumbs))

            self.common.log("Items before: " + repr(items))
            if len(videoids) == len(thumbs) and len(videoids) > 0:
                for i in range(0, len(videoids)):
                    items.append((videoids[i], thumbs[i]))
            self.common.log("Items now: " + repr(items))

        del params["page"]
        self.common.log("Done : " + str(len(items)))
        return (items, result["status"])

#================================== Common ============================================
    def getNewResultsFunction(self, params={}):
        get = params.get

        function = ""
        if (get("scraper") == "search_disco"):
            function = self.searchDisco
            params["batch"] = "true"
        if (get("scraper") in ["liked_videos", "watched_history"]):
            function = self.scrapeUserVideoFeed
            params["batch"] = "true"
        if (get("scraper") == "music_top100"):
            function = self.scrapeYouTubeTop100
            params["batch"] = "true"

        if (get("scraper") in ["movies", "shows"] and not get("category")):
            function = self.scrapeCategoryList
            params["folder"] = "true"

        if get("scraper") == "shows" and get("category"):
            params["folder"] = "true"
            function = self.scrapeShowsGrid

        if get("scraper") == "shows" and get("show"):
            del params["folder"]
            params["batch"] = "true"
            function = self.scrapeShow

        if get("scraper") == "movies" and get("category"):
            if get("subcategory"):
                params["folder"] = "true"
                function = self.scrapeMovieSubCategory
            else:
                params["batch"] = "thumbnails"
                function = self.scrapeMoviesGrid

        if (get("scraper") in ['current_trailers', 'game_trailers', 'popular_game_trailers', 'popular_trailers', 'trailers', 'upcoming_game_trailers', 'upcoming_trailers']):
            params["batch"] = "thumbnails"
            function = self.scrapeTrailersGridFormat
        if (get("scraper") in ["latest_game_trailers", "latest_trailers"]):
            params["batch"] = "thumbnails"
            function = self.scrapeTrailersListFormat

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

        if (get("scraper") == "shows"):
            url = self.urls["shows"] + "?hl=en"

            if (get("category")):
                category = get("category")
                category = urllib.unquote_plus(category)
                category = category.replace("/shows/", "")
                category = category.replace("/shows", "")
                url = self.urls["shows"] + "/" + category
                if category.find("?") > -1:
                    url += "&p=" + page + "&hl=en"
                else:
                    url += "?p=" + page + "&hl=en"

            if (get("show")):
                show = urllib.unquote_plus(get("show"))
                if (show.find("p=") < 0):
                    url = self.urls["show_list"] + "/" + show + "?hl=en"
                else:
                    url = self.urls["show_list"] + "?" + show + "&hl=en"
                if (get("season")):
                    url = url + "&s=" + get("season")

        if (get("scraper") == "movies"):
            if (get("category")):
                category = get("category")
                category = urllib.unquote_plus(category)
                category = category.replace("/movies/", "")  # indian
                category = category.replace("/movies", "")  # Foreign
                if get("subcategory"):
                    url = self.urls["main"] + "/movies/" + category + "?hl=en"
                else:
                    if category.find("?") > -1:
                        url = self.urls["main"] + "/movies/" + category + "&p=" + page + "&hl=en"
                    else:
                        url = self.urls["main"] + "/movies/" + category + "?p=" + page + "&hl=en"

            else:
                url = self.urls["movies"] + "?hl=en"

        if get("scraper") == "music_top100":
            url = self.urls["music"]

        if (get("scraper") in "search_disco"):
            url = self.urls["disco_search"] % urllib.quote_plus(get("search"))
            if get("mix_list_id") and get("disco_videoid"):
                url = self.urls["disco_mix_list"] % (get("disco_videoid"), get("mix_list_id"))

        return url

    def scrapeCategoryList(self, params={}):
        get = params.get
        self.common.log("")

        scraper = "movies"
        thumbnail = "explore"
        yobjects = []

        if (get("scraper") and get("scraper") != "movies"):
            scraper = get("scraper")
            thumbnail = get("scraper")

        url = self.createUrl(params)
        result = self.core._fetchPage({"link": url})

        if result["status"] == 200:
            categories = self.common.parseDOM(result["content"], "div", attrs={"class": "yt-uix-expander-body.*?"})
            if len(categories) == 0:
                categories = self.common.parseDOM(result["content"], "div", attrs={"id": "browse-filter-menu"})

            if len(categories) == 0:  # <- is this needed. Anyways. it breaks. fix that..
                categories = self.common.parseDOM(result["content"], "div", attrs={"class": "browse-filter-menu.*?"})

            for cat in categories:
                self.common.log("scrapeCategoryList : " + cat[0:50])
                ahref = self.common.parseDOM(cat, "a", ret="href")
                acontent = self.common.parseDOM(cat, "a")
                for i in range(0, len(ahref)):
                    item = {}
                    title = acontent[i]
                    title = self.common.replaceHTMLCodes(title)

                    if title == "All Categories" or title == "Education" or title == "":
                        continue
                    item['Title'] = title

                    cat = ahref[i].replace("/" + scraper + "/", "")

                    if get("scraper") == "movies":
                        if cat.find("pt=nr") > 0:
                            continue
                        elif cat.find("indian-cinema") > -1 or cat.find("foreign-film") > -1:
                            item["subcategory"] = "true"

                    cat = urllib.quote_plus(cat)
                    item['category'] = cat
                    item['scraper'] = scraper
                    item["thumbnail"] = thumbnail
                    yobjects.append(item)

            if (not yobjects):
                self.common.log("Failed")
                return (self.language(30601), 303)

        self.common.log("Done")
        return (yobjects, result["status"])

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

        self.common.log("paginator new result " + str(repr(len(result[0:50]))))

        if len(result) == 0:
            if get("scraper") not in ["music_top100"]:
                return (result, 303)
            result = self.storage.retrieve(params)
            if len(result) > 0:
                status = 200
        elif get("scraper") in ["music_top100"]:
            self.storage.store(params, result)

        if not get("folder") or (get("scraper") == "shows" and get("category")):
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

        if not get("page") and (get("scraper") == "search_disco" or get("scraper") == "music_artist"):
            thumbnail = result[0].get("thumbnail")
            self.storage.store(params, thumbnail, "thumbnail")

        if next == "true":
            self.utils.addNextFolder(result, params)

        return (result, status)

    def scrape(self, params={}):
        self.getNewResultsFunction(params)

        result = self.paginator(params)
        self.common.log(repr(result), 5)
        return result
