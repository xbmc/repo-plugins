import urllib2
import re
import json
from BeautifulSoup import BeautifulSoup

class Live:
    __MOBILE_USERAGENT = "Mozilla/5.0 (Linux; U; Android 4.2.2; it-it; GT-S7582 Build/JDQ39) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30"
    __USERAGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:50.0) Gecko/20100101 Firefox/50.0"

    def getMobileUrl(self):
        pageUrl = "http://www.federtennis.it/supertennis/app/app-get-live-stream.asp"
        req = urllib2.Request(pageUrl, headers={'User-Agent': self.__MOBILE_USERAGENT})
        htmlData = urllib2.urlopen(req).read()
        return htmlData
        
    def getUrl(self):
        pageUrl = "http://advplayer.morescreens.eu/supertennis/index1.php"
        req = urllib2.Request(pageUrl, headers={'User-Agent': self.__USERAGENT})        
        htmlData = urllib2.urlopen(req).read()
        
        tree = BeautifulSoup(htmlData, convertEntities=BeautifulSoup.HTML_ENTITIES)
        script = tree.find("body").find("script").text
        match = re.search(r'sources\s*:\s*(\[[^\]]+\])', script, re.DOTALL)
        string = match.group(1)
        
        # Convert string to JSON
        string = re.sub(r'^\s+(\/\/.*)$', "", string, flags=re.MULTILINE)
        string = string.replace('type', '"type"')
        string = string.replace('src', '"src"')
        string = re.sub(r'},\s*\]', "}]", string, flags=re.MULTILINE)
        
        sources = json.loads(string)
        videoUrl = sources[0]["src"]
        if videoUrl.startswith("//"):
            videoUrl = "http:" + videoUrl
        
        # Return HD HLS stream
        return  videoUrl
