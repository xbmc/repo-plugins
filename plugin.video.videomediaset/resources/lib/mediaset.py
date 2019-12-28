from phate89lib import rutils, staticutils
import json
import re
import math
try:
    from urllib.parse import urlencode, quote
except ImportError:
    from urllib import urlencode, quote
import xml.etree.ElementTree as ET

class Mediaset(rutils.RUtils):

    USERAGENT="VideoMediaset Kodi Addon"
    
    def __init__(self):
        self.anonymousLogin()
        super(rutils.RUtils, self).__init__()

    def __getAPISession(self):
        res = self.SESSION.get("https://api.one.accedo.tv/session?appKey=59ad346f1de1c4000dfd09c5&uuid=sdd",verify=False)
        self.setHeader('x-session',res.json()['sessionKey'])
        
    def login(self, user,password):
        self.log('Trying to login with user data', 4)
        data = {"loginID": user,
                "password": password,
                "sessionExpiration": "31536000",
                "targetEnv": "jssdk",
                "include": "profile,data,emails,subscriptions,preferences,",
                "includeUserInfo": "true",
                "loginMode": "standard",
                "lang": "it",
                "APIKey": "3_NhZq9YZgkgeKfN08uFjs3NYGo2Txv4QQTULh0he2w337E-o0DPXzEp4aVnWIR4jg",
                "cid": "mediaset-web-mediaset.it programmi-mediaset Default",
                "source": "showScreenSet",
                "sdk": "js_latest",
                "authMode": "cookie",
                "pageURL": "https://www.mediasetplay.mediaset.it",
                "format": "jsonp",
                "callback": "gigya.callback",
                "utf8": "&#x2713;"}
        res = self.createRequest("https://login.mediaset.it/accounts.login",post=data)
        s = res.text.strip().replace('gigya.callback(','',1)
        if s[-1:] ==';':
            s= s[:-1]
        if s[-1:] ==')':
            s= s[:-1]
        jsn = json.loads(s)
        if jsn['errorCode'] != 0:
            self.log('Login with user data failed', 4)
            return False
        self.__UID = jsn['UID']
        self.__UIDSignature = jsn['UIDSignature']
        self.__signatureTimestamp = jsn['signatureTimestamp']
        return self.__getAPIKeys(True)

    def anonymousLogin(self):
        return self.__getAPIKeys()

    def __getAPIKeys(self, login=False):
        if login:
            data = {"platform": "pc",
                    "UID": self.__UID,
                    "UIDSignature": self.__UIDSignature,
                    "signatureTimestamp": self.__signatureTimestamp,
                    "appName": "web/mediasetplay-web/bd16667" }
            url = "https://api-ott-prod-fe.mediaset.net/PROD/play/idm/account/login/v1.0"
        else:
            data = {"cid": "dc4e7d82-89a5-4a96-acac-d3c7f2ca6d67",
                    "platform": "pc",
                    "appName": "web/mediasetplay-web/576ea90" }
            url = "https://api-ott-prod-fe.mediaset.net/PROD/play/idm/anonymous/login/v1.0"
        res = self.SESSION.post(url,json=data,verify=False)
        jsn = res.json()
        if not jsn['isOk']:
            return False
        
        self.apigw = res.headers['t-apigw']
        self.cts = res.headers['t-cts']
        self.setHeader('t-apigw',self.apigw)
        self.setHeader('t-cts',self.cts)
        self.__tracecid=jsn['response']['traceCid']
        self.__cwid=jsn['response']['cwId']
        self.log('Retrieved keys successfully', 4)
        return True
        
    def __getEntriesFromUrl(self,url,format=False):
        data = self.getJson(url)
        if data and 'entries' in data:
            return data['entries']
        return data
    
    def __getElsFromUrl(self, url):
        res = None
        hasMore = False
        data = self.getJson(url)
        if data and 'isOk' in data and data['isOk']: 
            if 'response' in data:
                if 'hasMore' in data['response']:
                    hasMore = data['response']['hasMore']
                if 'entries' in data['response']:
                    res = data['response']['entries']
                else:
                    res = data['response']
            elif 'entries' in data:
                res = data['entries']
        return res, hasMore

    # def __getpagesFromUrl(self,url,page=0):
    #     url+= "&page={page}"
    #     if (page!=0):
    #         return self.__getEntriesFromUrl(url.format(page=page))
    #     els=[]
    #     while (True):
    #         page +=1
    #         data = self.__getResponseFromUrl(url.format(page=page))
    #         els.extend(data['entries'])
    #         if data['hasMore'] == False:
    #             return els
    
    def __getsectionsFromEntryID(self,id):
        self.__getAPISession()
        jsn = self.getJson("https://api.one.accedo.tv/content/entry/{id}?locale=it".format(id=id))
        if jsn and "components" in jsn:
            id = quote(",".join(jsn["components"]))
            jsn = self.getJson("https://api.one.accedo.tv/content/entries?id={id}&locale=it".format(id=id))
            if jsn and 'entries' in jsn:
                return jsn['entries']
        return False
    
    def __createMediasetUrl(self, base, pageels=None, page=None, args={}, passkeys=True):
        if pageels and not 'hitsPerPage' in args:
            args['hitsPerPage']=pageels
        if page and not 'page' in args:
            args['page'] = str(page)
        if passkeys and self.__tracecid:
            args['traceCid']=self.__tracecid
        if passkeys and self.__cwid:
            args['cwId']=self.__cwid
        return base + urlencode(args)


    def __createAZUrl(self,categories=[],query=None,inonda=None,pageels=100, page=None):
        args = {"query": query if query else "*:*" }

        if categories:
            args["categories"] = ",".join(categories)
        if inonda != None:
            args["inOnda"] = str(inonda).lower()
        return self.__createMediasetUrl("https://api-ott-prod-fe.mediaset.net/PROD/play/rec/azlisting/v1.0?",
                                        pageels, page, args)
    
    def OttieniTutto(self,inonda=None,pageels=100, page=None):
        self.log('Trying to get the full program list', 4)
        url = self.__createAZUrl(inonda=inonda, pageels=pageels, page = page)
        return self.__getElsFromUrl(url)
        
    def OttieniTuttoLettera(self,lettera, inonda=None,pageels=100, page=None):
        self.log('Trying to get the full program list with letter ' + lettera, 4)
        if lettera=='#':
            query='-(TitleFullSearch:{A TO *})'
        else:
            query='TitleFullSearch:' + lettera + '*'
        url = self.__createAZUrl(query=query, inonda=inonda, pageels=pageels, page = page)
        return self.__getElsFromUrl(url)

    def OttieniTuttiProgrammi(self,inonda=None,pageels=100, page=None):
        self.log('Trying to get the tv program list', 4)
        url = self.__createAZUrl(["Programmi Tv"], inonda=inonda, pageels=pageels, page = page)
        return self.__getElsFromUrl(url)
        
    def OttieniTutteFiction(self,inonda=None,pageels=100, page=None):
        self.log('Trying to get the fiction list', 4)
        url = self.__createAZUrl(["Fiction"], inonda=inonda,pageels=pageels,page=page)
        return self.__getElsFromUrl(url)
        
    def OttieniGeneriFiction(self):
        self.log('Trying to get the fiction sections list', 4)
        return self.__getsectionsFromEntryID("5acfcb3c23eec6000d64a6a4")
        
    def OttieniFilm(self,inonda=None,pageels=100, page=None):
        self.log('Trying to get the movie list', 4)
        url = self.__createAZUrl(["Cinema"], inonda=inonda,pageels=pageels,page=page)
        return self.__getElsFromUrl(url)
        
    def OttieniGeneriFilm(self):
        self.log('Trying to get the movie sections list', 4)
        return self.__getsectionsFromEntryID("5acfcbc423eec6000d64a6bb")
    
    def OttieniKids(self,inonda=None,pageels=100,page=None):
        self.log('Trying to get the kids list', 4)
        url = self.__createAZUrl(["Kids"], inonda=inonda, pageels=pageels,page=page)
        return self.__getElsFromUrl(url)
        
    def OttieniGeneriKids(self):
        self.log('Trying to get the kids sections list', 4)
        return self.__getsectionsFromEntryID("5acfcb8323eec6000d64a6b3")
    
    def OttieniDocumentari(self,inonda=None,pageels=100, page=None):
        self.log('Trying to get the movie list', 4)
        url = self.__createAZUrl(["Documentari"], inonda=inonda,pageels=pageels,page=page)
        return self.__getElsFromUrl(url)
        
    def OttieniGeneriDocumentari(self):
        self.log('Trying to get the movie sections list', 4)
        return self.__getsectionsFromEntryID("5bfd17c423eec6001aec49f9")
    
    def OttieniProgrammiGenere(self,id, pageels=100, page=None):
        self.log('Trying to get the programs from section id ' + id, 4)
        url = self.__createMediasetUrl("https://api-ott-prod-fe.mediaset.net/PROD/play/rec/cataloguelisting/v1.0?", pageels=pageels, page=page, args={'platform':'pc','uxReference':id})
        return self.__getElsFromUrl(url)

    def OttieniStagioni(self,seriesId):
        self.log('Trying to get the seasons from series id ' + seriesId, 4)
        url = 'https://feed.entertainment.tv.theplatform.eu/f/PR1GhC/mediaset-prod-tv-seasons/feed?bySeriesId' + seriesId
        return self.__getEntriesFromUrl(url)

    def OttieniSezioniProgramma(self,brandId):
        self.log('Trying to get the sections from brand id ' + brandId, 4)
        url = 'https://feed.entertainment.tv.theplatform.eu/f/PR1GhC/mediaset-prod-all-brands?byCustomValue={brandId}{' + brandId + '}' #&sort=mediasetprogram$order
        return self.__getEntriesFromUrl(url)
        
    def OttieniVideoSezione(self,subBrandId):
        self.log('Trying to get the videos from section ' + subBrandId, 4)
        url = 'https://feed.entertainment.tv.theplatform.eu/f/PR1GhC/mediaset-prod-all-programs?byCustomValue={subBrandId}{' + subBrandId + '}' #&sort=mediasetprogram$publishInfo_lastPublished|desc
        return self.__getEntriesFromUrl(url)
        
    def OttieniCanaliLive(self):
        self.log('Trying to get the live channels list', 4)
        url = 'https://feed.entertainment.tv.theplatform.eu/f/PR1GhC/mediaset-prod-all-stations?sort=ShortTitle' #sort=ShortTitle
        return self.__getEntriesFromUrl(url)

    def Cerca(self, query, section=None, pageels=100, page=None):
        args={'query': query, 'platform':'pc' }
        if section:
            args['uxReference']= section
        url = self.__createMediasetUrl('https://api-ott-prod-fe.mediaset.net/PROD/play/rec/search/v1.0?', 
                                        pageels=pageels, page=page,args=args)
        return self.__getElsFromUrl(url)

    def OttieniGuidaTV(self,chid, start, finish):
        self.log('Trying to get the tv guide from ' + chid + ' channel starting ' + str(start) + 'finishing ' + str(finish), 4)
        args = {'byCallSign':chid,'byListingTime': str(start) + '~' + str(finish)}
        url = self.__createMediasetUrl("https://api-ott-prod-fe.mediaset.net/PROD/play/alive/allListingFeedEpg/v1.0?", 
                                        pageels=None, page=None, args=args)
        res = self.__getElsFromUrl(url)
        if res:
            if len(res)>0 and res[0] and len(res[0])>0:
                return res[0][0]
            return {}
        else:
            return res

    def OttieniProgrammiLive(self):
        self.log('Trying to get the live programs', 4)
        now = staticutils.get_timestamp()
        args = {'byListingTime': str(now-1001) + '~' + str(now), 'sort':'title'}
        url = self.__createMediasetUrl("https://feed.entertainment.tv.theplatform.eu/f/PR1GhC/mediaset-prod-all-listings?", 
                                        pageels=None, page=None, args=args, passkeys=False)
        return self.__getEntriesFromUrl(url)

    def OttieniLiveStream(self,guid):
        self.log('Trying to get live and rewind channel program of id ' + guid, 4)
        url = 'https://static3.mediasetplay.mediaset.it/apigw/nownext/' + guid + '.json'
        return self.__getElsFromUrl(url)
        
    def OttieniInfoDaGuid(self,guid):
        self.log('Trying to get info from guid ' + guid, 4)
        url = 'https://feed.entertainment.tv.theplatform.eu/f/PR1GhC/mediaset-prod-all-programs/guid/-/' + guid
        data = self.getJson(url)
        if data and not 'isException' in data:
            return data
        else:
            return False

    def OttieniDatiVideo(self,pid, live=False):
        self.log('Trying to get video data from pid ' + pid, 4)
        url = 'https://link.theplatform.eu/s/PR1GhC/'
        if not live:
            url +='media/'
        url += pid + '?assetTypes=HD,browser,widevine:HD,browser:SD,browser,widevine:SD,browser:SD&auto=true&balance=true&format=smil&formats=MPEG-DASH,MPEG4,M3U&tracking=true'
        text = self.getText(url)
        res = { 'url': '', 'pid': '', 'type':'', 'security': False}
        root = ET.fromstring(text)
        for vid in root.findall('.//{http://www.w3.org/2005/SMIL21/Language}switch'):
            ref = vid.find('./{http://www.w3.org/2005/SMIL21/Language}ref')
            res['url'] = ref.attrib['src']
            res['type'] = ref.attrib['type']
            if 'security' in ref.attrib and ref.attrib['security'] =='commonEncryption':
                res['security'] = True
            par = ref.find('./{http://www.w3.org/2005/SMIL21/Language}param[@name="trackingData"]')
            if par is not None:
                for item in par.attrib['value'].split('|'):
                    [attr, value] = item.split('=',1)
                    if attr=='pid':
                        res['pid'] = value
                        break
            break
        return res