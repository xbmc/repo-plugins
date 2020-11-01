import requests
from resources.lib.utils import Util
from resources.lib.globals import *
from kodi_six import xbmc, xbmcaddon, xbmcgui
import time, uuid

if sys.version_info[0] > 2:
    from urllib.parse import quote
else:
    from urllib import quote


class Account:
    addon = xbmcaddon.Addon()
    username = ''
    password = ''
    session_key = ''
    icon = os.path.join(addon.getAddonInfo('path'), 'icon.png')
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
            self.username = dialog.input('Please enter your username', type=xbmcgui.INPUT_ALPHANUM)
            self.addon.setSetting(id='username', value=self.username)

        if self.password == '':
            dialog = xbmcgui.Dialog()
            self.password = dialog.input('Please enter your password', type=xbmcgui.INPUT_ALPHANUM,
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
                title = "Login Failed"
                msg = "Please check your credentials and try again"
                if 'error_description' in r.json():
                    msg = r.json()['error_description']
                dialog.notification(title, msg, ICON, 5000, False)
                self.addon.setSetting('login_token', '')
                self.addon.setSetting('last_login', '')
                sys.exit()


    def logout(self):
        self.util.delete_cookies()
        self.addon.setSetting('login_token', '')
        self.addon.setSetting('last_login', '')
        self.addon.setSetting('username', '')
        self.addon.setSetting('password', '')

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
            title = "Error Occured"
            msg = ""
            for item in r.json()['errors']:
                msg += item['code'] + '\n'
            dialog.notification(title, msg, self.icon, 5000, False)
            sys.exit()

        return auth, r.json()['data']['Airings'][0]['playbackUrls'][0]['href']

    def get_stream(self, content_id):
        auth, url = self.get_playback_url(content_id)

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
            title = "Error Occured"
            msg = ""
            for item in r.json()['errors']:
                msg += item['code'] + '\n'
            dialog.notification(title, msg, self.icon, 5000, False)
            sys.exit()

        if 'slide' in r.json()['stream']:
            stream_url = r.json()['stream']['slide']
        else:
            stream_url = r.json()['stream']['complete']

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
        
        return stream_url, headers

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
        ret = dialog.select('Choose Stream Quality', stream_title)
        if ret >= 0:
            if 'http' not in stream_urls[ret]:
                stream_url = stream_url.replace(stream_url.rsplit('/', 1)[-1], stream_urls[ret])
            else:
                stream_url = stream_urls[ret]
        else:
            sys.exit()

        return stream_url
