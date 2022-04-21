import requests
from resources.lib.utils import Util
from resources.lib.globals import *
from kodi_six import xbmc, xbmcaddon, xbmcgui
import time, uuid
import random
import string

if sys.version_info[0] > 2:
    from urllib.parse import quote
else:
    from urllib import quote


class Account:
    addon = xbmcaddon.Addon()
    username = ''
    password = ''
    session_key = ''
    icon = addon.getAddonInfo('icon')
    verify = True

    def __init__(self):
        self.username = self.addon.getSetting('username')
        self.password = self.addon.getSetting('password')
        self.session_key = self.addon.getSetting('session_key')
        self.did = self.device_id()
        self.util = Util()

    def device_id(self):
        if self.addon.getSetting('device_id') == '':
            self.addon.setSetting('device_id', str(uuid.uuid4()))

        return self.addon.getSetting('device_id')

    def login(self):
        # Check if username and password are provided
        if self.username == '':
            dialog = xbmcgui.Dialog()
            self.username = dialog.input(LOCAL_STRING(30240), type=xbmcgui.INPUT_ALPHANUM)
            self.addon.setSetting(id='username', value=self.username)

        if self.password == '':
            dialog = xbmcgui.Dialog()
            self.password = dialog.input(LOCAL_STRING(30250), type=xbmcgui.INPUT_ALPHANUM,
                                    option=xbmcgui.ALPHANUM_HIDE_INPUT)
            self.addon.setSetting(id='password', value=self.password)

        if self.username == '' or self.password == '':
            sys.exit()
        else:
            url = 'https://ids.mlb.com/oauth2/aus1m088yK07noBfh356/v1/token'
            headers = {'User-Agent': UA_ANDROID,
                       'Content-Type': 'application/x-www-form-urlencoded'
                       }
            payload = ('grant_type=password&username=%s&password=%s&scope=openid offline_access'
                       '&client_id=0oa3e1nutA1HLzAKG356') % (quote(self.username),
                                                             quote(self.password))

            r = requests.post(url, headers=headers, data=payload, verify=self.verify)
            if r.ok:
                login_token = r.json()['access_token']
                self.addon.setSetting('login_token', login_token)
                self.addon.setSetting('last_login', str(time.time()))
            else:
                dialog = xbmcgui.Dialog()
                msg = LOCAL_STRING(30263)
                if 'error_description' in r.json():
                    msg = r.json()['error_description']
                dialog.notification(LOCAL_STRING(30262), msg, ICON, 5000, False)
                self.addon.setSetting('login_token', '')
                self.addon.setSetting('last_login', '')
                sys.exit()


    def logout(self):
        self.util.delete_cookies()
        self.addon.setSetting('login_token', '')
        self.addon.setSetting('last_login', '')
        self.addon.setSetting('username', '')
        self.addon.setSetting('password', '')
        self.addon.setSetting('okta_client_id', '')
        self.addon.setSetting('session_token', '')
        self.addon.setSetting('okta_access_token', '')
        self.addon.setSetting('okta_access_token_expiry', '')

    def media_entitlement(self):
        if self.addon.getSetting('last_login') == '' or \
                (time.time() - float(self.addon.getSetting('last_login')) >= 86400):
            self.login()

        url = 'https://media-entitlement.mlb.com/api/v3/jwt?os=Android&appname=AtBat&did=' + self.device_id()
        headers = {'User-Agent': UA_ANDROID,
                   'Authorization': 'Bearer ' + self.addon.getSetting('login_token')
                   }

        r = requests.get(url, headers=headers, verify=self.verify)

        return r.text

    # the okta client id is used to get an okta access token (for featured videos like Big Inning)
    # doesn't change, can be cached until logout
    def okta_client_id(self):
        if self.addon.getSetting('okta_client_id') == '':
            xbmc.log('fetching okta_client_id')
            url = 'https://www.mlbstatic.com/mlb.com/vendor/mlb-okta/mlb-okta.js'
            headers = {
                'User-Agent': UA_PC,
                'Origin': 'https://www.mlb.com'
            }

            r = requests.get(url, headers=headers, verify=self.verify)
            e = re.search('production:{clientId:"([^"]+)",', r.text)
            if e:
                xbmc.log('found okta_client_id')
                okta_client_id = e.group(1)
                xbmc.log('okta_client_id: ' + okta_client_id)
                self.addon.setSetting(id='okta_client_id', value=okta_client_id)
                return okta_client_id
        else:
            return self.addon.getSetting('okta_client_id')

    # the session token is used to get an okta access token (for featured videos like Big Inning)
    # doesn't change much, can be cached until logout or until reset by okta_access_token function as needed
    def session_token(self):
        xbmc.log('requesting new session_token')

        # Check if username and password are provided
        if self.username == '':
            dialog = xbmcgui.Dialog()
            self.username = dialog.input(LOCAL_STRING(30240), type=xbmcgui.INPUT_ALPHANUM)
            self.addon.setSetting(id='username', value=self.username)

        if self.password == '':
            dialog = xbmcgui.Dialog()
            self.password = dialog.input(LOCAL_STRING(30250), type=xbmcgui.INPUT_ALPHANUM,
                                    option=xbmcgui.ALPHANUM_HIDE_INPUT)
            self.addon.setSetting(id='password', value=self.password)

        if self.username == '' or self.password == '':
            sys.exit()
        else:
            url = 'https://ids.mlb.com/api/v1/authn'
            headers = {
                'User-Agent': UA_PC,
                'Accept-Encoding': 'identity',
                'Content-Type': 'application/json'
            }
            data = {
              'username': self.username,
              'password': self.password,
              'options': {
                'multiOptionalFactorEnroll': False,
                'warnBeforePasswordExpired': True
              }
            }
            r = requests.post(url, headers=headers, json=data, verify=self.verify)
            xbmc.log(r.text)
            if 'sessionToken' in r.json():
                xbmc.log('found session_token')
                session_token = r.json()['sessionToken']
                self.addon.setSetting(id='session_token', value=session_token)

    # generate a random string of specified length, using numbers and uppercase letters
    # used for two variables in okta access token request
    def get_random_string(self, length):
        characters = string.ascii_uppercase + string.digits
        result_str = ''.join(random.choice(characters) for i in range(length))
        return result_str

    # the okta access token is used to access featured videos like Big Inning
    # can be cached until the specified expiry
    def okta_access_token(self, retry=False):
        # log in first, if needed
        if self.addon.getSetting('last_login') == '' or \
                (time.time() - float(self.addon.getSetting('last_login')) >= 86400):
            self.login()
        # check if we don't have it cached, or the cache has expired
        if self.addon.getSetting('okta_access_token') == '' or \
                parse(self.addon.getSetting('okta_access_token_expiry')) < datetime.now():
            xbmc.log('okta access token not set or expired')
            # check if we have a cached session token (shouldn't expire often)
            if self.addon.getSetting('session_token') == '':
                self.session_token()

            url = 'https://ids.mlb.com/oauth2/aus1m088yK07noBfh356/v1/authorize'
            xbmc.log('url : ' + url)
            headers = {
                'User-Agent': UA_PC,
                'accept-encoding': 'identity'
            }
            data = {
                'client_id': self.okta_client_id(),
                'redirect_uri': 'https://www.mlb.com/login',
                'response_type': 'id_token token',
                'response_mode': 'okta_post_message',
                'state': self.get_random_string(64),
                'nonce': self.get_random_string(64),
                'prompt': 'none',
                'sessionToken': self.addon.getSetting('session_token'),
                'scope': 'openid email'
            }
            r = requests.get(url, headers=headers, params=data, verify=self.verify)
            # check if the response indicates we need a new session token
            e = re.search("data.error = 'login_required'", r.text)
            if e:
                # if this is our second try, and we're still getting this error, just abort
                if retry == True:
                    xbmc.log('log in error, aborting')
                    sys.exit()
                else:
                    xbmc.log('not logged in, trying again')
                    self.addon.setSetting(id='session_token', value='')
                    okta_access_token = self.okta_access_token(True)
            else:
                xbmc.log('logged in')
                e = re.search("data.access_token = '([^']+)'", r.text)
                if e:
                    xbmc.log('found token')
                    # new token response likely contains a hyphen that needs to be decoded/un-escaped
                    okta_access_token = e.group(1).replace('\\x2D', '-')
                    xbmc.log('token result: ' + okta_access_token)
                    self.addon.setSetting(id='okta_access_token', value=okta_access_token)
                    # default token expiry is 86400 seconds (24 hours)
                    okta_access_token_expires_in = '86400'
                    e = re.search("data.expires_in = '([^']+)'", r.text)
                    if e:
                        xbmc.log('found expiry')
                        okta_access_token_expires_in = e.group(1)
                        xbmc.log('expires in: ' + okta_access_token_expires_in)
                    okta_access_token_expiry = datetime.now() + timedelta(seconds=int(okta_access_token_expires_in))
                    xbmc.log('expiry: ' + str(okta_access_token_expiry))
                    self.addon.setSetting(id='okta_access_token_expiry', value=str(okta_access_token_expiry))
        else:
            # cached token response likely contains a hyphen that needs to be decoded/un-escaped
            okta_access_token = self.addon.getSetting('okta_access_token').replace('\\x2D', '-')

        return okta_access_token

    def access_token(self):
        url = 'https://us.edge.bamgrid.com/token'
        headers = {'Accept': 'application/json',
                   'Authorization': 'Bearer bWxidHYmYW5kcm9pZCYxLjAuMA.6LZMbH2r--rbXcgEabaDdIslpo4RyZrlVfWZhsAgXIk',
                   'Content-Type': 'application/x-www-form-urlencoded'
                   }
        payload = 'grant_type=urn:ietf:params:oauth:grant-type:token-exchange&subject_token=%s' \
                  '&subject_token_type=urn:ietf:params:oauth:token-type:jwt&platform=android-tv' \
                  % self.media_entitlement()

        r = requests.post(url, headers=headers, data=payload, verify=self.verify)
        access_token = r.json()['access_token']
        # refresh_token = r.json()['refresh_token']

        return access_token

    def get_playback_url(self, content_id):
        auth = self.access_token()
        url = 'https://search-api-mlbtv.mlb.com/svc/search/v2/graphql/persisted/query/core/Airings' \
              '?variables=%7B%22contentId%22%3A%22' + content_id + '%22%7D'

        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + auth,
            'X-BAMSDK-Version': 'v4.3.0',
            'X-BAMSDK-Platform': 'android-tv',
            'User-Agent': 'BAMSDK/v4.3.0 (mlbaseball-7993996e 8.1.0; v2.0/v4.3.0; android; tv)'
        }

        r = requests.get(url, headers=headers, cookies=self.util.load_cookies(), verify=self.verify)
        if not r.ok:
            dialog = xbmcgui.Dialog()
            msg = ""
            for item in r.json()['errors']:
                msg += item['code'] + '\n'
            dialog.notification(LOCAL_STRING(30270), msg, self.icon, 5000, False)
            sys.exit()

        broadcast_start = '1'
        try:
            offset_index = 0
            if r.json()['data']['Airings'][0]['milestones'][0]['milestoneTime'][1]['type'] == 'offset':
                offset_index = 1
            broadcast_start = r.json()['data']['Airings'][0]['milestones'][0]['milestoneTime'][offset_index]['start']
            if isinstance(broadcast_start, int):
                broadcast_start = str(broadcast_start)
        except:
            pass
        
        return auth, r.json()['data']['Airings'][0]['playbackUrls'][0]['href'], broadcast_start

    def get_stream(self, content_id):
        auth, url, broadcast_start = self.get_playback_url(content_id)

        url = url.replace('{scenario}','browser~csai')
        headers = {
            'Accept': 'application/vnd.media-service+json; version=2',
            'Authorization': auth,
            'X-BAMSDK-Version': '3.0',
            'X-BAMSDK-Platform': 'windows',
            'User-Agent': UA_PC
        }

        r = requests.get(url, headers=headers, cookies=self.util.load_cookies(), verify=self.verify)
        if not r.ok:
            dialog = xbmcgui.Dialog()
            msg = ""
            for item in r.json()['errors']:
                msg += item['code'] + '\n'
            dialog.notification(LOCAL_STRING(30270), msg, self.icon, 5000, False)
            sys.exit()

        if 'complete' in r.json()['stream']:
            stream_url = r.json()['stream']['complete']
        else:
            stream_url = r.json()['stream']['slide']

        if QUALITY == 'Always Ask':
            stream_url = self.get_stream_quality(stream_url)
        headers = 'User-Agent=' + UA_PC
        headers += '&Authorization=' + auth
        headers += '&Cookie='
        cookies = requests.utils.dict_from_cookiejar(self.util.load_cookies())
        if sys.version_info[0] <= 2:
            cookies = cookies.iteritems()
        for key, value in cookies:
            headers += key + '=' + value + '; '
            
        #CDN
        akc_url = 'hlslive-aksc'
        l3c_url = 'hlslive-l3c'
        if CDN == 'Akamai' and akc_url not in stream_url:
            stream_url = stream_url.replace(l3c_url, akc_url)
        elif CDN == 'Level 3' and l3c_url not in stream_url:
            stream_url = stream_url.replace(akc_url, l3c_url)
        
        return stream_url, headers, broadcast_start

    def get_stream_quality(self, stream_url):
        #Check if inputstream adaptive is on, if so warn user and return master m3u8
        if xbmc.getCondVisibility('System.HasAddon(inputstream.adaptive)'):
            dialog = xbmcgui.Dialog()
            dialog.ok(LOCAL_STRING(30370), LOCAL_STRING(30371))
            return stream_url

        stream_title = []
        stream_urls = []
        headers = {'User-Agent': UA_PC}

        r = requests.get(stream_url, headers=headers, verify=False)
        master = r.text

        line = re.compile("(.+?)\n").findall(master)

        for temp_url in line:
            if '#EXT' not in temp_url:
                match = re.search(r'(\d.+?)K', temp_url, re.IGNORECASE)
                bandwidth = match.group()
                if 0 < len(bandwidth) < 6:
                    bandwidth = bandwidth.replace('K', ' kbps')
                    stream_title.append(bandwidth)
                    stream_urls.append(temp_url)

        stream_title.sort(key=self.util.natural_sort_key, reverse=True)
        stream_urls.sort(key=self.util.natural_sort_key, reverse=True)
        dialog = xbmcgui.Dialog()
        ret = dialog.select(LOCAL_STRING(30372), stream_title)
        if ret >= 0:
            if 'http' not in stream_urls[ret]:
                stream_url = stream_url.replace(stream_url.rsplit('/', 1)[-1], stream_urls[ret])
            else:
                stream_url = stream_urls[ret]
        else:
            sys.exit()

        return stream_url
