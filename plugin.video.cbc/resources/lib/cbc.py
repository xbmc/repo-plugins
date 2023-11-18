"""Module for general CBC stuff"""
from uuid import uuid4
from base64 import b64encode, b64decode
import json
# import http.client as http_client
from urllib.parse import urlparse, parse_qs
from xml.dom.minidom import parseString

import requests

from .utils import save_cookies, loadCookies, saveAuthorization, log

# http_client.HTTPConnection.debuglevel = 1

CALLSIGN = 'cbc$callSign'
CHANNEL_GUID = 'guid'
API_KEY = '3f4beddd-2061-49b0-ae80-6f1f2ed65b37'
SCOPES = 'openid '\
        'offline_access '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/email '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/id.account.create '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/id.account.delete '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/id.account.info '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/id.account.modify '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/id.account.reset-password '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/id.account.send-confirmation-email '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/id.write '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/media-drmt '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/media-meta '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/media-validation '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/media-validation.read '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/metrik '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/oidc4ropc '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/ott-profiling '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/ott-subscription '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/profile '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/subscriptions.validate '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/subscriptions.write '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/toutv '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/toutv-presentation '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/toutv-profiling '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/testapiwithjwtendpoint.admin '\
        'https://rcmnb2cprod.onmicrosoft.com/84593b65-0ef6-4a72-891c-d351ddd50aab/id.account.info'
AUTHORIZE_LOGIN = 'https://login.cbc.radio-canada.ca/bef1b538-1950-4283-9b27-b096cbc18070/B2C_1A_ExternalClient_FrontEnd_Login_CBC/oauth2/v2.0/authorize'
SELF_ASSERTED_LOGIN = 'https://login.cbc.radio-canada.ca/bef1b538-1950-4283-9b27-b096cbc18070/B2C_1A_ExternalClient_FrontEnd_Login_CBC/SelfAsserted'
CONFIRM_LOGIN = 'https://login.cbc.radio-canada.ca/bef1b538-1950-4283-9b27-b096cbc18070/B2C_1A_ExternalClient_FrontEnd_Login_CBC/api/SelfAsserted/confirmed'
SIGNIN_LOGIN = 'https://login.cbc.radio-canada.ca/bef1b538-1950-4283-9b27-b096cbc18070/B2C_1A_ExternalClient_FrontEnd_Login_CBC/api/CombinedSigninAndSignup/confirmed'
RADIUS_LOGIN_FMT = 'https://api.loginradius.com/identity/v2/auth/login?{}'
RADIUS_JWT_FMT = 'https://cloud-api.loginradius.com/sso/jwt/api/token?{}'
TOKEN_URL = 'https://services.radio-canada.ca/ott/cbc-api/v2/token'
PROFILE_URL = 'https://services.radio-canada.ca/ott/subscription/v2/gem/subscriber/profile'


