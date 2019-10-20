# -*- coding: utf-8 -*-
try:
    import urllib.request as urllib2
except ImportError:
    import urllib2

import json
import re

try:
    import HTMLParser
except:
    import html.parser as HTMLParser

import xbmc

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
    palinsestoUrl = "https://www.raiplay.it/palinsesto/app/old/[nomeCanale]/[dd-mm-yyyy].json"
    palinsestoUrlHtml = "https://www.raiplay.it/palinsesto/guidatv/lista/[idCanale]/[dd-mm-yyyy].html"
    AzTvShowPath = "/dl/RaiTV/RaiPlayMobile/Prod/Config/programmiAZ-elenco.json"
    
    # Rai Sport urls
    RaiSportMainUrl = 'https://www.raisport.rai.it'
    RaiSportLiveUrl= RaiSportMainUrl + '/dirette.html'
    RaiSportArchivioUrl = RaiSportMainUrl + '/archivio.html'        
    RaiSportSearchUrl = RaiSportMainUrl +  "/atomatic/news-search-service/api/v1/search?transform=false"

    
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
    
    def getRaiSportLivePage(self):
        chList = []
        response = urllib2.urlopen(self.RaiSportLiveUrl).read()
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
    
    def fillRaiSportKeys(self):
        # search for items in main menu
        RaiSportKeys=[]
        
        data = urllib2.urlopen(self.RaiSportMainUrl).read()
        m = re.search("<a href=\"javascript:void\(0\)\">Menu</a>(.*?)</div>", data,re.S)
        if not m: 
            return []
        menu = m.group(0)
        
        links = re.findall("<a href=\"(?P<url>[^\"]+)\">(?P<title>[^<]+)</a>", menu)
        good_links=[]
        for l in links:
            if ('/archivio.html?' in l[0]) and not ('&amp;' in l[0]):
                good_links.append({'title': l[1], 'url' : l[0]})
        
        good_links.append({'title': 'Altri sport', 'url' : '/archivio.html?tematica=altri-sport'})
        
        # open any single page in list and grab search keys
        
        for l in good_links:
            data = urllib2.urlopen(self.RaiSportMainUrl + l['url']).read()

            dataDominio= re.findall("data-dominio=\"(.*?)\"", data)
            dataTematica = re.findall("data-tematica=\"(.*?)\"", data)
            if dataTematica:
                del(dataTematica[0])
                title=dataTematica[0].split('|')[0]
                title = HTMLParser.HTMLParser().unescape(title).encode('utf-8')
                params={'title': title, 'dominio': dataDominio[0], 'sub_keys' : dataTematica}
                
                RaiSportKeys.append(params)
        
        return RaiSportKeys
    
    def getRaiSportVideos(self, key, domain, page):
        videos = []
        header = {
                  'Accept': 'application/json, text/javascript, */*; q=0.01' ,
                  'Content-Type': 'application/json; charset=UTF-8',
                  'Origin': 'https://www.raisport.rai.it',
                  'Referer': 'https://www.raisport.rai.it/archivio.html',
                  'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
                  'X-Requested-With': 'XMLHttpRequest',
                 }
        page = int(page)
        pageSize = 50

        payload = {
            "page": page,
            "pageSize": pageSize,
            "filters":{
                "tematica":[key],
                "dominio": domain
            }
        }
        postData=json.dumps(payload)
        req = urllib2.Request(self.RaiSportSearchUrl, postData, header)
        
        response = urllib2.urlopen(req)
        if response.code != 200:
            return []
        
        data = response.read()
        j = json.loads(data)
        
        if 'hits' in j:
            h = j['hits']
            if 'hits' in h:
                for hh in h['hits']:
                    if '_source' in hh:
                        news_type = hh['_source']['tipo']
                        if news_type == 'Video' and 'media' in hh['_source']:
                            relinker_url = hh['_source']['media']['mediapolis']

                            if 'durata' in hh['_source']['media']:
                                d= hh['_source']['media']['durata'].split(":")
                                duration = int(d[0])*3600 + int(d[1])*60 + int(d[2])
                            else:
                                duration = 0

                            icon = self.RaiSportMainUrl + hh['_source']['immagini']['default']
                            title = hh['_source']['titolo']
                            creation_date = hh['_source']['data_creazione']
                            if 'sommario' in hh['_source']: 
                                desc = creation_date + '\n' + hh['_source']['sommario']
                            else:
                                desc = creation_date 

                            params= {'mode':'raisport_video', 'title': title, 'url': relinker_url, 'icon': icon, 
                                     'duration' : duration, 'aired': creation_date, 'desc': desc}
                            videos.append(params)

            if h['total'] > (page + pageSize):
                page += pageSize
                params = {'mode':'raisport_subitem', 'title': xbmc.getLocalizedString(33078), 'page': page}
                videos.append(params)
        
        return videos
    
    def getProgrammes(self, channelName, epgDate):
        channelTag = channelName.replace(" ", "")
        url = self.palinsestoUrl
        url = url.replace("[nomeCanale]", channelTag)
        url = url.replace("[dd-mm-yyyy]", epgDate)
        response = json.load(urllib2.urlopen(url))
        try:
          oRetVal = response[channelName][0]["palinsesto"][0]["programmi"]
        except:
          oRetVal = None
        return oRetVal
    
    def getProgrammesHtml(self, channelName, epgDate):
        channelTag = channelName.replace(" ", "-").lower()
        url = self.palinsestoUrlHtml
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
        data = urllib2.urlopen(url).read()

        s_name = re.findall("\"name\": \"(.*?)\",", data)
        for s in s_name:
            data = data.replace(s , s.replace("\""," "))
        response = json.loads(data)
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
 