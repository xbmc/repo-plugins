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


class BlipTVScraper:
    def __init__(self):
        self.settings = sys.modules["__main__"].settings
        self.language = sys.modules["__main__"].language
        self.plugin = sys.modules["__main__"].plugin
        self.dbg = sys.modules["__main__"].dbg
        self.cache = sys.modules["__main__"].cache
        self.common = sys.modules["__main__"].common
        self.utils = sys.modules["__main__"].utils
        self.storage = sys.modules["__main__"].storage

        self.urls = {}
        self.urls['show_episodes'] = "http://blip.tv/pr/show_get_full_episode_list?users_id=%s&lite=0&esi=1&page=%s"
        self.urls['special'] = "http://blip.tv/%s"
        self.urls['main'] = "http://blip.tv"
        self.urls['search_shows'] = "http://blip.tv/search/get_show_results?q=%s&page=%s&no_wrap=1"
        self.urls['search_episodes'] = "http://blip.tv/search/get_episode_results?q=%s&page=%s&no_wrap=1"
        self.urls['category_recent_videos'] = "http://blip.tv/pr/channel_get_recent_episodes?channels_id=%s&page=%s&no_wrap=1"
        self.urls['category_trending_videos'] = "http://blip.tv/pr/channel_get_trending_episodes?channels_id=%s&page=%s&no_wrap=1"
        self.urls['category_popular_videos'] = "http://blip.tv/pr/channel_get_popular_episodes?channels_id=%s&page=%s&no_wrap=1"
        self.urls['category_az_listing'] = "http://blip.tv/pr/channel_get_directory_listing?channels_id=%s&section=all&page=%s&no_wrap=1"
        self.urls['category_staff_picks'] = "http://blip.tv/pr/channel_get_staff_picks?channels_id=%s&page=%s&no_wrap=1"
        self.urls['category_audience_favs'] = "http://blip.tv/pr/channel_get_audience_faves?channels_id=%s&page=%s&no_wrap=1"
        self.urls['home_popular'] = "http://blip.tv/pr/home_get_popular_shows?page=%s&no_wrap=1"
        self.urls['home_trending'] = "http://blip.tv/pr/home_get_growing_shows?page=%s&no_wrap=1"
        self.urls['home_new'] = "http://blip.tv/pr/home_get_new_shows?page=%s&no_wrap=1"

    def extractAndResizeThumbnail(self, item):
        thumbnail = self.common.parseDOM(item, "div", attrs={"class": "PosterCard"}, ret="style")[0]
        if thumbnail.find(":url("):
            thumbnail = thumbnail[thumbnail.find(":url(") + 5:]
            thumbnail = thumbnail[:thumbnail.find(");")]
            thumbnail = thumbnail.replace("&w=220", "&w=440")
            thumbnail = thumbnail.replace("&h=325", "&h=650")
        return thumbnail

    def searchShow(self, params={}):
        self.common.log("")
        get = params.get
        self.common.log(repr(params))

        next = True
        items = []
        page = int(get("page", "0")) + 1

        while next:
            tmp = []
            next = False
            params["page"] = str(page)

            url = self.createUrl(params, page)
            result = self.common.fetchPage({"link": url})

            self.common.log("result " + repr(result["content"]))

            dom_pages = self.common.parseDOM(result["content"], "div", {"class": "PosterCardWrap"})

            self.common.log("found items " + repr(dom_pages), 4)
            for item in dom_pages:
                thumbnail = self.extractAndResizeThumbnail(item)
                title = self.common.parseDOM(item, "h1", attrs={"class": "ShowTitle"})[0]
                name = self.common.parseDOM(title, "a")[0]
                link = self.common.parseDOM(title, "a", ret="href")[0]
                tmp.append({"path": get("path"), "show": link, "scraper": "show", "Title": self.common.replaceHTMLCodes(name.strip()), "thumbnail": thumbnail})

            if len(tmp) > 0 and page < 50:
                items += tmp
                next = True
            page += 1

        self.common.log("Done " + repr(items))
        return items

    def searchEpisodes(self, params={}):
        self.common.log("")
        self.common.log(repr(params))

        next = "true"
        episodes = []
        page = 1

        while next == "true":
            next = "false"

            url = self.createUrl(params, page)

            result = self.common.fetchPage({"link": url})
            lst = self.common.parseDOM(result["content"], "div", {"class": "EpisodeCard Extended"})

            if len(lst) > 0 and page <= 20:
                next = "true"

            for ep in lst:
                title = self.common.parseDOM(ep, "h5", ret="title")
                videoid = self.common.parseDOM(ep, "a", attrs={"class": "EpisodeThumb"}, ret="href")
                image = self.common.parseDOM(ep, "img", attrs={"class": "ThumbnailImage"}, ret="src")

                item = {}
                item["videoid"] = videoid[0][videoid[0].rfind("-") + 1:]
                item["Title"] = self.common.replaceHTMLCodes(title[0].strip())
                item["thumbnail"] = image[0]
                episodes.append(item)
            page += 1

        if len(episodes) > 0:
            self.storage.store(params, episodes[0]["thumbnail"], "thumbnail")

        return episodes

    #this function should scrape the onmouse over menu found in Browse on the main page
    def scrapeCategories(self, params={}):
        self.common.log("")
        get = params.get

        url = self.createUrl(params)
        result = self.common.fetchPage({"link": url})

        lst = self.common.parseDOM(result["content"], "div", attrs={"class": "Browse HoverDropDown"})
        ul_lst = self.common.parseDOM(lst, "ul", attrs={"class": "List"})
        names = self.common.parseDOM(ul_lst, "a")
        ids = self.common.parseDOM(ul_lst, "a", ret="href")

        categories = []
        if (len(names) == len(ids)):
            for index, id in enumerate(ids):
                item = {}
                item["Title"] = self.common.replaceHTMLCodes(names[index])
                item["scraper"] = get("scraper")
                item["category"] = urllib.quote_plus(id)
                categories.append(item)

        return categories

    # This function should return the videos listing minus staff picks
    def scrapeCategoryVideos(self, params={}):
        self.common.log("")
        get = params.get

        self.scrapeChannelId(params)

        episodes = []
        page = 1
        tester = True

        while tester:
            url = self.createUrl(params, page)
            result = self.common.fetchPage({"link": url})

            lst = self.common.parseDOM(result["content"], "div", attrs={"class": "EpisodeListCard"})

            if not lst:
                tester = False
                continue

            for episode in lst:
                details = self.common.parseDOM(episode, "a", attrs={"class": "EpisodeThumb"})

                id = self.common.parseDOM(episode, "a", attrs={"class": "EpisodeThumb"}, ret="href")
                image = self.common.parseDOM(details, "img", ret="src")
                title = self.common.parseDOM(episode, "h3", ret="title")

                item = {}
                item["videoid"] = id[0][id[0].rfind("-") + 1:]
                item["Title"] = self.common.replaceHTMLCodes(title[0])
                item["thumbnail"] = image[0]
                episodes.append(item)

            page += 1

        if get("channel_id"):
            del params["channel_id"]

        return episodes

    def scrapeCategoryFeaturedShows(self, params={}):
        self.common.log("")
        get = params.get

        self.scrapeChannelId(params)

        tester = True
        shows = []
        page = 1
        while tester:
            url = self.createUrl(params, page)
            result = self.common.fetchPage({"link": url})

            show_list = self.common.parseDOM(result["content"], "div", attrs={"class": "PosterCardWrap"})

            if not show_list:
                tester = False
                continue

            for show in show_list:
                thumbnail = self.extractAndResizeThumbnail(show)
                title = self.common.parseDOM(show, "h1", attrs={"class": "ShowTitle"})[0]
                name = self.common.parseDOM(title, "a")[0]
                link = self.common.parseDOM(title, "a", ret="href")[0]

                item = {}
                item["show"] = link
                item["scraper"] = "show"
                item["thumbnail"] = thumbnail
                item["Title"] = self.common.replaceHTMLCodes(name)

                shows.append(item)

            page += 1

        if get("channel_id"):
            del params["channel_id"]

        return shows

    def scrapeChannelId(self, params={}):
        self.common.log("")
        url = self.createUrl(params)
        result = self.common.fetchPage({"link": url})
        channel_id = self.common.parseDOM(result["content"], "div", attrs={"id": "ChannelHeading"}, ret="data-id")
        if channel_id:
            self.common.log(repr(channel_id))
            params["channel_id"] = channel_id[0]
            del params["category"]

    def scrapeCategoryShows(self, params={}):
        self.common.log("")
        get = params.get

        self.scrapeChannelId(params)

        tester = True
        shows = []
        page = 1
        while tester:
            url = self.createUrl(params, page)
            result = self.common.fetchPage({"link": url})

            show_list = self.common.parseDOM(result["content"], "div", attrs={"class": "ChannelDirectoryItem"})

            if not show_list or page > 19:
                tester = False
                continue

            for show in show_list:
                h3 = self.common.parseDOM(show, "h3")

                ids = self.common.parseDOM(h3, "a", ret="href")
                titles = self.common.parseDOM(h3, "a")
                images = self.common.parseDOM(show, "img", attrs={"class": "Poster"}, ret="src")

                item = {}
                item["show"] = ids[0]
                item["scraper"] = "show"
                item["thumbnail"] = images[0]
                item["Title"] = self.common.replaceHTMLCodes(titles[0])

                shows.append(item)
            page += 1

        if get("channel_id"):
            del params["channel_id"]

        return shows

    def addShowToMyFavorites(self, params={}):
        self.common.log("")
        get = params.get

        params["scraper"] = "show"
        url = self.createUrl(params)
        result = self.common.fetchPage({"link": url})

        showinfo = self.common.parseDOM(result["content"], "div", attrs={"class": "Show"})
        show_name = self.common.parseDOM(showinfo, "h1")
        show_poster = self.common.parseDOM(result["content"], "div", attrs={"class": "ShowPoster"})
        thumbnail = self.common.parseDOM(show_poster, "img", ret="src")

        if show_name:
            item = {}
            item["Title"] = self.common.replaceHTMLCodes(show_name[0].strip())
            if thumbnail:
                item["thumbnail"] = thumbnail[0]
            item["scraper"] = "show"
            item["show"] = get("show")
            self.storage.addToMyFavoritesShow(params, item)

    def scrapeUserId(self, params={}):
        self.common.log("")

        url = self.createUrl(params)
        result = self.common.fetchPage({"link": url})
        user_id = self.common.parseDOM(result["content"], "div", attrs={"id": "PageInfo"}, ret="data-users-id")

        if user_id:
            self.common.log("found user_id " + repr(user_id))
            params["user_id"] = user_id[0]

    def scrapeShowVideos(self, params={}):
        self.common.log("")
        get = params.get

        self.scrapeUserId(params)
        episodes = []

        original_page = int(get("page", "0"))
        per_page = (10, 15, 20, 25, 30, 40, 50)[int(self.settings.getSetting("perpage"))]
        eps_per_page = 12

        max_pages = per_page / eps_per_page + 1
        start_page = original_page * per_page / eps_per_page + 1

        page = start_page
        tester = True
        while tester:
            url = self.createUrl(params, page)
            result = self.common.fetchPage({"link": url})

            studio = self.common.parseDOM(result["content"], "strong")
            if studio:
                studio = studio[0].strip()

            ep_list = self.common.parseDOM(result["content"], "div", attrs={"class": "EpisodeList"})
            lst = self.common.parseDOM(ep_list, "li")

            if not lst or page > (max_pages + start_page):
                tester = False
                continue

            for episode in lst:
                episode = episode.replace("\t","")

                id = self.common.parseDOM(episode, "a", attrs={"class": "ArchiveCard"}, ret="href")
                image = self.common.parseDOM(episode, "img", ret="src")
                title = self.common.parseDOM(episode, "span", attrs={"class": "Title"}, ret="title")

                item = {}
                item["videoid"] = id[0][id[0].rfind("-") + 1:]
                item["Title"] = self.common.replaceHTMLCodes(title[0].strip())
                item["thumbnail"] = image[0]
                item["Studio"] = studio

                episodes.append(item)
            page += 1

        if get("user_id"):
            del params["user_id"]

        if (len(episodes) > 0):
            episodes = episodes[((per_page * original_page) - (eps_per_page * (start_page - 1))):]
            if (len(episodes) > per_page):
                episodes = episodes[:per_page]
                self.utils.addNextFolder(episodes, params)

        return episodes

    def scrapeShowsHomepageFeed(self, params={}):
        self.common.log(repr(params))

        tester = True
        shows = []
        page = 1

        while tester:
            url = self.createUrl(params, page)
            result = self.common.fetchPage({"link": url})

            show_list = self.common.parseDOM(result["content"], "div", attrs={"class": "ChannelDirectoryItem"})

            if not show_list:
                tester = False
                continue
            for show in show_list:
                h3 = self.common.parseDOM(show, "h3")
                show_name = self.common.parseDOM(h3[0], "a", ret="href")
                titles = self.common.parseDOM(h3[0], "a")
                images = self.common.parseDOM(show, "img", attrs={"class": "Poster"}, ret="src")

                item = {}
                item["show"] = show_name[0]
                item["scraper"] = "show"
                item["thumbnail"] = images[0]
                item["Title"] = self.common.replaceHTMLCodes(titles[0])

                shows.append(item)
            page += 1

        return shows

