# -*- coding: utf-8 -*-
try:
  import urllib.request as urllib2
except ImportError:
    import urllib2
import json
import re

class RaiPlay:
    # Raiplay android app
    UserAgent = "Dalvik/1.6.0 (Linux; U; Android 4.2.2; GT-I9105P Build/JDQ39)"
    MediapolisUserAgent = "Android 4.2.2 (smart) / RaiPlay 2.1.3 / WiFi"
    
    noThumbUrl = "http://www.rai.it/dl/components/img/imgPlaceholder.png"
    
    # From http://www.raiplay.it/mobile/prod/config/RaiPlay_Config.json
    baseUrl = "https://www.raiplay.it/"
    channelsUrl = "http://www.rai.it/dl/RaiPlay/2016/PublishingBlock-9a2ff311-fcf0-4539-8f8f-c4fee2a71d58.html?json"
    localizeUrl = "http://mediapolisgs.rai.it/relinker/relinkerServlet.htm?cont=201342"
    menuUrl = "http://www.rai.it/dl/RaiPlay/2016/menu/PublishingBlock-20b274b1-23ae-414f-b3bf-4bdc13b86af2.html?homejson"
    #palinsestoUrl = "https://www.raiplay.it/dl/palinsesti/Page-e120a813-1b92-4057-a214-15943d95aa68-json.html?canale=[nomeCanale]&giorno=[dd-mm-yyyy]"
    palinsestoUrl = "https://www.raiplay.it/palinsesto/guidatv/lista/[idCanale]/[dd-mm-yyyy].html"
    AzTvShowPath = "/dl/RaiTV/RaiPlayMobile/Prod/Config/programmiAZ-elenco.json"
    RaiSportWebUrl= "https://www.raisport.rai.it/dirette.html"
    
    def __init__(self):
        opener = urllib2.build_opener()
        # Set User-Agent
        opener.addheaders = [('User-Agent', self.UserAgent)]
        urllib2.install_opener(opener)
    
    def getCountry(self):
        try:
            response = urllib2.urlopen(self.localizeUrl).read()
        except urllib2.HTTPError:
            response = "ERROR"
        return response
        
    def getChannels(self):
        response = json.load(urllib2.urlopen(self.channelsUrl))
        return response["dirette"]
    
    def getRaiSportPage(self):
        chList = []
        response = urllib2.urlopen(self.RaiSportWebUrl).read()
        m = re.search('<ul class="canali">(?P<list>.*)</ul>', response, re.S)
        if m:
            channels = re.findall ('<li>(.*?)</li>', m.group('list'), re.S)
            for ch in channels:
                url = re.search('''data-video-url=['"](?P<url>[^'^"]+)['"]''', ch)
                if url:
                    url = url.group('url')
                    icon = re.search('''stillframe=['"](?P<url>[^'^"]+)['"]''', ch )
                    if icon:
                        icon = self.getUrl(icon.group('url'))
                    else:
                        icon = ''
                    title = re.search(">(?P<title>[^<]+)</a>", ch )
                    if title:
                        title = title.group('title')
                    else:
                        title = 'Rai Sport Web Link'
                    chList.append({'title':title, 'url':url, 'icon':icon})
        
        return chList
        
    def getProgrammes(self, channelName, epgDate):
        channelTag = channelName.replace(" ", "-").lower()
        url = self.palinsestoUrl
        url = url.replace("[idCanale]", channelTag)
        url = url.replace("[dd-mm-yyyy]", epgDate)
        return urllib2.urlopen(url).read()
        
    def getMainMenu(self):
        response = json.load(urllib2.urlopen(self.menuUrl))
        return response["menu"]

    # RaiPlay Genere Page
    # RaiPlay Tipologia Page
    def getCategory(self, pathId):
        url = self.getUrl(pathId)
        response = json.load(urllib2.urlopen(url))
        return response["blocchi"]
  
    # Raiplay Tipologia Item
    def getProgrammeList(self, pathId):
        url = self.getUrl(pathId)
        response = json.load(urllib2.urlopen(url))
        return response
    
    #  PLR programma Page
    def getProgramme(self, pathId):
        url = self.getUrl(pathId)
        response = json.load(urllib2.urlopen(url))
        return response
        
    def getContentSet(self, url):
        url = self.getUrl(url)
        response = json.load(urllib2.urlopen(url))
        return response["items"]
    
    def getVideoMetadata(self, pathId):
        url = self.getUrl(pathId)
        response = json.load(urllib2.urlopen(url))
        return response["video"]
    
    def getUrl(self, pathId):
        pathId = pathId.replace(" ", "%20")
        if pathId[0:2] == "//":
            url = "http:" + pathId
        elif pathId[0] == "/":
            url = self.baseUrl[:-1] + pathId
        else:
            url = pathId
        return url
        
    def getThumbnailUrl(self, pathId):
        if pathId == "":
            url = self.noThumbUrl
        else:
            url = self.getUrl(pathId)
            url = url.replace("[RESOLUTION]", "256x-")
        return url
 