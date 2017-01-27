import urllib2
import json
import re
from BeautifulSoup import BeautifulSoup

class CorriereTV:
    __USERAGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:50.0) Gecko/20100101 Firefox/50.0"
    __BaseUrl = "http://video.corriere.it"
    __noThumb = "http://images2.corriereobjects.it/methode_image/placeholder/320x240_A1.jpg"

    def __init__(self):
        opener = urllib2.build_opener()
        # Use Firefox User-Agent
        opener.addheaders = [('User-Agent', self.__USERAGENT)]
        urllib2.install_opener(opener)

    def getChannels(self):
        pageUrl = self.__BaseUrl
        data = urllib2.urlopen(pageUrl).read()
        tree = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
        
        list = tree.find("ul", {"id": "menu-v"}).findAll("li", recursive=False)
        channels = []
        for item in list:
            channel = {}
            link = item.find("a")
            channel["title"] = link.text
            channel["url"] = link["href"]
            
            if channel["url"][0] == "/":
                channel["url"] = self.__BaseUrl + channel["url"]
            if channel["url"][-1:] != "/":
                channel["url"] = channel["url"] + "/"
            if channel["url"] == "http://video.corriere.it/archivio/":
                continue
            
            channels.append(channel)
        
        return channels

    def getVideoByChannel(self, pageUrl):
        data = urllib2.urlopen(pageUrl).read()
        tree = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
        
        script = tree.find("script", text=re.compile("channel"))
        match = re.search(r'channel\s*=\s*({[^;]+});', script, re.DOTALL)
        string = match.group(1)
        channel = json.loads(string)
        playlistId = channel["hierarchicalAssetProperties"]["playlistId"]
        
        pageUrl = self.__BaseUrl + "/p/" + playlistId
        data = urllib2.urlopen(pageUrl).read()
        tree = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
        
        articles = tree.findAll("article")
        videos = []
        for article in articles:
            video = {}
            video["videoId"] = article["class"][-36:]
            
            thumb = article.find("img")
            if thumb is not None:
                video["thumb"] = thumb["data-original"]
            else:
                video["thumb"] = self.__noThumb
            
            # DIRTY ROTTEN HTML
            figcaption = article.find("figcaption")
            if figcaption is None:
                figcaption = article.findNextSibling("figcaption")
            
            video["title"] = figcaption.find("h4").text
            video["date"] = figcaption.find("h3").text

            videos.append(video)
            
        return videos

    def getVideoUrl(self, videoId):
        url = "http://video.corriere.it/fragment-includes/video-includes/%s/%s/%s.json" % (videoId[:2], videoId[2:4], videoId)
        response = json.load(urllib2.urlopen(url))
        
        for mediaFile in response["mediaProfile"]["mediaFile"]:
            if mediaFile["mimeType"] == "application/vnd.apple.mpegurl":
                videoUrl = mediaFile["value"]
                break
        return videoUrl
        