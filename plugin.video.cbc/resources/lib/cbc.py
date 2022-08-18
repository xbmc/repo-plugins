"""Module for general CBC stuff"""
import urllib.request
import urllib.parse
import urllib.error
import json
from xml.dom.minidom import *
import xml.etree.ElementTree as ET

import requests

from .utils import save_cookies, loadCookies, saveAuthorization, log

CALLSIGN = 'cbc$callSign'
API_KEY = '3f4beddd-2061-49b0-ae80-6f1f2ed65b37'
RADIUS_LOGIN_FMT = 'https://api.loginradius.com/identity/v2/auth/login?{}'
RADIUS_JWT_FMT = 'https://cloud-api.loginradius.com/sso/jwt/api/token?{}'
TOKEN_URL = 'https://services.radio-canada.ca/ott/cbc-api/v2/token'
PROFILE_URL = 'https://services.radio-canada.ca/ott/cbc-api/v2/profile'


class CBC:
    """Class for CBC stuff."""

    def __init__(self):
        """Initialize the CBC class."""
        # Create requests session object
        self.session = requests.Session()
        session_cookies = loadCookies()
        if session_cookies is not None:
            self.session.cookies = session_cookies

    def authorize(self, username=None, password=None, callback=None):
        """Authorize for video playback."""
        token = self.radius_login(username, password)
        if callback is not None:
            callback(25)
        if token is None:
            log('Radius Login failed', True)
            return False

        jwt = self.radius_jwt(token)
        if callback is not None:
            callback(50)
        if jwt is None:
            log('Radius JWT retrieval failed', True)
            return False

        # token = self.login(login_url, auth['devid'], jwt)
        auth = {}
        token = self.get_access_token(jwt)
        if callback is not None:
            callback(75)
        if token is None:
            log('Access token retrieval failed', True)
            return False
        auth['token'] = token

        claims = self.get_claims_token(token)
        if callback is not None:
            callback(100)
        if token is None:
            log('Claims token retrieval failed', True)
            return False
        auth['claims'] = claims

        saveAuthorization(auth)
        save_cookies(self.session.cookies)

        return True

    def radius_login(self, username, password):
        """Login with Radius using user credentials."""
        query = urllib.parse.urlencode({'apikey': API_KEY})

        data = {
            'email': username,
            'password': password
        }
        url = RADIUS_LOGIN_FMT.format(query)
        req = self.session.post(url, json=data)
        if not req.status_code == 200:
            log('{} returns status {}'.format(req.url, req.status_code), True)
            return None

        token = json.loads(req.content)['access_token']

        return token

    def radius_jwt(self, token):
        """Exchange a radius token for a JWT."""
        query = urllib.parse.urlencode({
            'access_token': token,
            'apikey': API_KEY,
            'jwtapp': 'jwt'
        })
        url = RADIUS_JWT_FMT.format(query)
        req = self.session.get(url)
        if not req.status_code == 200:
            log('{} returns status {}'.format(req.url, req.status_code))
            return None
        return json.loads(req.content)['signature']

    def get_access_token(self, jwt):
        """Exchange a JWT for another JWT."""
        data = {'jwt': jwt}
        req = self.session.post(TOKEN_URL, json=data)
        if not req.status_code == 200:
            log('{} returns status {}'.format(req.url, req.status_code), True)
            return None
        return json.loads(req.content)['accessToken']

    def get_claims_token(self, access_token):
        """Get the claims token for tied to the access token."""
        headers = {'ott-access-token': access_token}
        req = self.session.get(PROFILE_URL, headers=headers)
        if not req.status_code == 200:
            log('{} returns status {}'.format(req.url, req.status_code), True)
            return None
        return json.loads(req.content)['claimsToken']

    def getImage(self, item):
        # ignore 'cbc$liveImage' - the pix don't make sense after the first load
        if 'defaultThumbnailUrl' in item:
            return item['defaultThumbnailUrl']
        if 'cbc$staticImage' in item:
            return item['cbc$staticImage']
        if 'cbc$featureImage' in item:
            return item['cbc$featureImage']
        return None

    @staticmethod
    def get_callsign(item):
        """Get the callsign for a channel."""
        return item[CALLSIGN] if CALLSIGN in item else None

    @staticmethod
    def get_labels(item):
        """Get labels for a CBC item."""
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
            log('ERROR: {} returns status of {}'.format(smil, r.status_code), True)
            return None
        save_cookies(self.session.cookies)

        dom = parseString(r.content)
        seq = dom.getElementsByTagName('seq')[0]
        video = seq.getElementsByTagName('video')[0]
        src = video.attributes['src'].value
        title = video.attributes['title'].value
        abstract = video.attributes['abstract'].value
        return src

    def get_session():
        """Get a requests session object with CBC cookies."""
        sess = requests.Session()
        cookies = loadCookies()
        if cookies is not None:
            sess.cookies = cookies
        return sess
