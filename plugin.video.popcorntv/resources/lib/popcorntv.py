import urllib2
import urlparse
import re
import json
from BeautifulSoup import BeautifulSoup
from BeautifulSoup import BeautifulStoneSoup

class PopcornTV:
    __USERAGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:51.0) Gecko/20100101 Firefox/51.0"

    def __init__(self):
        opener = urllib2.build_opener()
        # Use Firefox User-Agent
        opener.addheaders = [('User-Agent', self.__USERAGENT)]
        urllib2.install_opener(opener)

    def getCategories(self):
        pageUrl = "https://popcorntv.it/"
        data = urllib2.urlopen(pageUrl).read()
        tree = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)

        categories = []
        list = tree.find("ul", {"id":"pctv-main-menu-list"}).findAll("li")
        for item in list:
            category = {}
            category["title"] = item.find("a").text.strip()
            if category["title"] not in ("Serie Tv", "News"):
                category["url"] = item.find("a")["href"]
                categories.append(category)
        
        return categories

    def getSubCategories(self, pageUrl):
        data = urllib2.urlopen(pageUrl).read()
        htmlTree = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
        urlParsed = urlparse.urlsplit(pageUrl)
        urlSite = urlParsed.scheme + "://" + urlParsed.netloc

        subcategories = []
        list = htmlTree.findAll("div", "async_box")
        for item in list:
            link = item.find("a")
            if link is None:
                # Anime section
                link = item.parent
            subcategory = {}
            subcategory["title"] = link.text.strip()
            subcategory["url"] = link["href"]
            if subcategory["url"].startswith("/"):
                subcategory["url"] = urlSite + subcategory["url"]
            # Don't insert duplicate items
            if subcategory not in subcategories:
                subcategories.append(subcategory)
            
        return subcategories
        
    def getVideoBySubCategories(self, pageUrl):
        data = urllib2.urlopen(pageUrl).read()
        htmlTree = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
        urlParsed = urlparse.urlsplit(pageUrl)
        
        videoList = []
        
        if urlParsed.netloc == "cinema.popcorntv.it":
            # Show video in "Lista film"
            items = htmlTree.findAll("a", "episodio-link")
        else:
            # Show video in "Tutti gli episodi"
            items = htmlTree.find("div", {"role": "tabpanel", "id": "all"}).findAll("a", "episodio-link")

        for item in items:
            video = {}
            video["title"] = item["title"].strip()
            video["plot"] = item["data-content"]
            video["url"] = item["href"]
            # strip() is needed because image URLs may have a leading space
            video["thumb"] = item.find("img")["src"].strip()
            if video["thumb"].startswith("//"):
                video["thumb"] = urlParsed.scheme +":" + video["thumb"]
            videoList.append(video)
            
        # Get pagination URLs
        nextPageUrl = None
        prevPageUrl = None

        pagination = htmlTree.find("ul", "pagination")
        if pagination is not None:
            prevPage = pagination.find("a", {"rel": "prev"})
            if prevPage is not None:
                prevPageUrl = prevPage["href"]
                
            nextPage = pagination.find("a", {"rel": "next"})
            if nextPage is not None:
                nextPageUrl = nextPage["href"]
            
        page = {}
        page["videoList"] = videoList
        page["prevPageUrl"] = prevPageUrl
        page["nextPageUrl"] = nextPageUrl
        return page

    def getVideoMetadata(self, pageUrl):
        data = urllib2.urlopen(pageUrl).read()
        htmlTree = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
        
        cover = htmlTree.find("div", "row scheda-cover")
        if cover is not None:
            # Cinema section
            url = cover.find("a")["href"]
            return self.getVideoMetadata(url)
        
        jsonText = htmlTree.find("script", {"type":"application/ld+json"}).text
        # Fix JSON
        jsonText = re.sub(r'"description":\s*"([^"]*?)"', '"description": ""', jsonText, flags=re.MULTILINE)
        params = json.loads(jsonText)

        metadata = {}
        metadata["title"] = params["name"]
        metadata["thumb"] = params["thumbnailUrl"][0]
        
        contentUrl= params["contentUrl"]
        urlParsed = urlparse.urlsplit(contentUrl)
        if urlParsed.netloc == "player.vimeo.com":
            metadata["videoUrl"] = self.getVimeoUrl(contentUrl, pageUrl)
        elif "www.youtube.com":
            metadata["videoUrl"] = self.getYouTubeUrl(contentUrl)
        else:
            metadata["videoUrl"] = ""
            
        return metadata

    def getVimeoUrl(self, contentUrl, refererUrl):
        req = urllib2.Request(contentUrl)
        req.add_header("Referer", refererUrl)
        data = urllib2.urlopen(req).read()
        
        match = re.search(r'"hls":({.*?}),"progressive":', data, re.DOTALL)
        string = match.group(1)
        
        hls = json.loads(string)
        videoUrl = hls["cdns"]["fastly_skyfire"]["url"]
        return videoUrl
        
    def getYouTubeUrl(self, contentUrl):
        videoId = contentUrl[contentUrl.rfind("/")+1:contentUrl.rfind("?")]
        videoUrl = "plugin://plugin.video.youtube/play/?video_id=%s" % videoId
        return videoUrl
