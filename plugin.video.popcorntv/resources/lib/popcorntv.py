import urllib2
import urlparse
import re
from BeautifulSoup import BeautifulSoup
from BeautifulSoup import BeautifulStoneSoup


class PopcornTV:
    __USERAGENT = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:46.0) Gecko/20100101 Firefox/46.0"

    def __init__(self):
        opener = urllib2.build_opener()
        # Use Firefox User-Agent
        opener.addheaders = [('User-Agent', self.__USERAGENT)]
        urllib2.install_opener(opener)

    def getCategories(self):
        pageUrl = "http://popcorntv.it/"
        data = urllib2.urlopen(pageUrl).read()
        tree = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
        categories = []
        list = tree.findAll("div", "megamenu")
        for item in list:
            link = item.parent.find("a")
            category = {}
            category["title"] = link.text.strip()
            category["url"] = link["href"]
            categories.append(category)
       
        return categories

    def getSubCategories(self, pageUrl):
        data = urllib2.urlopen(pageUrl).read()
        htmlTree = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
        urlParsed = urlparse.urlsplit(pageUrl)
        urlSite = urlParsed.scheme + "://" + urlParsed.netloc

        subcategories = []
        list = htmlTree.findAll("div", "lista-serie")
        for item in list:
            link = item.find("a")
            subcategory = {}
            subcategory["title"] = link.text.strip()
            subcategory["url"] = link["href"]
            if not subcategory["url"].startswith("http"):
                subcategory["url"] = urlSite + subcategory["url"]
            # Don't insert duplicate items
            if subcategory not in subcategories:
                subcategories.append(subcategory)
            
        return subcategories
        
    def getVideoBySubCategories(self, pageUrl):
        data = urllib2.urlopen(pageUrl).read()
        htmlTree = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
        
        videoList = []
        
        if pageUrl.startswith("http://cinema.popcorntv.it"):
            # Show video in "Altri fim"
            items = htmlTree.find(text="Altri film").parent.findNextSiblings("a")
        else:
            # Show video in "Tutti gli episodi"
            items = htmlTree.find(text="Tutti gli episodi").parent.findNextSibling("div").findAll("a")
        
        for item in items:
            video = {}
            video["title"] = item["title"].strip()
            video["url"] = item["href"]
            video["thumb"] = item.find("img")["src"]
            videoList.append(video)
            
        # Get pagination URLs
        nextPageUrl = None
        firstPageUrl = None
        lastPageUrl = None
        prevPageUrl = None

        pagination = htmlTree.find("ul", "pagination")
        if pagination is not None:
            prevPage = pagination.find("a", {"rel": "prev"})
            if prevPage is not None:
                prevPageUrl = prevPage["href"]
                firstPage = prevPage.parent.findNextSibling("li").find("a")
                firstPageUrl = firstPage["href"]
                
            nextPage = pagination.find("a", {"rel": "next"})
            if nextPage is not None:
                nextPageUrl = nextPage["href"]
                lastPage = nextPage.parent.findPreviousSibling("li").find("a")
                lastPageUrl = lastPage["href"]
            
        page = {}
        page["videoList"] = videoList
        page["prevPageUrl"] = prevPageUrl
        page["firstPageUrl"] = firstPageUrl
        page["lastPageUrl"] = lastPageUrl
        page["nextPageUrl"] = nextPageUrl
        return page

    def getVideoMetadata(self, pageUrl):
        metadata = {}
        
        data = urllib2.urlopen(pageUrl).read()
        htmlTree = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
        metadata["url"] = htmlTree.find("meta", {"property": "og:url"})['content']
        if metadata["url"] != pageUrl:
            return self.getVideoMetadata(metadata["url"])

        metadata["title"] = htmlTree.find("header","video-heading").text.strip()
        metadata["thumb"] = htmlTree.find("meta", {"property": "og:image"})['content']
        metadata["videoUrl"] = re.search(r'\("vplayerPopcorn","1020","550","(.+?)"', data).group(1)
        
        return metadata

