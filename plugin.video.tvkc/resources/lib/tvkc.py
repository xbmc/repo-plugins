import urllib2
import json
from BeautifulSoup import BeautifulSoup

class TVKC:
    __USERAGENT = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0"
    
    def __init__(self):
        opener = urllib2.build_opener()
        # Use Firefox User-Agent
        opener.addheaders = [('User-Agent', self.__USERAGENT)]
        urllib2.install_opener(opener)
        
    def getSeries(self):
        pageUrl = "http://www.rtvslo.si/tvcapodistria/archivio/"
        data = urllib2.urlopen(pageUrl).read()
        tree = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)

        paging = tree.find("div", {"class": "paging"}).findAll("a")
        links = []
        for page in paging:
            link = page["href"]
            if link not in links:
                links.append(link)
        
        series = []
        while True:
            videos = tree.findAll("div", {"class": "videoSection"})
            for video in videos:
                serie = {}
                serie["title"] = video.text
                serie["url"] = video.find("a")["href"]
                serie["thumb"] = video.find("img")["src"]
                series.append(serie)
            
            if links:
                # Go to next page
                pageUrl = links[0]
                links = links[1:]
                data = urllib2.urlopen(pageUrl).read()
                tree = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
            else:
                break
        
        return series
        
    def getVideoList(self, pageUrl):
        data = urllib2.urlopen(pageUrl).read()
        tree = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)

        videos = []
        items = tree.find("ul", {"id": "videoShows"}).findAll("li")
        for item in items:
            video = {}
            video["title"] = item.find("h4").text
            video["date"] = item.find("p").text
            player = item.find("span", {"class": "player"})
            video["id"] = player["data-recording"]
            options = json.loads(player["data-options"])
            video["thumb"] = options["image"]
            videos.append(video)
            
        return videos
        
    def getVideoMetadata(self, videoId):
        url = "http://api.rtvslo.si/ava/getRecording/%s?client_id=82013fb3a531d5414f478747c1aca622" % videoId
        response = json.load(urllib2.urlopen(url))
        return response["response"]
        
        
