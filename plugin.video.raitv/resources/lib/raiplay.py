# -*- coding: utf-8 -*-
import sys
import json
import re
import xbmc
import resources.lib.utils as utils

PY3 = sys.version_info.major >= 3

if PY3:
    import urllib.request as urllib2
    import html.parser as HTMLParser

else:
    import urllib2
    import HTMLParser


class RaiPlay:
    # Raiplay android app
    #UserAgent = "Dalvik/1.6.0 (Linux; U; Android 4.2.2; GT-I9105P Build/JDQ39)"
    #MediapolisUserAgent = "Android 4.2.2 (smart) / RaiPlay 2.1.3 / WiFi"
    
    UserAgent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36"
    MediapolisUserAgent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36"
    
    noThumbUrl = "http://www.rai.it/dl/components/img/imgPlaceholder.png"
    
    # From http://www.raiplay.it/mobile/prod/config/RaiPlay_Config.json
    baseUrl = "https://www.raiplay.it/"
    channelsUrl = "http://www.rai.it/dl/RaiPlay/2016/PublishingBlock-9a2ff311-fcf0-4539-8f8f-c4fee2a71d58.html?json"
    localizeUrl = "http://mediapolisgs.rai.it/relinker/relinkerServlet.htm?cont=201342"
    menuUrl = "http://www.rai.it/dl/RaiPlay/2016/menu/PublishingBlock-20b274b1-23ae-414f-b3bf-4bdc13b86af2.html?homejson"
    palinsestoUrl = "https://www.raiplay.it/palinsesto/app/old/[nomeCanale]/[dd-mm-yyyy].json"
    palinsestoUrlHtml = "https://www.raiplay.it/palinsesto/guidatv/lista/[idCanale]/[dd-mm-yyyy].html"
    onAirUrl = "https://www.raiplay.it/palinsesto/onAir.json" 
    AzTvShowPath = "/dl/RaiTV/RaiPlayMobile/Prod/Config/programmiAZ-elenco.json"
    
    # Rai Sport urls
    RaiSportMainUrl = 'https://www.rainews.it/archivio/sport'
    RaiSportArchivioUrl = RaiSportMainUrl
    RaiSportCategoriesUrl = "https://www.rainews.it/category/6dd7493b-f116-45de-af11-7d28a3f33dd2.json"
    RaiSportSearchUrl = "https://www.rainews.it/atomatic/news-search-service/api/v3/search"

    RaiPlayAddonHandle = None
    
    def __init__(self, addonHandle):
        opener = urllib2.build_opener()
        # Set User-Agent
        opener.addheaders = [('User-Agent', self.UserAgent)]
        urllib2.install_opener(opener)
        self.RaiPlayAddonHandle = addonHandle
        
    def getCountry(self):
        try:
            response = utils.checkStr(urllib2.urlopen(self.localizeUrl).read())
        except :
            response = "ERROR"
        return response
        
    def getChannels(self):
        response = json.loads(utils.checkStr(urllib2.urlopen(self.channelsUrl).read()))
        return response["dirette"]
    
    def getOnAir(self):
        response = json.loads(utils.checkStr(urllib2.urlopen(self.onAirUrl).read()))
        return response["on_air"]
    
    def getHomePage(self, defaultUrl):
        response = json.loads(utils.checkStr(urllib2.urlopen(self.baseUrl + defaultUrl).read()))
        return response["contents"]
      
    def getRaiSportLivePage(self):
        chList = []

        chList.append({'title':'RaiSport Web 1', 'url': 'https://mediapolis.rai.it/relinker/relinkerServlet.htm?cont=22590', 'icon':''})
        chList.append({'title':'RaiSport Web 2', 'url': 'https://mediapolis.rai.it/relinker/relinkerServlet.htm?cont=35259', 'icon':''})
        
        return chList
    
    def fillRaiSportKeys(self):
        # search for items in main menu
        dominio = "RaiNews|Category-60bbaf3f-99b8-4aac-8a6d-69a98e11bfc1"
        RaiSportKeys=[]
        
        try:        
            data = json.loads(utils.checkStr(urllib2.urlopen(self.RaiSportCategoriesUrl).read()))
        except :
            data = ''

        RaiSportKeys=[]
        
        for c in data.get('children',[]):
            
            categName = c.get("name","")
            categCode =  c.get("uniqueName","")
            categChildren = c.get("children", [])
            xbmc.log("Raisport: sto per aggiungere %s" % (categName + "|" + categCode) )
            if categName:
            
                sub_keys = []
                for c2 in categChildren:
                    subcategName = c2.get("name","")
                    subcategCode =  c2.get("uniqueName","")
                    if subcategName:
                        xbmc.log("Raisport: aggiunto %s" % (subcategName+"|"+subcategCode) )
                        sub_keys.append({'title': subcategName , "dominio": dominio, "key" : (subcategName+"|"+subcategCode)})

                xbmc.log("Raisport: aggiunto %s" % subcategName )
                RaiSportKeys.append({'title': categName , "dominio": dominio, "key": (categName + "|" + categCode), 'sub_keys' : sub_keys })
        
        #good_links.append({'title': self.RaiPlayAddonHandle.getLocalizedString(32015), 'url' : '/archivio.html?tematica=altri-sport'})
        
        # open any single page in list and grab search keys
        
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
            "mode":"archive",
            "filters":{
                "tematica":[key],
                "dominio": domain
            }
        }
        postData=json.dumps(payload)
        xbmc.log(postData)
        
        try:
            req = urllib2.Request(self.RaiSportSearchUrl, postData, header)
            response = urllib2.urlopen(req)
        except TypeError:
            req = urllib2.Request(self.RaiSportSearchUrl, postData.encode('utf-8'), header)
            response = urllib2.urlopen(req)
        
        if response.code != 200:
            return []
        
        data = utils.checkStr(response.read())
        xbmc.log("Raisport: -------- risultati della ricerca -------------------------------------------------------------------")
        xbmc.log(data)
        xbmc.log("Raisport: -------- fine risultati della ricerca---------------------------------------------------------------")

        j = json.loads(data)
        
        hits = j.get("hits",[])
        
        for h in hits:
            title = h.get("title","")
            dataType = h.get("data_type","")

            if dataType == "video":
                media = h.get('media',{})
                relinker_url = media.get('mediapolis',"")
                if 'durata' in media:
                    d= media['durata'].split(":")
                    duration = int(d[0])*3600 + int(d[1])*60 + int(d[2])
                else:
                    duration = 0                
                icon = self.getThumbnailUrl2(h)
                creation_date = h['create_date']
                if "summary" in h: 
                    desc = creation_date + '\n' + h['summary']
                else:
                     desc = creation_date 

                params= {'mode':'raisport_video', 'title': title, 'url': relinker_url, 'icon': icon, 
                                     'duration' : duration, 'aired': creation_date, 'desc': desc}
                videos.append(params)


        if j['total'] > (page + pageSize):
            page += pageSize
            params = {'mode':'raisport_subitem', 'title': xbmc.getLocalizedString(33078), 'page': page}
            videos.append(params)
        
        return videos
    
    def getProgrammes(self, channelName, epgDate):
        channelTag = channelName.replace(" ", "")
        url = self.palinsestoUrl
        url = url.replace("[nomeCanale]", channelTag)
        url = url.replace("[dd-mm-yyyy]", epgDate)
        response = json.loads(utils.checkStr(urllib2.urlopen(url).read()))
        try:
            key = channelName if channelName in response else ''
            oRetVal = response[key][0]["palinsesto"][0]["programmi"]
        except:
            oRetVal = None
        return oRetVal
    
    def getProgrammesHtml(self, channelName, epgDate):
        channelTag = channelName.replace(" ", "-").lower()
        url = self.palinsestoUrlHtml
        url = url.replace("[idCanale]", channelTag)
        url = url.replace("[dd-mm-yyyy]", epgDate)
        try:
            data = utils.checkStr(urllib2.urlopen(url).read())
        except :
            data = ''
        return data
        
    def getMainMenu(self):
        response = json.loads(utils.checkStr(urllib2.urlopen(self.menuUrl).read()))
        return response["menu"]

    # RaiPlay Genere Page
    # RaiPlay Tipologia Page
    def getCategory(self, pathId):
        url = self.getUrl(pathId)
        try:
            response = json.loads(utils.checkStr(urllib2.urlopen(url).read()))
            return response["contents"]
        except: 
            return []
  
    # Raiplay Tipologia Item
    def getProgrammeList(self, pathId):
        url = self.getUrl(pathId)
        try:
            response = json.loads(utils.checkStr(urllib2.urlopen(url).read()))
            return response["contents"]
        except:
            return []

    # Raiplay AZ List
    def getProgrammeListOld(self, pathId):
        url = self.getUrl(pathId)
        try:
            response = json.loads(utils.checkStr(urllib2.urlopen(url).read()))
            return response
        except:
            return []
      
    #  PLR programma Page
    def getProgramme(self, pathId):
        url = self.getUrl(pathId)
        try:
            response = json.loads(utils.checkStr(urllib2.urlopen(url).read()))
            return response
        except:
            return[]
        
    def getContentSet(self, url):
        url = self.getUrl(url)
        try:
            response = json.loads(utils.checkStr(urllib2.urlopen(url).read()))
            return response["items"]
        except:
            return []
    
    def getVideoMetadata(self, pathId):
        url = self.getUrl(pathId)
        if url.endswith(".html"):
            url = url.replace(".html",".json")
            
        try:
            response = json.loads(utils.checkStr(urllib2.urlopen(url).read()))
            return response["video"]
        except:
            return []
    
    def getIndexFromJSON(self, pathId):
        url = self.getUrl(pathId)
        try:
            response = json.loads(utils.checkStr(urllib2.urlopen(url).read()))
        
            index = []
            for i in response["contents"]:
              if len(response["contents"][i])>0:
                index.append(i)
        
            index.sort()
            return index
        except:
            return []
    
    def getUrl(self, pathId):
        url = pathId.replace(" ", "%20")
        
        if url.startswith("/raiplay/"):
            url = url.replace("/raiplay/","https://raiplay.it/")
        
        if url[0:2] == "//":
            url = "https:" + url
        elif url[0] == "/":
            url = self.baseUrl[:-1] + url
        
        # fix old format of url for json
        if url.endswith(".html?json"):
            url = url.replace(".html?json", ".json")
        elif url.endswith("/?json"):
            url = url.replace("/?json","/index.json")
        elif url.endswith("?json"):
            url = url.replace("?json",".json")
        
        return url
        
    def getThumbnailUrl(self, pathId):
        if pathId == "":
            url = self.noThumbUrl
        else:
            url = self.getUrl(pathId)
            url = url.replace("[RESOLUTION]", "256x-")
        return url
 
    def getThumbnailUrl2(self, item):
        if "images" in item:
            if "landscape" in item["images"]:
                url = item["images"]["landscape"]
                return self.getThumbnailUrl(url)
            elif "landscape43" in item["images"]:
                url = item["images"]["landscape43"]
                return self.getThumbnailUrl(url)
            elif "portrait" in item["images"]:
                url = item["images"]["portrait"]
                return self.getThumbnailUrl(url)
            elif "portrait43" in item["images"]:
                url = item["images"]["portrait43"]
                return self.getThumbnailUrl(url)
                
        return self.noThumbUrl
        