class CBC:
    """Class for CBC stuff."""

    def __init__(self):
        """Initialize the CBC class."""
        # Create requests session object
        self.session = requests.Session()
        session_cookies = loadCookies()
        if session_cookies is not None:
            self.session.cookies = session_cookies

    @staticmethod
    def azure_authorize_authorize(sess: requests.Session):
        """
        Make the first authorization call.
        @param sess A requests session
        """
        nonce= str(uuid4())
        guid = str(uuid4())
        state_str = f'{guid}|{{"action":"login","returnUrl":"/","fromSubscription":false}}'.encode()
        state = b64encode(state_str).decode('ascii')
        params = {
            'client_id': 'fc05b0ee-3865-4400-a3cc-3da82c330c23',
            'nonce': nonce,
            'redirect_uri': 'https://gem.cbc.ca/auth-changed',
            'scope': SCOPES,
            'response_type': 'id_token token',
            'response_mode': 'fragment',
            'state': state,
            'state_value': state,
            'ui_locales': 'en',
        }
        resp = sess.get(AUTHORIZE_LOGIN, params=params)
        if resp.status_code != 200:
            log('Call to authorize fails', True)
            return False

        if not 'x-ms-gateway-requestid' in resp.headers:
            log('authorize authorize response had no x-ms-gateway-requestid header')
            return False

        return resp.headers['x-ms-gateway-requestid']

    @staticmethod
    def azure_authorize_self_asserted(sess: requests.Session, username: str, tx_arg: str, password: str = None):
        """
        Make the second authorization call.
        @param sess The requests session
        """
        cookies = sess.cookies.get_dict()
        headers = { 'x-csrf-token': cookies['x-ms-cpim-csrf'] }
        params = { 'tx': tx_arg, 'p': 'B2C_1A_ExternalClient_FrontEnd_Login_CBC' }
        data = { 'request_type': 'RESPONSE', 'email': username}
        if password:
            data['password'] = password

        resp = sess.post(SELF_ASSERTED_LOGIN, params=params, headers=headers, data=data)
        if not resp.status_code == 200:
            log('Call to SelfAsserted fails', True)
            return False
        return True

    @staticmethod
    def azure_authorize_confirmed(sess: requests.Session, tx_arg: str):
        """
        Make the third authorization call.
        @param sess The requests session
        @param csrf The csrf token
        @param tx_arg the tx parameter
        """
        cookies = sess.cookies.get_dict()
        params = {
            'tx': tx_arg,
            'p': 'B2C_1A_ExternalClient_FrontEnd_Login_CBC',
            'csrf_token': cookies['x-ms-cpim-csrf'],
        }

        resp = sess.get(CONFIRM_LOGIN, params=params)
        if resp.status_code != 200:
            log('Call to authorize fails', True)
            return False

        if not 'x-ms-gateway-requestid' in resp.headers:
            log('authorize confirmed response had no x-ms-gateway-requestid header')
            return False

        return resp.headers['x-ms-gateway-requestid']

    @staticmethod
    def azure_authorize_sign_in(sess: requests.Session, tx_arg: str):
        """
        Make the third authorization call.
        @param sess The requests session
        @param csrf The csrf token
        @param tx_arg the tx parameter
        """
        cookies = sess.cookies.get_dict()
        params = {
            'tx': tx_arg,
            'p': 'B2C_1A_ExternalClient_FrontEnd_Login_CBC',
            'csrf_token': cookies['x-ms-cpim-csrf'],
            'rememberMe': 'true',
        }

        resp = sess.get(SIGNIN_LOGIN, params=params, allow_redirects=False)
        if resp.status_code != 302:
            log('Call to authorize fails', True)
            return None

        url = urlparse(resp.headers['location'])
        frags = parse_qs(url.fragment)
        access_token = frags['access_token'][0]
        id_token = frags['id_token'][0]

        return (access_token, id_token)


    def azure_authorize(self, username=None, password=None, callback=None):
        """
        Perform multi-step authorization with CBC's azure authorization platform.
        ** Azure Active Directory B2C **
        """
        sess = requests.Session()

        if callback:
            callback(0)
        gw_req_id = CBC.azure_authorize_authorize(sess)
        if not gw_req_id:
            log('Authorization "authorize" step failed', True)
            return False

        if callback:
            callback(20)
        cookies = sess.cookies.get_dict()
        if 'x-ms-cpim-csrf' not in cookies:
            log('Unable to get csrt token for self asserted', True)
            return False

        if 'x-ms-cpim-trans' not in cookies:
            log('Unable to get transaction for self asserted', True)
            return False

        trans = cookies['x-ms-cpim-trans']
        trans = b64decode(trans).decode()
        trans = json.loads(trans)
        if not 'C_ID' in trans:
            log('Unable to get C_ID from trans', True)
            return False
        tid = trans['C_ID']

        tid_str = f'{{"TID":"{tid}"}}'.encode()
        b64_tid = b64encode(tid_str).decode('ascii')
        b64_tid = b64_tid.rstrip('=')
        tx_arg = f'StateProperties={b64_tid}'

        if callback:
            callback(40)
        if not CBC.azure_authorize_self_asserted(sess, username, tx_arg):
            log('Authorization "SelfAsserted" step failed', True)
            return False

        if callback:
            callback(60)
        gw_req_id = CBC.azure_authorize_confirmed(sess, tx_arg)
        if not gw_req_id:
            log('Authorization "confirmed" step failed', True)
            return False

        if callback:
            callback(80)
        if not CBC.azure_authorize_self_asserted(sess, username, tx_arg, password):
            log('Authorization "SelfAsserted" step failed', True)
            return False
        access_token, id_token = CBC.azure_authorize_sign_in(sess, tx_arg)
        if not access_token or not id_token:
            log('Authorization "confirmed" step failed', True)
            return False

        if callback:
            callback(90)
        claims_token = self.get_claims_token(access_token)

        saveAuthorization({'token': access_token, 'claims': claims_token})
        if callback:
            callback(100)

        return True

    def get_claims_token(self, access_token):
        """Get the claims token for tied to the access token."""
        headers = {'Authorization': f'Bearer {access_token}'}
        params = {'device': 'web'}
        req = self.session.get(PROFILE_URL, headers=headers, params=params)
        if not req.status_code == 200:
            log(f'{req.url} returns status {req.status_code}', True)
            return None
        return json.loads(req.content)['claimsToken']

    def get_image(self, item):
        """Get an image."""
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
        if CALLSIGN in item:
            return item[CALLSIGN]
        if CHANNEL_GUID in item:
            return item[CHANNEL_GUID]
        return None

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


    def parse_smil(self, smil):
        """Parse a SMIL file for the video."""
        resp = self.session.get(smil)

        if not resp.status_code == 200:
            log(f'ERROR: {smil} returns status of {resp.status_code}', True)
            return None
        save_cookies(self.session.cookies)

        dom = parseString(resp.content)
        seq = dom.getElementsByTagName('seq')[0]
        video = seq.getElementsByTagName('video')[0]
        src = video.attributes['src'].value
        return src

    @staticmethod
    def get_session():
        """Get a requests session object with CBC cookies."""
        sess = requests.Session()
        cookies = loadCookies()
        if cookies is not None:
            sess.cookies = cookies
        return sess
