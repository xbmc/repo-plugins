import json
import xml.etree.ElementTree as ET
from phate89lib import rutils, staticutils  # pylint: disable=import-error
try:
    from urllib.parse import urlencode, quote
except ImportError:
    from urllib import urlencode, quote


class Mediaset(rutils.RUtils):

    USERAGENT = "VideoMediaset Kodi Addon"

    def __init__(self):
        self.__UID = ''
        self.__UIDSignature = ''
        self.__signatureTimestamp = ''
        self.apigw = ''
        self.cts = ''
        self.__tracecid = ''
        self.__cwid = ''
        self.anonymousLogin()
        self.uxReferenceMapping = {
            'CWDOCUBIOSTORIE': 'documentariBioStoria',
            'CWDOCUINCHIESTE': 'documentariInchiesta',
            'CWDOCUMOSTRECENT': 'mostRecentDocumentariFep',
            'CWDOCUNATURANIMALI': 'documentariNatura',
            'CWDOCUSCIENZATECH': 'documentariScienza',
            'CWDOCUSPAZIO': 'documentariSpazio',
            'CWDOCUTOPVIEWED': 'stagioniDocumentari',
            'CWENABLERKIDS': 'stagioniKids',
            'CWFICTIONADVENTURE': 'stagioniFictionAvventura',
            'CWFICTIONBIOGRAPHICAL': 'stagioniFictionBiografico',
            'CWFICTIONCOMEDY': 'stagioniFictionCommedia',
            'CWFICTIONDRAMATIC': 'stagioniFictionDrammatico',
            'CWFICTIONPOLICE': 'stagioniFictionPoliziesco',
            'CWFICTIONSENTIMENTAL': 'stagioniFictionSentimentale',
            'CWFICTIONSITCOM': 'stagioniFictionSitCom',
            'CWFICTIONSOAP': 'mostRecentSoapOpera',
            'CWFILMACTION': 'filmAzioneThrillerAvventura',
            'CWFILMCLASSIC': 'filmClassici',
            'CWFILMCOMEDY': 'filmCommedia',
            'CWFILMDOCU': 'filmDocumentario',
            'CWFILMDRAMATIC': 'filmDrammatico',
            'CWFILMSENTIMENTAL': 'filmSentimentale',
            'CWFILMTOPVIEWED': 'filmPiuVisti24H',
            'CWHOMEBRANDS': 'personToContentHomepage',
            'CWHOMEFICTIONNOWELITE': 'stagioniFictionSerieTvSezione',
            'CWHOMEFICTIONNOWPOP': 'stagioniFictionSerieTvHomepage',
            'CWHOMEPROGTVNOW': 'stagioniProgrammiTv',
            'CWKIDSBOINGFORYOU': 'kidsBoing',
            'CWKIDSCARTOONITO': 'kidsCartoonito',
            'CWKIDSMEDIASETBRAND': 'kidsMediaset',
            'CWPROGTVDAY': 'stagioniDaytime',
            'CWPROGTVMAGAZINE': 'stagioniCucinaLifestyle',
            'CWPROGTVPRIME': 'stagioniPrimaSerata',
            'CWPROGTVSPORT': 'mostRecentSport',
            'CWPROGTVTALENT': 'stagioniReality',
            'CWPROGTVTALK': 'stagioniTalk',
            'CWPROGTVTG': 'mostRecentTg',
            'CWPROGTVTOPVIEWED': 'programmiTvClip24H',
            'CWPROGTVVARIETY': 'stagioniVarieta',
            'CWSEARCHBRAND': 'searchStagioni',
            'CWSEARCHCLIP': 'searchClip',
            'CWSEARCHEPISODE': 'searchEpisodi',
            'CWSEARCHMOVIE': 'searchMovie',
            'CWSIMILARDOCUMENTARI': 'similarDocumentari',
            'CWSIMILARFICTION': 'similarSerieTvFiction',
            'CWSIMILARFILM': 'similarCinema',
            'CWSIMILARINFORMAZIONE': 'similarInformazione',
            'CWSIMILARINTRATTENIMENTO': 'similarIntrattenimento',
            'CWSIMILARKIDS': 'similarCartoni',
            'CWSIMILARSERIETV': 'similarSerieTvFiction',
            'CWSIMILARSPORT': 'similarSport',
            'CWSIMILARTG': 'similarTg',
            'CWTOPSEARCHBRAND': 'defaultSearchStagioni',
            'CWTOPSEARCHCLIP': 'defaultSearchVideo',
            'CWTOPVIEWEDDAY': 'piuVisti24H',
            'documentariBioStoria': 'documentariBioStoria',
            'documentariInchiesta': 'documentariInchiesta',
            'documentariNatura': 'documentariNatura',
            'documentariScienza': 'documentariScienza',
            'documentariSpazio': 'documentariSpazio',
            'filmAzioneThrillerAvventura': 'filmAzioneThrillerAvventura',
            'filmClassici': 'filmClassici',
            'filmCommedia': 'filmCommedia',
            'filmDocumentario': 'filmDocumentario',
            'filmDrammatico': 'filmDrammatico',
            'filmPiuVisti24H': 'filmPiuVisti24H',
            'filmSentimentale': 'filmSentimentale',
            'kidsBoing': 'kidsBoing',
            'kidsCartoonito': 'kidsCartoonito',
            'kidsMediaset': 'kidsMediaset',
            'mostRecentDocumentariFep': 'mostRecentDocumentariFep',
            'mostRecentSoapOpera': 'mostRecentSoapOpera',
            'mostRecentSport': 'mostRecentSport',
            'mostRecentTg': 'mostRecentTg',
            'personToContentFilm': 'personToContentFilm',
            'personToContentHomepage': 'personToContentHomepage',
            'piuVisti24H': 'piuVisti24H',
            'programmiTvClip24H': 'programmiTvClip24H',
            'similarCartoni': 'similarCartoni',
            'similarCinema': 'similarCinema',
            'similarDocumentari': 'similarDocumentari',
            'similarInformazione': 'similarInformazione',
            'similarIntrattenimento': 'similarIntrattenimento',
            'similarSerieTvFiction': 'similarSerieTvFiction',
            'similarSport': 'similarSport',
            'similarTg': 'similarTg',
            'stagioniCucinaLifestyle': 'stagioniCucinaLifestyle',
            'stagioniDaytime': 'stagioniDaytime',
            'stagioniDocumentari': 'stagioniDocumentari',
            'stagioniFictionAvventura': 'stagioniFictionAvventura',
            'stagioniFictionBiografico': 'stagioniFictionBiografico',
            'stagioniFictionCommedia': 'stagioniFictionCommedia',
            'stagioniFictionDrammatico': 'stagioniFictionDrammatico',
            'stagioniFictionPoliziesco': 'stagioniFictionPoliziesco',
            'stagioniFictionSentimentale': 'stagioniFictionSentimentale',
            'stagioniFictionSerieTvHomepage': 'stagioniFictionSerieTvHomepage',
            'stagioniFictionSerieTvSezione': 'stagioniFictionSerieTvSezione',
            'stagioniFictionSitCom': 'stagioniFictionSitCom',
            'stagioniKids': 'stagioniKids',
            'stagioniPrimaSerata': 'stagioniPrimaSerata',
            'stagioniProgrammiTv': 'stagioniProgrammiTv',
            'stagioniReality': 'stagioniReality',
            'stagioniTalk': 'stagioniTalk',
            'stagioniVarieta': 'stagioniVarieta'
        }
        rutils.RUtils.__init__(self)

    def __getAPISession(self):
        res = self.createRequest(
            "https://api.one.accedo.tv/session?appKey=59ad346f1de1c4000dfd09c5&uuid=sdd")
        self.setHeader('x-session', res.json()['sessionKey'])

    def login(self, user, password):
        self.log('Trying to login with user data', 4)
        data = {
            "loginID": user,
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
        res = self.createRequest(
            "https://login.mediaset.it/accounts.login", post=data)
        s = res.text.strip().replace('gigya.callback(', '', 1)
        if s[-1:] == ';':
            s = s[:-1]
        if s[-1:] == ')':
            s = s[:-1]
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
                    "appName": "web/mediasetplay-web/bd16667"}
            url = "https://api-ott-prod-fe.mediaset.net/PROD/play/idm/account/login/v1.0"
        else:
            data = {"cid": "dc4e7d82-89a5-4a96-acac-d3c7f2ca6d67",
                    "platform": "pc",
                    "appName": "web/mediasetplay-web/576ea90"}
            url = "https://api-ott-prod-fe.mediaset.net/PROD/play/idm/anonymous/login/v1.0"
        res = self.SESSION.post(url, json=data, verify=True)
        jsn = res.json()
        if not jsn['isOk']:
            return False

        self.apigw = res.headers['t-apigw']
        self.cts = res.headers['t-cts']
        self.setHeader('t-apigw', self.apigw)
        self.setHeader('t-cts', self.cts)
        self.__tracecid = jsn['response']['traceCid']
        self.__cwid = jsn['response']['cwId']
        self.log('Retrieved keys successfully', 4)
        return True

    def __getEntriesFromUrl(self, url, args=None):
        data = self.getJson(self.__create_url(url, args))
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

    def __getsectionsFromEntryID(self, eid):
        self.__getAPISession()
        jsn = self.getJson(
            "https://api.one.accedo.tv/content/entry/{eid}?locale=it".format(eid=eid))
        if jsn and "components" in jsn:
            eid = quote(",".join(jsn["components"]))
            jsn = self.getJson(
                "https://api.one.accedo.tv/content/entries?id={eid}&locale=it".format(eid=eid))
            if jsn and 'entries' in jsn:
                return jsn['entries']
        return False

    def __createMediasetUrl(self, base, pageels=None, page=None, args=None, passkeys=True):
        if args is None:
            args = {}
        if pageels and 'hitsPerPage' not in args:
            args['hitsPerPage'] = pageels
        if page and 'page' not in args:
            args['page'] = str(page)
        if 'page' not in args and 'hitsPerPage' in args:
            args['page'] = '1'
        if passkeys and self.__tracecid:
            args['traceCid'] = self.__tracecid
        if passkeys and self.__cwid:
            args['cwId'] = self.__cwid
        return self.__create_url(base, args)

    def __create_url(self, url, args=None):
        if args is None:
            return url
        if url.endswith('?'):
            return url + urlencode(args)
        return url + '?' + urlencode(args)

    def __createAZUrl(self, categories=None, query=None, inonda=None, pageels=100, page=None):
        args = {"query": query if query else "*:*"}

        if categories is not None:
            args["categories"] = ",".join(categories)
        if inonda is not None:
            args["inOnda"] = str(inonda).lower()
        return self.__createMediasetUrl(
            "https://api-ott-prod-fe.mediaset.net/PROD/play/rec/azlisting/v1.0?",
            pageels, page, args)

    def OttieniTutto(self, inonda=None, pageels=100, page=None):
        self.log('Trying to get the full program list', 4)
        url = self.__createAZUrl(inonda=inonda, pageels=pageels, page=page)
        return self.__getElsFromUrl(url)

    def OttieniTuttoLettera(self, lettera, inonda=None, pageels=100, page=None):
        self.log('Trying to get the full program list with letter {}'.format(lettera), 4)
        if lettera == '#':
            query = '-(TitleFullSearch:{A TO *})'
        else:
            query = 'TitleFullSearch:' + lettera + '*'
        url = self.__createAZUrl(query=query, inonda=inonda, pageels=pageels, page=page)
        return self.__getElsFromUrl(url)

    def OttieniTuttiProgrammi(self, inonda=None, pageels=100, page=None):
        self.log('Trying to get the tv program list', 4)
        url = self.__createAZUrl(["Programmi Tv"], inonda=inonda, pageels=pageels, page=page)
        return self.__getElsFromUrl(url)

    def OttieniTutteFiction(self, inonda=None, pageels=100, page=None):
        self.log('Trying to get the fiction list', 4)
        url = self.__createAZUrl(["Fiction"], inonda=inonda, pageels=pageels, page=page)
        return self.__getElsFromUrl(url)

    def OttieniCategorieProgrammi(self):
        self.log('Trying to get the programs sections list', 4)
        return self.__getsectionsFromEntryID("5acfc8011de1c4000b6ec953")

    def OttieniGeneriFiction(self):
        self.log('Trying to get the fiction sections list', 4)
        return self.__getsectionsFromEntryID("5acfcb3c23eec6000d64a6a4")

    def OttieniFilm(self, inonda=None, pageels=100, page=None):
        self.log('Trying to get the movie list', 4)
        url = self.__createAZUrl(["Cinema"], inonda=inonda, pageels=pageels, page=page)
        return self.__getElsFromUrl(url)

    def OttieniGeneriFilm(self):
        self.log('Trying to get the movie sections list', 4)
        return self.__getsectionsFromEntryID("5acfcbc423eec6000d64a6bb")

    def OttieniKids(self, inonda=None, pageels=100, page=None):
        self.log('Trying to get the kids list', 4)
        url = self.__createAZUrl(["Kids"], inonda=inonda, pageels=pageels, page=page)
        return self.__getElsFromUrl(url)

    def OttieniGeneriKids(self):
        self.log('Trying to get the kids sections list', 4)
        return self.__getsectionsFromEntryID("5acfcb8323eec6000d64a6b3")

    def OttieniDocumentari(self, inonda=None, pageels=100, page=None):
        self.log('Trying to get the movie list', 4)
        url = self.__createAZUrl(["Documentari"], inonda=inonda, pageels=pageels, page=page)
        return self.__getElsFromUrl(url)

    def OttieniGeneriDocumentari(self):
        self.log('Trying to get the movie sections list', 4)
        return self.__getsectionsFromEntryID("5bfd17c423eec6001aec49f9")

    def OttieniProgrammiGenere(self, gid, pageels=100, page=None):
        self.log('Trying to get the programs from section id ' + gid, 4)
        url = self.__createMediasetUrl(
            "https://api-ott-prod-fe.mediaset.net/PROD/play/rec2/cataloguelisting/v1.0",
            pageels=pageels, page=page, args={'platform': 'pc', 'uxReference': self.uxReferenceMapping[gid]})
        return self.__getElsFromUrl(url)

    def OttieniStagioni(self, seriesId, sort=None, erange=None):
        self.log('Trying to get the seasons from series id {}'.format(seriesId), 4)
        url = 'https://feed.entertainment.tv.theplatform.eu/f/PR1GhC/mediaset-prod-tv-seasons/feed'
        args = {'bySeriesId': seriesId}
        if sort:
            args['sort'] = sort
        if erange:
            args['range'] = erange
        return self.__getEntriesFromUrl(url, args)

    def OttieniSezioniProgramma(self, brandId, sort=None, erange=None):
        self.log('Trying to get the sections from brand id {}'.format(brandId), 4)
        url = 'https://feed.entertainment.tv.theplatform.eu/f/PR1GhC/mediaset-prod-all-brands?'
        args = {'byCustomValue': '{{brandId}}{{{brandId}}}'.format(brandId=brandId)}
        if sort:
            args['sort'] = sort
        if erange:
            args['range'] = erange
        return self.__getEntriesFromUrl(url, args)

    def OttieniVideoSezione(self, subBrandId, sort=None, erange=None):
        self.log('Trying to get the videos from section {}'.format(subBrandId), 4)
        url = 'https://feed.entertainment.tv.theplatform.eu/f/PR1GhC/mediaset-prod-all-programs'
        args = {'byCustomValue': '{{subBrandId}}{{{subBrandId}}}'.format(subBrandId=subBrandId)}
        if sort:
            args['sort'] = sort
        if erange:
            args['range'] = erange
        return self.__getEntriesFromUrl(url, args)

    def OttieniCanaliLive(self, sort=None, erange=None):
        self.log('Trying to get the live channels list', 4)
        url = ('https://feed.entertainment.tv.theplatform.eu/f/PR1GhC/mediaset-prod-all-stations?')
        args = {}
        if sort:
            args['sort'] = sort
        if erange:
            args['range'] = erange
        return self.__getEntriesFromUrl(url, args)

    def Cerca(self, query, section=None, pageels=100, page=None):
        args = {'query': query, 'platform': 'pc'}
        if section:
            args['uxReference'] = self.uxReferenceMapping[section]
        url = self.__createMediasetUrl(
            'https://api-ott-prod-fe.mediaset.net/PROD/play/rec2/search/v1.0', pageels=pageels, page=page, args=args)
        return self.__getElsFromUrl(url)

    def OttieniGuidaTV(self, chid, start, finish):
        self.log(('Trying to get the tv guide from {} channel '
                  'starting {} finishing {}').format(chid, str(start), str(finish)), 4)
        args = {'byCallSign': chid, 'byListingTime': '{s}~{f}'.format(s=str(start), f=str(finish))}
        url = self.__createMediasetUrl(
            "https://api-ott-prod-fe.mediaset.net/PROD/play/alive/allListingFeedEpg/v1.0?",
            pageels=None, page=None, args=args)
        res = self.__getElsFromUrl(url)
        if res is not None:
            if res and res[0]:
                return res[0][0]
            return {}
        return res

    def OttieniProgrammiLive(self, sort=None):
        self.log('Trying to get the live programs', 4)
        now = staticutils.get_timestamp()
        args = {'byListingTime': '{s}~{f}'.format(s=str(now - 1001), f=str(now))}
        if sort:
            args['sort'] = sort
        url = self.__createMediasetUrl(
            "https://feed.entertainment.tv.theplatform.eu/f/PR1GhC/mediaset-prod-all-listings?",
            pageels=None, page=None, args=args, passkeys=False)
        return self.__getEntriesFromUrl(url)

    def OttieniLiveStream(self, guid):
        self.log('Trying to get live and rewind channel program of id {}'.format(guid), 4)
        url = 'https://static3.mediasetplay.mediaset.it/apigw/nownext/{}.json'.format(guid)
        return self.__getElsFromUrl(url)

    def OttieniInfoDaGuid(self, guid):
        self.log('Trying to get info from guid ' + guid, 4)
        url = ('https://feed.entertainment.tv.theplatform.eu/f/PR1GhC/mediaset-prod-all-programs/'
               'guid/-/{guid}').format(guid=guid)
        data = self.getJson(url)
        if data and 'isException' not in data:
            return data
        return False

    def OttieniDatiVideo(self, pid, live=False):
        self.log('Trying to get video data from pid ' + pid, 4)
        u = 'https://link.theplatform.eu/s/PR1GhC/'
        if not live:
            u += 'media/'
        u += pid + ('?auto=true&balance=true&format=SMIL&formats=MPEG-DASH,MPEG4,M3U&tracking=true'
                    '&assetTypes=HD,browser,widevine,geoIT|geoNo:HD,browser,geoIT|geoNo:HD,'
                    'geoIT|geoNo:SD,''browser,widevine,geoIT|geoNo:SD,browser,geoIT|geoNo:SD,'
                    'geoIT|geoNo')
        text = self.getText(u)
        res = {'url': '', 'pid': '', 'type': '', 'security': False}
        root = ET.fromstring(text)
        for vid in root.findall('.//{http://www.w3.org/2005/SMIL21/Language}switch'):
            ref = vid.find('./{http://www.w3.org/2005/SMIL21/Language}ref')
            res['url'] = ref.attrib['src']
            res['type'] = ref.attrib['type']
            if 'security' in ref.attrib and ref.attrib['security'] == 'commonEncryption':
                res['security'] = True
            par = ref.find(
                './{http://www.w3.org/2005/SMIL21/Language}param[@name="trackingData"]')
            if par is not None:
                for item in par.attrib['value'].split('|'):
                    [attr, value] = item.split('=', 1)
                    if attr == 'pid':
                        res['pid'] = value
                        break
            break
        return res

    def OttieniWidevineAuthUrl(self, uid):
        return (
            'https://widevine.entitlement.theplatform.eu/wv/web/ModularDrm/getRawWidevineLicense?'
            'releasePid={pid}&account=http://access.auth.theplatform.com/data/Account/'
            '2702976343&schema=1.0&token={cts}').format(pid=uid, cts=self.cts)
