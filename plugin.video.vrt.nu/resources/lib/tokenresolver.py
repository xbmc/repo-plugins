# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, unicode_literals
from resources.lib.helperobjects import Credentials

try:
    from urllib.parse import urlencode, unquote
    from urllib.request import build_opener, install_opener, ProxyHandler, HTTPCookieProcessor, HTTPErrorProcessor, urlopen, Request
except ImportError:
    from urllib import urlencode
    from urllib2 import build_opener, install_opener, ProxyHandler, HTTPCookieProcessor, HTTPErrorProcessor, unquote, urlopen, Request


class NoRedirection(HTTPErrorProcessor):

    def http_response(self, request, response):
        return response

    https_response = http_response


class TokenResolver:

    _API_KEY = '3_qhEcPa5JGFROVwu5SWKqJ4mVOIkwlFNMSKwzPDAh8QZOtHqu6L4nD5Q7lk0eXOOG'
    _LOGIN_URL = 'https://accounts.vrt.be/accounts.login'
    _TOKEN_GATEWAY_URL = 'https://token.vrt.be'
    _VRT_LOGIN_URL = 'https://login.vrt.be/perform_login'
    _ONDEMAND_COOKIE = 'ondemand_vrtPlayerToken'
    _LIVE_COOKIE = 'live_vrtPlayerToken'
    _ROAMING_XVRTTOKEN_COOKIE = 'roaming_XVRTToken'
    _FAV_TOKEN_GATEWAY_URL = 'https://token.vrt.be/vrtnuinitlogin?provider=site&destination=https://www.vrt.be/vrtnu/'
    _FAV_XVRTTOKEN_COOKIE = 'user_XVRTToken'
    _XVRT_TOKEN_COOKIE = 'XVRTToken'

    def __init__(self, _kodi):
        self._kodi = _kodi
        self._proxies = _kodi.get_proxies()
        install_opener(build_opener(ProxyHandler(self._proxies)))

    def get_ondemand_playertoken(self, token_url, xvrttoken):
        token_path = self._kodi.get_userdata_path() + self._ONDEMAND_COOKIE
        token = self._get_cached_token(token_path, 'vrtPlayerToken')

        if xvrttoken and token is None:
            cookie_value = 'X-VRT-Token=' + xvrttoken
            headers = {'Content-Type': 'application/json', 'Cookie': cookie_value}
            token = self._get_new_playertoken(token_path, token_url, headers)
        return token

    def get_live_playertoken(self, token_url, xvrttoken):
        token_path = self._kodi.get_userdata_path() + self._LIVE_COOKIE
        token = self._get_cached_token(token_path, 'vrtPlayerToken')
        if token is None:
            if xvrttoken is None:
                headers = {'Content-Type': 'application/json'}
            else:
                cookie_value = 'X-VRT-Token=' + xvrttoken
                headers = {'Content-Type': 'application/json', 'Cookie': cookie_value}
            token = self._get_new_playertoken(token_path, token_url, headers)
        return token

    def get_xvrttoken(self, get_roaming_token=False):
        token_filename = self._ROAMING_XVRTTOKEN_COOKIE if get_roaming_token else self._XVRT_TOKEN_COOKIE
        token_path = self._kodi.get_userdata_path() + token_filename
        token = self._get_cached_token(token_path, 'X-VRT-Token')

        if token is None:
            token = self._get_new_xvrttoken(token_path, get_roaming_token)
        return token

    def get_fav_xvrttoken(self):
        token_path = self._kodi.get_userdata_path() + self._FAV_XVRTTOKEN_COOKIE
        token = self._get_cached_token(token_path, 'X-VRT-Token')

        if token is None:
            token = self._get_fav_xvrttoken(token_path)
        return token

    def _get_new_playertoken(self, path, token_url, headers):
        import json
        self._kodi.log_notice('URL post: ' + unquote(token_url), 'Verbose')
        req = Request(token_url, data=b'', headers=headers)
        playertoken = json.load(urlopen(req))
        with self._kodi.open_file(path, 'w') as f:
            json.dump(playertoken, f)
        return playertoken.get('vrtPlayerToken')

    def _get_cached_token(self, path, token_name):
        cached_token = None

        if self._kodi.check_if_path_exists(path):
            from datetime import datetime
            import dateutil.parser
            import dateutil.tz
            import json
            with self._kodi.open_file(path) as f:
                token = json.load(f)
            now = datetime.now(dateutil.tz.tzlocal())
            exp = dateutil.parser.parse(token.get('expirationDate'))
            if exp > now:
                self._kodi.log_notice("Got cached token '%s'" % path, 'Verbose')
                cached_token = token.get(token_name)
            else:
                self._kodi.log_notice("Cached token '%s' deleted" % path, 'Verbose')
                self._kodi.delete_file(path)
        return cached_token

    def _get_new_xvrttoken(self, path, get_roaming_token):
        import json

        cred = Credentials(self._kodi)
        if not cred.are_filled_in():
            self._kodi.open_settings()
            cred.reload()

        payload = dict(
            loginID=cred.username,
            password=cred.password,
            sessionExpiration='-1',
            APIKey=self._API_KEY,
            targetEnv='jssdk',
        )
        data = urlencode(payload).encode('utf8')
        self._kodi.log_notice('URL post: ' + unquote(self._LOGIN_URL), 'Verbose')
        req = Request(self._LOGIN_URL, data=data)
        logon_json = json.load(urlopen(req))
        token = None

        if logon_json.get('errorCode') != 0:
            self._handle_error(logon_json, cred)
            return None

        login_token = logon_json.get('sessionInfo', dict()).get('login_token')
        login_cookie = 'glt_%s=%s' % (self._API_KEY, login_token)
        payload = dict(
            uid=logon_json.get('UID'),
            uidsig=logon_json.get('UIDSignature'),
            ts=logon_json.get('signatureTimestamp'),
            email=cred.username,
        )
        data = json.dumps(payload).encode('utf8')
        headers = {'Content-Type': 'application/json', 'Cookie': login_cookie}
        self._kodi.log_notice('URL post: ' + unquote(self._TOKEN_GATEWAY_URL), 'Verbose')
        req = Request(self._TOKEN_GATEWAY_URL, data=data, headers=headers)
        try:  # Python 2
            cookie_data = urlopen(req).info().getheader('Set-Cookie').split('X-VRT-Token=')[1].split('; ')
        except AttributeError:
            cookie_data = urlopen(req).info().get('Set-Cookie').split('X-VRT-Token=')[1].split('; ')
        xvrttoken = TokenResolver._create_token_dictionary_from_urllib(cookie_data)
        if get_roaming_token:
            xvrttoken = self._get_roaming_xvrttoken(xvrttoken)
        if xvrttoken is not None:
            token = xvrttoken.get('X-VRT-Token')
            with self._kodi.open_file(path, 'w') as f:
                json.dump(xvrttoken, f)
        return token

    def _get_fav_xvrttoken(self, path):
        try:
            import http.cookiejar as cookielib
        except ImportError:
            import cookielib
        import json

        cred = Credentials(self._kodi)
        if not cred.are_filled_in():
            self._kodi.open_settings()
            cred.reload()

        payload = dict(
            loginID=cred.username,
            password=cred.password,
            sessionExpiration='-1',
            APIKey=self._API_KEY,
            targetEnv='jssdk',
        )
        data = urlencode(payload).encode('utf8')
        self._kodi.log_notice('URL post: ' + unquote(self._LOGIN_URL), 'Verbose')
        req = Request(self._LOGIN_URL, data=data)
        logon_json = json.load(urlopen(req))
        token = None

        if logon_json.get('errorCode') != 0:
            self._handle_error(logon_json, cred)
            return None

        payload = dict(
            UID=logon_json.get('UID'),
            UIDSignature=logon_json.get('UIDSignature'),
            signatureTimestamp=logon_json.get('signatureTimestamp'),
            client_id='vrtnu-site',
            submit='submit',
        )
        data = urlencode(payload).encode('utf8')
        cookiejar = cookielib.CookieJar()
        opener = build_opener(HTTPCookieProcessor(cookiejar))
        self._kodi.log_notice('URL get: ' + unquote(self._FAV_TOKEN_GATEWAY_URL), 'Verbose')
        opener.open(self._FAV_TOKEN_GATEWAY_URL)
        self._kodi.log_notice('URL post: ' + unquote(self._VRT_LOGIN_URL), 'Verbose')
        opener.open(self._VRT_LOGIN_URL, data=data)
        xvrttoken = TokenResolver._create_token_dictionary(cookiejar)
        if xvrttoken is not None:
            token = xvrttoken.get('X-VRT-Token')
            with self._kodi.open_file(path, 'w') as f:
                json.dump(xvrttoken, f)
        return token

    def _handle_error(self, logon_json, cred):
        message = logon_json.get('errorDetails')
        if message == 'invalid loginID or password':
            cred.reset()
            message = self._kodi.localize(30952)  # Invalid login!
        elif message == 'loginID must be provided':
            message = self._kodi.localize(30955)  # Please fill in username
        elif message == 'Missing required parameter: password':
            message = self._kodi.localize(30956)  # Please fill in password
        self._kodi.show_ok_dialog(heading=self._kodi.localize(30951), message=message)  # Login failed!
        self._kodi.end_of_directory()

    def _get_roaming_xvrttoken(self, xvrttoken):
        roaming_xvrttoken = None
        url = 'https://token.vrt.be/vrtnuinitloginEU?destination=https://www.vrt.be/vrtnu/'
        cookie_value = 'X-VRT-Token=' + xvrttoken.get('X-VRT-Token')
        headers = {'Cookie': cookie_value}
        opener = build_opener(NoRedirection, ProxyHandler(self._proxies))
        self._kodi.log_notice('URL get: ' + unquote(url), 'Verbose')
        req = Request(url, headers=headers)
        req_info = opener.open(req).info()
        try:  # Python 2
            cookie_value += '; state=' + req_info.getheader('Set-Cookie').split('state=')[1].split('; ')[0]
        except AttributeError:  # Python 3
            cookie_value += '; state=' + req_info.get('Set-Cookie').split('state=')[1].split('; ')[0]
        url = req_info.getheader('Location')
        self._kodi.log_notice('URL get: ' + unquote(url), 'Verbose')
        try:  # Python 2
            url = opener.open(url).info().getheader('Location')
        except AttributeError:  # Python 3
            url = opener.open(url).info().get('Location')
        headers = {'Cookie': cookie_value}
        if url is not None:
            self._kodi.log_notice('URL get: ' + unquote(url), 'Verbose')
            req = Request(url, headers=headers)
            try:  # Python 2
                cookie_data = opener.open(req).info().getheader('Set-Cookie').split('X-VRT-Token=')[1].split('; ')
            except AttributeError:  # Python 3
                cookie_data = opener.open(req).info().get('Set-Cookie').split('X-VRT-Token=')[1].split('; ')
            roaming_xvrttoken = TokenResolver._create_token_dictionary_from_urllib(cookie_data)
        return roaming_xvrttoken

    @staticmethod
    def _create_token_dictionary(cookie_jar):
        token_dictionary = None
        # Get cookie from cookiejar
        xvrttoken_cookie = next(cookie for cookie in cookie_jar if cookie.name == 'X-VRT-Token')
        if xvrttoken_cookie is not None:
            from datetime import datetime
            token_dictionary = {
                xvrttoken_cookie.name: xvrttoken_cookie.value,
                'expirationDate': datetime.utcfromtimestamp(xvrttoken_cookie.expires).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            }
        return token_dictionary

    @staticmethod
    def _create_token_dictionary_from_urllib(cookie_data):
        import dateutil.parser
        token_dictionary = {
            'X-VRT-Token': cookie_data[0],
            'expirationDate': dateutil.parser.parse(cookie_data[2].strip('Expires=')).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        }
        return token_dictionary

    def reset_cookies(self):
        user_data_path = self._kodi.get_userdata_path()
        self._kodi.delete_file(user_data_path + self._ONDEMAND_COOKIE)
        self._kodi.delete_file(user_data_path + self._LIVE_COOKIE)
        self._kodi.delete_file(user_data_path + self._XVRT_TOKEN_COOKIE)
        self._kodi.delete_file(user_data_path + self._ROAMING_XVRTTOKEN_COOKIE)
        self._kodi.delete_file(user_data_path + self._FAV_XVRTTOKEN_COOKIE)
