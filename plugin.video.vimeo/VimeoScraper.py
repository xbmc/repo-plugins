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
import string


class VimeoScraper(object):
    def __init__(self):
        self.settings = sys.modules["__main__"].settings
        self.language = sys.modules["__main__"].language
        self.plugin = sys.modules["__main__"].plugin
        self.dbg = sys.modules["__main__"].dbg
        self.hq_thumbs = self.settings.getSetting("high_quality_thumbs") == "true"

        self.common = sys.modules["__main__"].common
        self.cache = sys.modules["__main__"].cache
        self.utils = sys.modules["__main__"].utils
        
        self.feeds = {}
        self.feeds['channels'] = "http://vimeo.com/channels"
        self.feeds['groups'] = "http://vimeo.com/groups"
        self.feeds['categories'] = "http://vimeo.com/categories"

    def _scrapeCloud(self, params={}):
        self.common.log("")
        get = params.get
        params["path"] = "/root/explore/cloud"
        vobjects = []

        url = self.createUrl(params)
        result = self.common.fetchPage({"link": url})
        cloud = self.common.parseDOM(result["content"], "div", attrs={"id": "cloud"})

        if (len(cloud) > 0):
            title = self.common.parseDOM(cloud, "a")
            href = self.common.parseDOM(cloud, "a", ret="href")

            for i in range(0, len(title)):
                item = {}

                if (len(title[0]) < 3):
                    item["Title"] = title[0].upper()
                else:
                    item["Title"] = string.capwords(title[i].strip())

                item["Title"] = item["Title"].replace("Diy", "DIY")
                category = href[i]
                if (category.rfind(":") > 0):
                    category = category[category.rfind(":") + 1:]
                item["category"] = category 
                if get("scraper") != "categories":
                    item["folder"] = "true"
                item["scraper"] = get("scraper")
                item["thumbnail"] = "explore"
                vobjects.append(item)

        self.common.log("Done")
        return (vobjects, 200)

    def _scrapeThumbnailFormat(self, params={}):
        self.common.log("")
    
        vobjects = []

        url = self.createUrl(params)
        result = self.common.fetchPage({"link": url})

        videos = self.common.parseDOM(result["content"], "div", attrs={"class": "thumbnail_format"})
        pagination = self.common.parseDOM(result["content"], "li", attrs={"class": "arrow"})
        
        next = "false"
        if (len(pagination) > 0):
            if (repr(pagination).find('alt="next"') > 0):
                next = "true"

        avideo = self.common.parseDOM(videos, "div", attrs={"class": "title"})
        athumb = self.common.parseDOM(videos, "img", ret="src")

        for i in range(0, len(avideo)):
            atitle = self.common.parseDOM(avideo[i], "a")
            ahref = self.common.parseDOM(avideo[i], "a", ret="href")

            if len(atitle) > 0 and len(ahref) > 0:
                item = {}
                title = atitle[0]
                item["Title"] = title.strip()
                videoid = ahref[0]
                if (videoid.find("/") > -1):
                    videoid = videoid[videoid.find("/") + 1:]

                item["videoid"] = videoid
                thumbnail = athumb[i]
                if (self.hq_thumbs):
                    if thumbnail.rfind("_200"):
                        thumbnail = thumbnail.replace("_200", "_640")

                overlay = self.settings.getSetting("vidstatus-" + item['videoid'])

                if overlay:
                    item['Overlay'] = int(overlay)

                item["thumbnail"] = thumbnail
                vobjects.append(item)
        
        if next == "true" and len(vobjects):
            vobjects[len(vobjects) -1]["next"] = next
        
        return (vobjects, 200)

    def _scrapeChannelBadgeFormat(self, params={}):
        self.common.log("")
        vobjects = []

        url = self.createUrl(params)

        result = self.common.fetchPage({"link": url})
        pagination = self.common.parseDOM(result["content"], "li", attrs={"class": "arrow"})

        next = "false"
        if (len(pagination) > 0):
            if (repr(pagination).find('alt="next"') > 0):
                next = "true"

        featured = self.common.parseDOM(result["content"], "div", attrs={"id": "featured"})

        if (len(featured) > 0):
            atitle = self.common.parseDOM(featured, "a", ret="title")
            ahref = self.common.parseDOM(featured, "a", ret="href")
            astyle = self.common.parseDOM(featured, "div", attrs={"class": "badge"}, ret="style")
            for i in range(0, len(atitle)):
                item = {}
                item["Title"] = atitle[i].strip()
                channel = ahref[i]
                item["channel"] = channel[channel.rfind("/") + 1:]
                image = astyle[i]
                image = image[image.find("('") + 2:]
                image = image[:image.rfind("')")]
                if (self.hq_thumbs):
                    if (image.rfind("_200")):
                        image = image.replace("_200", "_600")
                item["thumbnail"] = image
                vobjects.append(item)

        if next == "true" and len(vobjects):
            vobjects[len(vobjects) -1]["next"] = next

        self.common.log("Done")
        return (vobjects, 200)

    def _scrapeCategoryBrowser(self, params={}):
        self.common.log("")
        get = params.get
        vobjects = []

        url = self.createUrl(params)
        result = self.common.fetchPage({"link": url})

        categories = self.common.parseDOM(result["content"], "div", attrs={"id": "cat_browse"})

        self.common.log(str(len(categories)))
        if (len(categories) > 0):

            atitle = self.common.parseDOM(categories, "a")
            ahref = self.common.parseDOM(categories, "a", ret="href")

            for i in range(0, len(atitle)):
                item = {}
                title = atitle[i]
                if (title):
                    category = ahref[i]
                    if (category.rfind("/") > 0):
                            category = category[category.rfind("/") + 1:]

                    item["category"] = category
                    item["folder"] = "true"
                    item["Title"] = title.strip()
                    item["thumbnail"] = "explore"
                    item["scraper"] = get("scraper")
                    vobjects.append(item)
        
        self.common.log("Done")
        return (vobjects, 200)

    def _scrapeDetailFormat(self, params={}):
        self.common.log("")
        get = params.get
        vobjects = []
        api = get("scraper")
        api = api[:api.rfind("s")]

        url = self.createUrl(params)
        result = self.common.fetchPage({"link": url})

        details = self.common.parseDOM(result["content"], "div", attrs={"class": "detail_format"})

        pagination = self.common.parseDOM(result["content"], "li", attrs={"class": "arrow"})
        next = "false"
        if (len(pagination) > 0):
            if (repr(pagination).find('alt="next"')):
                next = "true"
        
        items = self.common.parseDOM(details, "div", attrs={"class": "row"})

        for it in items:
            item = {}
            href = self.common.parseDOM(it, "div", attrs={"class": "title"})
            cog = self.common.parseDOM(href, "a", ret="href")[0]
            if (cog.find("/") > -1):
                cog = cog[cog.rfind("/") + 1:]
            if (get("scraper") == "groups"):
                item["group"] = cog
            else:
                item["channel"] = cog

            img = self.common.parseDOM(it, "a", attrs={"class": "thumbnail"})

            thumb = self.common.parseDOM(img, "img", ret="src")
            thumbnail = thumb[0]
            if (self.hq_thumbs and thumbnail.rfind("_200")): 
                thumbnail = thumbnail.replace("_200", "_640")
            item["thumbnail"] = thumbnail
                        
            title = self.common.parseDOM(href, "a")[0]
            title = self.common.replaceHTMLCodes(title)
            item["Title"] = title.strip()
            
            item["api"] = api
            
            vobjects.append(item)

        if next == "true" and len(vobjects):
            vobjects[len(vobjects) -1]["next"] = next

        self.common.log("Done")

        return (vobjects, 200)

    def getNewResultsFunction(self, params={}):
        get = params.get
        function = ""

        if get('scraper') == "groups":
            function = self._scrapeCloud
            if get("category"):
                function = self._scrapeDetailFormat

        if get('scraper') == "channels":
            params["folder"] = "true"
            function = self._scrapeCloud
            if get("featured"):
                function = self._scrapeChannelBadgeFormat
            elif get("category"):
                function = self._scrapeDetailFormat

        if (get("scraper") == 'categories'):
            params["folder"] = "true"
            function = self._scrapeCategoryBrowser
            if get("category"):
                del params["folder"]
                function = self._scrapeThumbnailFormat

        if function:
            params["new_results_function"] = function

    def createUrl(self, params={}):
        self.common.log("")
        get = params.get
        page = str(int(get("page","0")) + 1)
        feed = self.feeds[get("scraper")]

        if (get("category")):
            if (get("scraper") == "categories"):
                feed += "/" + get("category") + "/videos"
            else:
                feed += "/all"
                if (get("page")):
                    feed += "/page:" + page
                feed += "/category:" + get("category")

        if (get("page") and get("category") and get("scraper") == "categories"):
            feed += "/page:" + page

        if (get("sort")):
            feed += "/sort:" + get("sort")

        return feed

    def paginator(self, params={}):
        print repr(params)
        self.common.log(repr(params))
        get = params.get
        print repr(get("fetch_all"))
        status = 303
        result = []
        next = 'false'
        page = int(get("page", "0"))
        per_page = (10, 15, 20, 25, 30, 40, 50,)[int(self.settings.getSetting("perpage"))]

        (result, status) = self.cache.cacheFunction(params["new_results_function"], params)

        self.common.log("paginator new result " + str(repr(len(result[0:50]))))

        if get("fetch_all") != "true":
            if len(result) > 0:
                if result[len(result) -1].get("next"):
                    del result[len(result) -1]["next"]
                    next = "true"

            if (per_page * (page + 1) < len(result)):
                next = 'true'

            if len(result) == 0:
                return (result, status)

        if next == "true":
            self.utils.addNextFolder(result, params)

        return (result, status)

    def scrape(self, params={}):
        self.getNewResultsFunction(params)

        result = self.paginator(params)
        self.common.log(repr(result), 5)
        return result