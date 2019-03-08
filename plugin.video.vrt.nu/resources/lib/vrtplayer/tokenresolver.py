from resources.lib.helperobjects import helperobjects
import requests
import json
import datetime
import time

class TokenResolver:

    _API_KEY = '3_qhEcPa5JGFROVwu5SWKqJ4mVOIkwlFNMSKwzPDAh8QZOtHqu6L4nD5Q7lk0eXOOG'
    _LOGIN_URL = 'https://accounts.vrt.be/accounts.login'
    _TOKEN_GATEWAY_URL = 'https://token.vrt.be'
    _ONDEMAND_COOKIE = 'ondemand_vrtPlayerToken'
    _LIVE_COOKIE = 'live_vrtPlayerToken'
    _ROAMING_XVRTTOKEN_COOKIE = 'roaming_XVRTToken'
    _XVRT_TOKEN_COOKIE = 'XVRTToken'

    def __init__(self, kodi_wrapper):
        self._kodi_wrapper = kodi_wrapper

    def get_ondemand_playertoken(self, token_url, xvrttoken):
        token_path = self._kodi_wrapper.get_userdata_path() + self._ONDEMAND_COOKIE
        token = self._get_cached_token(token_path)

        if token == None:
            cookie_value = 'X-VRT-Token=' + xvrttoken
            headers = {'Content-Type': 'application/json', 'Cookie' : cookie_value}
            token = TokenResolver._get_new_playertoken(token_path, token_url, headers)
        return token

    def get_live_playertoken(self, token_url):
        token_path = self._kodi_wrapper.get_userdata_path() + self._LIVE_COOKIE
        token = self._get_cached_token(token_path)
        if token == None:
            headers = {'Content-Type': 'application/json'}
            token = TokenResolver._get_new_playertoken(token_path, token_url, headers)
        return token

    def get_xvrttoken(self, get_roaming_token = False):
        token_filename = self._ROAMING_XVRTTOKEN_COOKIE if get_roaming_token else self._XVRT_TOKEN_COOKIE
        token_path = self._kodi_wrapper.get_userdata_path() + token_filename
        token = self._get_cached_token(token_path)

        if token == None:
            token = self._get_new_xvrttoken(token_path, get_roaming_token)
        return token

    @staticmethod
    def _get_new_playertoken(path, token_url, headers):
        playertoken = requests.post(token_url, headers=headers).json()
        json.dump(playertoken, open(path,'w'))
        return playertoken['vrtPlayerToken']

    def _get_cached_token(self, path):
        cached_token = None

        if self._kodi_wrapper.check_if_path_exists(path):
            token = json.loads(open(path, 'r').read())
            now = datetime.datetime.utcnow()
            exp = datetime.datetime(*(time.strptime(token['expirationDate'], '%Y-%m-%dT%H:%M:%S.%fZ')[0:6]))
            if exp > now:
                self._kodi_wrapper.log_notice('Got cached token')
                cached_token = token[token.keys()[0]]
            else:
                self._kodi_wrapper.log_notice('Cached token deleted')
                self._kodi_wrapper.delete_path(path)
        return cached_token

    def _get_new_xvrttoken(self, path, get_roaming_token):
        cred = helperobjects.Credentials(self._kodi_wrapper)
        if not cred.are_filled_in():
            self._kodi_wrapper.open_settings()
            cred.reload()
        data = {'loginID': cred.username, 'password': cred.password, 'sessionExpiration': '-1', 'APIKey': self._API_KEY, 'targetEnv': 'jssdk'}
        logon_json = requests.post(self._LOGIN_URL, data).json()
        token = None
        if logon_json['errorCode'] == 0:
            session = logon_json['sessionInfo']
            login_token = logon_json['sessionInfo']['login_token']
            login_cookie = ''.join(('glt_', self._API_KEY, '=', login_token))
            payload = {'uid': logon_json['UID'], 'uidsig': logon_json['UIDSignature'], 'ts': logon_json['signatureTimestamp'], 'email': cred.username}
            headers = {'Content-Type': 'application/json', 'Cookie': login_cookie}
            cookie_jar = requests.post(self._TOKEN_GATEWAY_URL, headers=headers, json=payload).cookies
            
            xvrttoken = TokenResolver._create_token_dictionary(cookie_jar)
            token =  xvrttoken['X-VRT-Token']
            if get_roaming_token: 
                xvrttoken = TokenResolver._get_roaming_xvrttoken(login_cookie, xvrttoken)
                token = xvrttoken['X-VRT-Token'] if xvrttoken is not None else None
            json.dump(xvrttoken, open(path,'w'))
        else:
            title = self._kodi_wrapper.get_localized_string(32051)
            message = self._kodi_wrapper.get_localized_string(32052)
            self._kodi_wrapper.show_ok_dialog(title, message)
        return token

    @staticmethod
    def _get_roaming_xvrttoken(login_cookie, xvrttoken):
        url = 'https://token.vrt.be/vrtnuinitloginEU?destination=https://www.vrt.be/vrtnu/'
        cookie_value = 'X-VRT-Token=' + xvrttoken['X-VRT-Token']
        headers = {'Cookie' : cookie_value}
        r = requests.get(url, headers=headers, allow_redirects=False)
        url = r.headers.get('Location')
        r = requests.get(url, headers=headers, allow_redirects=False)
        url = r.headers.get('Location')
        headers = {'Cookie': login_cookie }
        roaming_xvrttoken = None
        if url is not None:
            cookie_jar = requests.get(url, headers=headers).cookies
            roaming_xvrttoken = TokenResolver._create_token_dictionary(cookie_jar)
        return roaming_xvrttoken

    @staticmethod
    def _create_token_dictionary(cookie_jar):
        token_dictionary = None
        if 'X-VRT-Token' in cookie_jar:
            xvrttoken_cookie = cookie_jar._cookies['.vrt.be']['/']['X-VRT-Token']
            token_dictionary = { xvrttoken_cookie.name : xvrttoken_cookie.value, 'expirationDate' : datetime.datetime.fromtimestamp(xvrttoken_cookie.expires).strftime('%Y-%m-%dT%H:%M:%S.%fZ')}
        return token_dictionary

    def reset_cookies(self):
        user_data_path = self._kodi_wrapper.get_userdata_path()
        ondemand = user_data_path + self._ONDEMAND_COOKIE
        live = user_data_path + self._LIVE_COOKIE
        xvrt = user_data_path + self._XVRT_TOKEN_COOKIE
        roaming = user_data_path + self._ROAMING_XVRTTOKEN_COOKIE
        self._kodi_wrapper.delete_path(ondemand)
        self._kodi_wrapper.delete_path(live)
        self._kodi_wrapper.delete_path(xvrt)
        self._kodi_wrapper.delete_path(roaming)

