import requests, uuid, urllib.request, urllib.parse, urllib.error, json
from xml.dom.minidom import *
import xml.etree.ElementTree as ET

from .utils import saveCookies, loadCookies, saveAuthorization, log

class CBC:

    def __init__(self):
        self.ENV_JS = 'https://watch.cbc.ca/public/js/env.js'
        self.API_KEY = '3f4beddd-2061-49b0-ae80-6f1f2ed65b37'
        self.RADIUS_LOGIN_FMT = 'https://api.loginradius.com/identity/v2/auth/login?{}'
        self.RADIUS_JWT_FMT = 'https://cloud-api.loginradius.com/sso/jwt/api/token?{}'
        self.IDENTITIES_URL='https://api-cbc.cloud.clearleap.com/cloffice/client/identities'
        self.DEVICE_XML_FMT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<device>
  <type>web</type>
</device>"""
        self.LOGIN_XML_FMT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<login>
  <token>{}</token>
  <device>
    <deviceId>{}</deviceId>
    <type>web</type>
  </device>
</login>"""
        # Create requests session object
        self.session = requests.Session()
        session_cookies = loadCookies()
        if not session_cookies == None:
            self.session.cookies = session_cookies

    def authorize(self, username = None, password = None, callback = None):
        full_auth = not username == None and not password == None
        r = self.session.get(self.IDENTITIES_URL)
        if not callback == None:
            callback(20 if full_auth else 50)
        if not r.status_code == 200:
            log('ERROR: {} returns status of {}'.format(self.IDENTITIES_URL, r.status_code), True)
            return None

        dom = parseString(r.content)
        reg_url = dom.getElementsByTagName('registerDeviceUrl')[0].firstChild.nodeValue
        login_url = dom.getElementsByTagName('loginUrl')[0].firstChild.nodeValue

        auth = self.registerDevice(reg_url)
        if not callback == None:
            callback(40 if full_auth else 100)
        if auth == None:
            log('Device registration failed', True)
            return False


        if full_auth:
            token = self.radiusLogin(username, password)
            if not callback == None:
                callback(60)
            if token == None:
                log('Radius Login failed', True)
                return False

            jwt = self.radiusJWT(token)
            if not callback == None:
                callback(80)
            if jwt == None:
                log('Radius JWT retrieval failed', True)
                return False

            token = self.login(login_url, auth['devid'], jwt)
            if not callback == None:
                callback(100)
            if token == None:
                log('Final login failed', True)
                return False
            auth['token'] = token

        saveAuthorization(auth)
        saveCookies(self.session.cookies)

        return True


    def registerDevice(self, url):
        r = self.session.post(url, data=self.DEVICE_XML_FMT)
        if not r.status_code == 200:
            log('ERROR: {} returns status of {}'.format(url, r.status_code), True)
            return None
        saveCookies(self.session.cookies)
        # Parse the authorization response
        dom = parseString(r.content)
        status = dom.getElementsByTagName('status')[0].firstChild.nodeValue
        if status != "Success":
            log('Error: Unable to authorize device', True)
            return None
        auth = {
            'devid': dom.getElementsByTagName('deviceId')[0].firstChild.nodeValue,
            'token': dom.getElementsByTagName('deviceToken')[0].firstChild.nodeValue
        }

        return auth


    def radiusLogin(self, username, password):
        query = urllib.parse.urlencode({'apikey': self.API_KEY})

        data = {
            'email': username,
            'password': password
        }
        url = self.RADIUS_LOGIN_FMT.format(query)
        r = self.session.post(url, json = data)
        if not r.status_code == 200:
            log('{} returns status {}'.format(r.url, r.status_code))
            return None

        token = json.loads(r.content)['access_token']

        return token


    def radiusJWT(self, token):
        query = urllib.parse.urlencode({
            'access_token': token,
            'apikey': self.API_KEY,
            'jwtapp': 'jwt'
        })
        url = self.RADIUS_JWT_FMT.format(query)
        r = self.session.get(url)
        if not r.status_code == 200:
            log('{} returns status {}'.format(r.url, r.status_code))
            return None
        return json.loads(r.content)['signature']


    def login(self, url, devid, jwt):
        data = self.LOGIN_XML_FMT.format(jwt, devid)
        headers = {'Content-type': 'content_type_value'}
        r = self.session.post(url, data = data, headers = headers)
        if not r.status_code == 200:
            log('{} returns status {}'.format(r.url, r.status_code))
            return None

        dom = parseString(r.content)
        res = dom.getElementsByTagName('result')[0]
        token = res.getElementsByTagName('token')[0].firstChild.nodeValue

        return token


    def getImage(self, item):
        # ignore 'cbc$liveImage' - the pix don't make sense after the first load
        if 'defaultThumbnailUrl' in item:
            return item['defaultThumbnailUrl']
        elif 'cbc$staticImage' in item:
            return item['cbc$staticImage']
        elif 'cbc$featureImage' in item:
            return item['cbc$featureImage']
        return None


    def getLabels(self, item):
        labels = {
            'studio': 'Canadian Broadcasting Corporation',
            'country': 'Canada'
        }
        if 'cbc$callSign' in item:
            labels['title'] = '{} {}'.format(item['cbc$callSign'], item['title'])
        else:
            labels['title'] = item['title'].encode('utf-8')

        if 'cbc$show' in item:
            labels['tvshowtitle'] = item['cbc$show']
        elif 'clearleap:series' in item:
            labels['tvshowtitle'] = item['clearleap:series']

        if 'description' in item:
            labels['plot'] = item['description'].encode('utf-8')
            labels['plotoutline'] = item['description'].encode('utf-8')

        if 'cbc$liveDisplayCategory' in item:
            labels['genre'] = item['cbc$liveDisplayCategory']
        elif 'media:keywords' in item:
            labels['genre'] = item['media:keywords']

        if 'clearleap:season' in item:
            labels['season'] = item['clearleap:season']

        if 'clearleap:episodeInSeason' in item:
            labels['episode'] = item['clearleap:episodeInSeason']

        if 'media:rating' in item:
            labels['mpaa'] =  item['media:rating']

        if 'premiered' in item:
            labels['premiered'] = item['premiered']

        if 'video' in item:
            labels['mediatype'] = 'video'
        elif 'cbc$audioVideo' in item:
            if item['cbc$audioVideo'].lower() == 'video':
                labels['mediatype'] = 'video'

        return labels


    def parseSmil(self, smil):
        r = self.session.get(smil)

        if not r.status_code == 200:
            log('ERROR: {} returns status of {}'.format(url, r.status_code), True)
            return None
        saveCookies(self.session.cookies)

        dom = parseString(r.content)
        seq = dom.getElementsByTagName('seq')[0]
        video = seq.getElementsByTagName('video')[0]
        src = video.attributes['src'].value
        title = video.attributes['title'].value
        abstract = video.attributes['abstract'].value
        return src