#================================== Common ============================================
    def getNewResultsFunction(self, params={}):
        self.common.log("")
        get = params.get

        function = ""
        if get("scraper") in ['browse_shows', 'staff_picks', 'favorites', 'new_episodes', 'popular_episodes', 'trending_episodes'] and not get("category") and not get("channel_id") and not get("user_id"):
            params["folder"] = "true"
            function = self.scrapeCategories

        if get("category"):
            params["folder"] = "true"
            if get("scraper") in ['browse_shows']:
                function = self.scrapeCategoryShows
            if get("scraper") in ['staff_picks', 'favorites']:
                function = self.scrapeCategoryFeaturedShows
            if get("scraper") in ['popular_episodes', 'new_episodes', 'trending_episodes']:
                del params["folder"]
                function = self.scrapeCategoryVideos

        if get("scraper") == "search":
            function = self.searchEpisodes

        if get("scraper") == "show_search":
            params["folder"] = "true"
            function = self.searchShow

        if get("scraper") == "show":
            function = self.scrapeShowVideos

        if get("scraper") in ["new_shows", "popular_shows", "trending_shows"]:
            params["folder"] = "true"
            function = self.scrapeShowsHomepageFeed

        if function:
            params["new_results_function"] = function

        return True

    def createUrl(self, params={}, page_override=0):
        self.common.log("")
        get = params.get
        page = str(int(get("page", "0")) + 1)
        if page_override > 0:
            page = page_override

        url = self.urls['main']

        if get("scraper") == "browse_shows" and get("channel_id"):
            url = self.urls['category_az_listing'] % (get("channel_id", ""), page)

        if get("scraper") == "staff_picks" and get("channel_id"):
            url = self.urls['category_staff_picks'] % (get("channel_id", ""), page)

        if get("scraper") == "favorites" and get("channel_id"):
            url = self.urls['category_audience_favs'] % (get("channel_id", ""), page)

        if get("scraper") == "popular_episodes" and get("channel_id"):
            url = self.urls["category_popular_videos"] % (get("channel_id", ""), page)

        if get("scraper") == "trending_episodes" and get("channel_id"):
            url = self.urls["category_trending_videos"] % (get("channel_id", ""), page)

        if get("scraper") == "new_episodes" and get("channel_id"):
            url = self.urls["category_recent_videos"] % (get("channel_id", ""), page)

        if get("category"):
            url = self.urls['main'] + urllib.unquote_plus(get("category", ""))

        if get("scraper") == "popular_shows":
            url = self.urls['home_popular'] % page

        if get("scraper") == "trending_shows":
            url = self.urls['home_trending'] % page

        if get("scraper") == "new_shows":
            url = self.urls['home_new'] % page

        if get("scraper") == "show":
            if get("show") and not get("user_id"):
                url = self.urls['main'] + get("show")
            elif get("user_id"):
                url = self.urls['show_episodes'] % (get("user_id"), page)

        if get("scraper") == "search":
            url = self.urls["search_episodes"] % (urllib.unquote_plus(get("search")), page)

        if get("scraper") == "show_search":
            url = self.urls["search_shows"] % (urllib.unquote_plus(get("search")), page)

        return url

    def paginator(self, params={}):
        self.common.log("")
        get = params.get

        result = []
        next = 'false'
        page = int(get("page", "0"))
        per_page = (10, 15, 20, 25, 30, 40, 50)[int(self.settings.getSetting("perpage"))]
        path = get("path", "/root")

        if get("page") and not get("scraper") in ["show", "search"]:
            del params["page"]
        if get("path"):
            del params["path"]

        result = self.cache.cacheFunction(params["new_results_function"], params)

        params["path"] = path
        params["page"] = str(page)

        if not get("folder") and not get("scraper") == "show":
            if (per_page * (page + 1) < len(result)):
                next = 'true'

            if get("fetch_all", "false") == "false":
                result = result[(per_page * page):(per_page * (page + 1))]

            if len(result) == 0:
                return result

        if next == "true":
            self.utils.addNextFolder(result, params)

        return result

    def scrape(self, params={}):
        self.common.log("")

        self.getNewResultsFunction(params)

        return self.paginator(params)
