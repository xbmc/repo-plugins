import re
import urllib2
import json
from BeautifulSoup import BeautifulSoup

class FlopTV:
    __USERAGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:50.0) Gecko/20100101 Firefox/50.0"
    __BASEURL = "http://www.floptv.tv"
    
    def __init__(self):
        opener = urllib2.build_opener()
        # Use Firefox User-Agent
        opener.addheaders = [('User-Agent', self.__USERAGENT)]
        urllib2.install_opener(opener)

    def getShows(self):
        pageUrl = "http://www.floptv.tv/show/"
        data = urllib2.urlopen(pageUrl).read()
        tree = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
        
        shows = []
        sections = tree.find("div", "all-shows").findAll("section")
        for section in sections:
            items = section.findAll("li")
            for item in items:
                show = {}
                show["title"] = item.text
                show["thumb"] = item.find("img")["src"]
                show["pageUrl"] = self.__BASEURL + item.find("a")["href"]
                shows.append(show)
       
        return shows

    def getVideoByShow(self, pageUrl):
        data = urllib2.urlopen(pageUrl).read()
        tree = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)

        videos = []
        sections = tree.findAll("section", "tabella")
        for section in sections:
            items = section.find("tbody").findAll("tr")
            for item in items:
                video = {}
                data = item.findAll("td")
                video["title"] = data[0].text + " " + data[2].text
                video["thumb"] = item.find("img")["src"].replace("-62x36.jpg", "-307x173.jpg")
                video["pageUrl"] = self.__BASEURL + item.find("a")["href"]
                videos.append(video)
            
        return videos

    def getVideoUrl(self, pageUrl):
        # Parse the HTML page to get the Video URL
        data = urllib2.urlopen(pageUrl).read()
        tree = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
        
        iframeUrl = "http:" + tree.find("iframe", {"id": "player"})["src"]
        req = urllib2.Request(iframeUrl)
        req.add_header('Referer', pageUrl)
        data = urllib2.urlopen(req).read()
        tree = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
        
        script = tree.find("script", text=re.compile("playerConfig"))
        match = re.search(r'sources\s*:\s*(\[[^\]]+\])', script, re.DOTALL)
        string = match.group(1)
        
        # Convert to JSON
        string = string.replace('file:','"file":')
        string = string.replace('type:','"type":')
        
        sources = json.loads(string)
        for source in sources:
            if source["type"] == "hls":
                videoUrl = source["file"]
                break
        
        return videoUrl
        