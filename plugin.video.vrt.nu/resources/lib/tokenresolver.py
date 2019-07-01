# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' This module contains all functionality for VRT NU API authentication. '''

from __future__ import absolute_import, division, unicode_literals
import json
from resources.lib.helperobjects import Credentials

try:  # Python 3
    import http.cookiejar as cookielib
    from urllib.parse import urlencode, unquote
    from urllib.request import build_opener, install_opener, ProxyHandler, HTTPCookieProcessor, HTTPErrorProcessor, urlopen, Request
except ImportError:  # Python 2
    from urllib import urlencode
    from urllib2 import build_opener, install_opener, ProxyHandler, HTTPCookieProcessor, HTTPErrorProcessor, unquote, urlopen, Request
    import cookielib


class NoRedirection(HTTPErrorProcessor):
    ''' Prevent urllib from following http redirects '''

    def http_response(self, request, response):
        return response

    https_response = http_response


class TokenResolver:
    ''' Get, refresh and cache tokens for VRT NU API authentication. '''

    _API_KEY = '3_qhEcPa5JGFROVwu5SWKqJ4mVOIkwlFNMSKwzPDAh8QZOtHqu6L4nD5Q7lk0eXOOG'
    _LOGIN_URL = 'https://accounts.vrt.be/accounts.login'
    _VRT_LOGIN_URL = 'https://login.vrt.be/perform_login'
    _TOKEN_GATEWAY_URL = 'https://token.vrt.be'
    _USER_TOKEN_GATEWAY_URL = 'https://token.vrt.be/vrtnuinitlogin?provider=site&destination=https://www.vrt.be/vrtnu/'
    _ROAMING_TOKEN_GATEWAY_URL = 'https://token.vrt.be/vrtnuinitloginEU?destination=https://www.vrt.be/vrtnu/'

    def __init__(self, _kodi):
        ''' Initialize Token Resolver class '''
        self._kodi = _kodi
        self._proxies = _kodi.get_proxies()
        install_opener(build_opener(ProxyHandler(self._proxies)))

    def get_playertoken(self, token_url, token_variant=None, roaming=False):
        ''' Get cached or new playertoken, variants: live or ondemand '''
        token = None
        xvrttoken_variant = None
        if roaming:
            xvrttoken_variant = 'roaming'
            # Delete cached playertoken
            path = self._get_token_path('vrtPlayerToken', token_variant)
            self._kodi.delete_file(path)
        else:
            token = self._get_cached_token('vrtPlayerToken', token_variant)

        if token is None:
            if token_variant == 'ondemand' or roaming:
                xvrttoken = self.get_xvrttoken(token_variant=xvrttoken_variant)
                if xvrttoken is None:
                    return token
                cookie_value = 'X-VRT-Token=' + xvrttoken
                headers = {'Content-Type': 'application/json', 'Cookie': cookie_value}
            else:
                headers = {'Content-Type': 'application/json'}
            token = self._get_new_playertoken(token_url, headers, token_variant)

        return token

    def get_xvrttoken(self, token_variant=None):
        ''' Get cached, fresh or new X-VRT-Token, variants: None, user or roaming '''
        token = self._get_cached_token('X-VRT-Token', token_variant)
        if token is None:
            # Try to refresh if we have a cached refresh token (vrtlogin-rt)
            refresh_token = self._get_cached_token('vrtlogin-rt')
            if refresh_token:
                token = self._get_fresh_token(refresh_token, 'X-VRT-Token', token_variant='user')
            else:
                token = self._get_new_xvrttoken(token_variant)
        return token

    def _get_token_path(self, token_name, token_variant):
        ''' Create token path following predefined file naming rules '''
        prefix = token_variant + '_' if token_variant else ''
        token_path = self._kodi.get_userdata_path() + prefix + token_name.replace('-', '') + '.tkn'
        return token_path

    def _get_cached_token(self, token_name, token_variant=None):
        ''' Return a cached token '''
        cached_token = None
        path = self._get_token_path(token_name, token_variant)

        if self._kodi.check_if_path_exists(path):
            from datetime import datetime
            import dateutil.parser
            import dateutil.tz
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

    def _set_cached_token(self, token, token_variant=None):
        ''' Save token to cache'''
        token_name = list(token.keys())[0]
        path = self._get_token_path(token_name, token_variant)
        with self._kodi.open_file(path, 'w') as f:
            json.dump(token, f)

    def _get_new_playertoken(self, token_url, headers, token_variant=None):
        ''' Get new playertoken from VRT Token API '''
        self._kodi.log_notice('URL post: ' + unquote(token_url), 'Verbose')
        req = Request(token_url, data=b'', headers=headers)
        playertoken = json.load(urlopen(req))
        self._set_cached_token(playertoken, token_variant)
        return playertoken.get('vrtPlayerToken')

    def _get_new_xvrttoken(self, token_variant=None):
        ''' Get new X-VRT-Token from VRT NU website '''
        if token_variant == 'user':
            return self._get_new_user_xvrttoken()
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
            self._handle_login_error(logon_json, cred)
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
        try:  # Python 3
            setcookie_header = urlopen(req).info().get('Set-Cookie')
        except AttributeError:  # Python 2
            setcookie_header = urlopen(req).info().getheader('Set-Cookie')
        xvrttoken = TokenResolver._create_token_dictionary(setcookie_header)
        if token_variant == 'roaming':
            xvrttoken = self._get_roaming_xvrttoken(xvrttoken)
        if xvrttoken is not None:
            token = xvrttoken.get('X-VRT-Token')
            self._set_cached_token(xvrttoken, token_variant)
        return token

    def _get_new_user_xvrttoken(self):
        ''' Get new 'user' X-VRT-Token from VRT NU website '''
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
            self._handle_login_error(logon_json, cred)
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
        opener = build_opener(HTTPCookieProcessor(cookiejar), ProxyHandler(self._proxies))
        self._kodi.log_notice('URL get: ' + unquote(self._USER_TOKEN_GATEWAY_URL), 'Verbose')
        opener.open(self._USER_TOKEN_GATEWAY_URL)
        self._kodi.log_notice('URL post: ' + unquote(self._VRT_LOGIN_URL), 'Verbose')
        opener.open(self._VRT_LOGIN_URL, data=data)
        xvrttoken = TokenResolver._create_token_dictionary(cookiejar)
        refreshtoken = TokenResolver._create_token_dictionary(cookiejar, cookie_name='vrtlogin-rt')
        if xvrttoken is not None:
            token = xvrttoken.get('X-VRT-Token')
            self._set_cached_token(xvrttoken, token_variant='user')
        if refreshtoken is not None:
            self._set_cached_token(refreshtoken)
        return token

    def _get_fresh_token(self, refresh_token, token_name, token_variant=None):
        ''' Refresh an expired X-VRT-Token, vrtlogin-at or vrtlogin-rt token '''
        token = None
        refresh_url = self._TOKEN_GATEWAY_URL + '/refreshtoken'
        cookie_value = 'vrtlogin-rt=' + refresh_token
        headers = {'Cookie': cookie_value}
        cookiejar = cookielib.CookieJar()
        opener = build_opener(HTTPCookieProcessor(cookiejar), ProxyHandler(self._proxies))
        self._kodi.log_notice('URL get: ' + refresh_url, 'Verbose')
        req = Request(refresh_url, headers=headers)
        opener.open(req)
        token = TokenResolver._create_token_dictionary(cookiejar, token_name)
        self._set_cached_token(token, token_variant)
        return list(token.values())[0]

    def _handle_login_error(self, logon_json, cred):
        ''' Show localized login error messages in Kodi GUI'''
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
        ''' Get new 'roaming' X-VRT-Token from VRT NU website '''
        roaming_xvrttoken = None
        cookie_value = 'X-VRT-Token=' + xvrttoken.get('X-VRT-Token')
        headers = {'Cookie': cookie_value}
        opener = build_opener(NoRedirection, ProxyHandler(self._proxies))
        self._kodi.log_notice('URL get: ' + unquote(self._ROAMING_TOKEN_GATEWAY_URL), 'Verbose')
        req = Request(self._ROAMING_TOKEN_GATEWAY_URL, headers=headers)
        req_info = opener.open(req).info()
        try:  # Python 3
            cookie_value += '; state=' + req_info.get('Set-Cookie').split('state=')[1].split('; ')[0]
        except AttributeError:  # Python 2
            cookie_value += '; state=' + req_info.getheader('Set-Cookie').split('state=')[1].split('; ')[0]
        url = req_info.getheader('Location')
        self._kodi.log_notice('URL get: ' + unquote(url), 'Verbose')
        try:  # Python 3
            url = opener.open(url).info().get('Location')
        except AttributeError:  # Python 2
            url = opener.open(url).info().getheader('Location')
        headers = {'Cookie': cookie_value}
        if url is not None:
            self._kodi.log_notice('URL get: ' + unquote(url), 'Verbose')
            req = Request(url, headers=headers)
            try:  # Python 3
                setcookie_header = opener.open(req).info().get('Set-Cookie')
            except AttributeError:  # Python 2
                setcookie_header = opener.open(req).info().getheader('Set-Cookie')
            roaming_xvrttoken = TokenResolver._create_token_dictionary(setcookie_header)
        return roaming_xvrttoken

    @staticmethod
    def _create_token_dictionary(cookie_data, cookie_name='X-VRT-Token'):
        ''' Create a dictionary with token name and token expirationDate from a Python cookielib.CookieJar or urllib2 Set-Cookie http header '''
        token_dictionary = None
        if isinstance(cookie_data, cookielib.CookieJar):
            # Get token dict from cookiejar
            token_cookie = next(cookie for cookie in cookie_data if cookie.name == cookie_name)
            if token_cookie:
                from datetime import datetime
                token_dictionary = {
                    token_cookie.name: token_cookie.value,
                    'expirationDate': datetime.utcfromtimestamp(token_cookie.expires).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                }
        elif cookie_name in cookie_data:
            # Get token dict from http header
            import dateutil.parser
            cookie_data = cookie_data.split('X-VRT-Token=')[1].split('; ')
            token_dictionary = {
                cookie_name: cookie_data[0],
                'expirationDate': dateutil.parser.parse(cookie_data[2].strip('Expires=')).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            }
        return token_dictionary

    def delete_tokens(self):
        ''' Delete all cached tokens '''
        dirs, files = self._kodi.listdir(self._kodi.get_userdata_path())  # pylint: disable=unused-variable
        for item in files:
            if item.endswith('.tkn'):
                self._kodi.delete_file(self._kodi.get_userdata_path() + item)
