__author__ = 'bromix'

import time
import urlparse
import xbmc

from resources.lib.kodion import simple_requests as requests
from resources.lib.youtube.youtube_exceptions import LoginException

# Kodi 17 support and API keys by Uukrul
def log_error(text):
    xbmc.log('YouTube login_client.py - %s' % (text),xbmc.LOGERROR)

class LoginClient(object):
    CONFIGS = {
        'youtube-tv': {
            'system': 'All',
            'key': 'AIzaSyAd-YEOqZz9nXVzGtn3KWzYLbLaajhqIDA',
            'id': '861556708454-d6dlm3lh05idd8npek18k6be8ba3oc68.apps.googleusercontent.com',
            'secret': 'SboVhoG9s0rNafixCSGGKXAT'
        },
        # API KEY for search and channel infos. These should work most of the time without login to safe some quota
        'youtube-for-kodi-quota': {
            'token-allowed': False,
            'system': 'All',
            'key': 'AIzaSyBLzlcN2eCzOhnl1WhyX0kYuyu-kwshDt8',
            'id': '707691027705-s4mq8q747f8mrb0vjcn3jvp17af4819o.apps.googleusercontent.com',
            'secret': 'r_95MHjK38AyCkoEQm8fzcCM'
        },
        'youtube-for-kodi-fallback': {
            'token-allowed': False,
            'system': 'Fallback!',
            'key': 'AIzaSyAUjiaAUOcm6wmA8BHMloDby6U4RMtKLvs',
            'id': '970514987436-b1rlhh1sf3fufqcvlm2a2taa2tq4t5uc.apps.googleusercontent.com',
            'secret': 'zFaJYGEbvx329c8G_GPO5RJ3'
        },
        'youtube-for-kodi-12': {
            'system': 'Frodo',
            'key': 'AIzaSyCDn_9EybTJiymHipNS3jk5ZpCTXdCotQ0',
            'id': '947596709414-08nrn314d8j3k91cl4f51srcu6m19hvu.apps.googleusercontent.com',
            'secret': 'HsLT2ZCexIV-VFxWeYVZ2TUc'
        },
        'youtube-for-kodi-13': {
            'system': 'Gotham',
            'key': 'AIzaSyAmrf3BneEQPDiUEuQlzy0_rbFGDBg-bi0',
            'id': '448940676713-min9u5frfujprbnb8f3dri3cv9jr32rn.apps.googleusercontent.com',
            'secret': '79vMsJsNC9jypSfryUMu00jW'
        },
        'youtube-for-kodi-14': {
            'system': 'Helix',
            'key': 'AIzaSyCCnZImC7gTniNfgwqGwixIdBVGxiCOKlU',
            'id': '107500767506-9mvbaacuscf8cge2n3kkvj50a6dnrk8g.apps.googleusercontent.com',
            'secret': '2ceVfognBCtn8uh20HmlJN4X'
        },
        'youtube-for-kodi-15': {
            'system': 'Isengard',
            'key': 'AIzaSyATqDim-56y8HcN1NAzQdVZgdMoc6d9Eys',
            'id': '610696918705-bkt6v536k7gn2dtcv8vdngm4b0vt5sev.apps.googleusercontent.com',
            'secret': 'kV7ReP1f_Lg9i2hWR2liHnO6'
        },
        'youtube-for-kodi-16': {
            'system': 'Jarvis',
            'key': 'AIzaSyBS3rNymJtzPYbJX5lSGdNCBS6ajh4VDDY',
            'id': '879761788105-sduf0ht335dvg923ane7cg1jnt1d5l4k.apps.googleusercontent.com',
            'secret': 'vBVDa-kNdCHDTkpD8b8HO718'
        },
        'youtube-for-kodi-17': {
            'system': 'Krypton',
            'key': 'AIzaSyBynxCrJOe3NWa4l2VezTHWVIQOrI9nPgY',
            'id': '167759489832-579ic1cjlk5j6fg6bo6d7btvces6528p.apps.googleusercontent.com',
            'secret': 'n93VQADkcc-HIqbx_kvnpAs4'
        }
    }

    def __init__(self, config={}, language='en-US', access_token='', access_token_tv=''):
        if not config:
            config = self.CONFIGS['youtube-for-kodi-fallback']
            pass

        self._config = config
        self._config_tv = self.CONFIGS['youtube-tv']

        # the default language is always en_US (like YouTube on the WEB)
        if not language:
            language = 'en_US'
            pass

        language = language.replace('-', '_')
        language_components = language.split('_')
        if len(language_components) != 2:
            language = 'en_US'
            pass

        self._language = language
        self._country = language.split('_')[1]
        self._access_token = access_token
        self._access_token_tv = access_token_tv
        self._log_error_callback = None
        pass

    def set_log_error(self, callback):
        self._log_error_callback = callback
        pass

    def log_error(self, text):
        if self._log_error_callback:
            self._log_error_callback(text)
            pass
        else:
            print text
            pass
        pass

    def revoke(self, refresh_token):
        headers = {'Host': 'www.youtube.com',
                   'Connection': 'keep-alive',
                   'Origin': 'https://www.youtube.com',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.28 Safari/537.36',
                   'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                   'Accept': '*/*',
                   'DNT': '1',
                   'Referer': 'https://www.youtube.com/tv',
                   'Accept-Encoding': 'gzip, deflate',
                   'Accept-Language': 'en-US,en;q=0.8,de;q=0.6'}

        post_data = {'token': refresh_token}

        # url
        url = 'https://www.youtube.com/o/oauth2/revoke'

        result = requests.post(url, data=post_data, headers=headers, verify=False)
        if result.status_code != requests.codes.ok:
            log_error('revoke')
            raise LoginException('Logout Failed')

        pass

    def refresh_token_tv(self, refresh_token, grant_type=''):
        client_id = self.CONFIGS['youtube-tv']['id']
        client_secret = self.CONFIGS['youtube-tv']['secret']
        return self.refresh_token(refresh_token, client_id=client_id, client_secret=client_secret,
                                  grant_type=grant_type)

    def refresh_token(self, refresh_token, client_id='', client_secret='', grant_type=''):
        headers = {'Host': 'www.youtube.com',
                   'Connection': 'keep-alive',
                   'Origin': 'https://www.youtube.com',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.28 Safari/537.36',
                   'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                   'Accept': '*/*',
                   'DNT': '1',
                   'Referer': 'https://www.youtube.com/tv',
                   'Accept-Encoding': 'gzip, deflate',
                   'Accept-Language': 'en-US,en;q=0.8,de;q=0.6'}

        _client_id = client_id
        if not client_id:
            _client_id = self._config['id']
            pass
        _client_secret = client_secret
        if not _client_secret:
            _client_secret = self._config['secret']
            pass
        post_data = {'client_id': _client_id,
                     'client_secret': _client_secret,
                     'refresh_token': refresh_token,
                     'grant_type': 'refresh_token'}

        # url
        url = 'https://www.youtube.com/o/oauth2/token'

        result = requests.post(url, data=post_data, headers=headers, verify=False)
        if result.status_code != requests.codes.ok:
            log_error('refresh_token')
            raise LoginException('Login Failed')

        if result.headers.get('content-type', '').startswith('application/json'):
            json_data = result.json()
            access_token = json_data['access_token']
            expires_in = time.time() + int(json_data.get('expires_in', 3600))
            return access_token, expires_in

        return '', ''

    def get_device_token_tv(self, code, client_id='', client_secret='', grant_type=''):
        client_id = self.CONFIGS['youtube-tv']['id']
        client_secret = self.CONFIGS['youtube-tv']['secret']
        return self.get_device_token(code, client_id=client_id, client_secret=client_secret, grant_type=grant_type)

    def get_device_token(self, code, client_id='', client_secret='', grant_type=''):
        headers = {'Host': 'www.youtube.com',
                   'Connection': 'keep-alive',
                   'Origin': 'https://www.youtube.com',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.28 Safari/537.36',
                   'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                   'Accept': '*/*',
                   'DNT': '1',
                   'Referer': 'https://www.youtube.com/tv',
                   'Accept-Encoding': 'gzip, deflate',
                   'Accept-Language': 'en-US,en;q=0.8,de;q=0.6'}

        _client_id = client_id
        if not client_id:
            _client_id = self._config['id']
            pass
        _client_secret = client_secret
        if not _client_secret:
            _client_secret = self._config['secret']
            pass
        post_data = {'client_id': _client_id,
                     'client_secret': _client_secret,
                     'code': code,
                     'grant_type': 'http://oauth.net/grant_type/device/1.0'}

        # url
        url = 'https://www.youtube.com/o/oauth2/token'

        result = requests.post(url, data=post_data, headers=headers, verify=False)
        if result.status_code != requests.codes.ok:
            log_error('get_device_token')
            raise LoginException('Login Failed')

        if result.headers.get('content-type', '').startswith('application/json'):
            return result.json()

        return None

    def generate_user_code_tv(self):
        client_id = self.CONFIGS['youtube-tv']['id']
        return self.generate_user_code(client_id=client_id)

    def generate_user_code(self, client_id=''):
        headers = {'Host': 'www.youtube.com',
                   'Connection': 'keep-alive',
                   'Origin': 'https://www.youtube.com',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.28 Safari/537.36',
                   'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                   'Accept': '*/*',
                   'DNT': '1',
                   'Referer': 'https://www.youtube.com/tv',
                   'Accept-Encoding': 'gzip, deflate',
                   'Accept-Language': 'en-US,en;q=0.8,de;q=0.6'}

        _client_id = client_id
        if not client_id:
            _client_id = self._config['id']
        post_data = {'client_id': _client_id,
                     'scope': 'https://www.googleapis.com/auth/youtube'}
        # 'scope': 'http://gdata.youtube.com https://www.googleapis.com/auth/youtube-paid-content'}

        # url
        url = 'https://www.youtube.com/o/oauth2/device/code'

        result = requests.post(url, data=post_data, headers=headers, verify=False)
        if result.status_code != requests.codes.ok:
            log_error(result.text)
            raise LoginException('Login Failed')

        if result.headers.get('content-type', '').startswith('application/json'):
            return result.json()

        return None

    def get_access_token(self):
        return self._access_token

    def authenticate(self, username, password):
        headers = {'device': '38c6ee9a82b8b10a',
                   'app': 'com.google.android.youtube',
                   'User-Agent': 'GoogleAuth/1.4 (GT-I9100 KTU84Q)',
                   'content-type': 'application/x-www-form-urlencoded',
                   'Host': 'android.clients.google.com',
                   'Connection': 'Keep-Alive',
                   'Accept-Encoding': 'gzip'}

        post_data = {'device_country': self._country.lower(),
                     'operatorCountry': self._country.lower(),
                     'lang': self._language.replace('-', '_'),
                     'sdk_version': '19',
                     # 'google_play_services_version': '6188034',
                     'accountType': 'HOSTED_OR_GOOGLE',
                     'Email': username.encode('utf-8'),
                     'service': 'oauth2:https://www.googleapis.com/auth/youtube https://www.googleapis.com/auth/youtube.force-ssl https://www.googleapis.com/auth/plus.me https://www.googleapis.com/auth/emeraldsea.mobileapps.doritos.cookie https://www.googleapis.com/auth/plus.stream.read https://www.googleapis.com/auth/plus.stream.write https://www.googleapis.com/auth/plus.pages.manage https://www.googleapis.com/auth/identity.plus.page.impersonation',
                     'source': 'android',
                     'androidId': '38c6ee9a82b8b10a',
                     'app': 'com.google.android.youtube',
                     # 'client_sig': '24bb24c05e47e0aefa68a58a766179d9b613a600',
                     'callerPkg': 'com.google.android.youtube',
                     # 'callerSig': '24bb24c05e47e0aefa68a58a766179d9b613a600',
                     'Passwd': password.encode('utf-8')}

        # url
        url = 'https://android.clients.google.com/auth'

        result = requests.post(url, data=post_data, headers=headers, verify=False)
        if result.status_code != requests.codes.ok:
            log_error('authenticate')
            raise LoginException('Login Failed')

        lines = result.text.replace('\n', '&')
        params = dict(urlparse.parse_qsl(lines))
        token = params.get('Auth', '')
        expires = int(params.get('Expiry', -1))
        if not token or expires == -1:
            raise LoginException('Failed to get token')

        return token, expires

    pass
