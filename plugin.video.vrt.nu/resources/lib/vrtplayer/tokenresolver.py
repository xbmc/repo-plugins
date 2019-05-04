# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, unicode_literals
from resources.lib.helperobjects import helperobjects

try:
    from urllib.parse import urlencode
    from urllib.request import build_opener, install_opener, ProxyHandler, HTTPErrorProcessor, urlopen, Request
except ImportError:
    from urllib2 import build_opener, install_opener, ProxyHandler, HTTPErrorProcessor, urlopen, Request
    from urllib import urlencode  # pylint: disable=ungrouped-imports


class NoRedirection(HTTPErrorProcessor):

    def http_response(self, request, response):
        return response

    https_response = http_response


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
        self._proxies = self._kodi_wrapper.get_proxies()
        install_opener(build_opener(ProxyHandler(self._proxies)))

    def get_ondemand_playertoken(self, token_url, xvrttoken):
        token_path = self._kodi_wrapper.get_userdata_path() + self._ONDEMAND_COOKIE
        token = self._get_cached_token(token_path, 'vrtPlayerToken')

        if xvrttoken and token is None:
            cookie_value = 'X-VRT-Token=' + xvrttoken
            headers = {'Content-Type': 'application/json', 'Cookie': cookie_value}
            token = self._get_new_playertoken(token_path, token_url, headers)
        return token

    def get_live_playertoken(self, token_url, xvrttoken):
        token_path = self._kodi_wrapper.get_userdata_path() + self._LIVE_COOKIE
        token = self._get_cached_token(token_path, 'vrtPlayerToken')
        if token is None:
            if xvrttoken is not None:
                cookie_value = 'X-VRT-Token=' + xvrttoken
                headers = {'Content-Type': 'application/json', 'Cookie': cookie_value}
            else:
                headers = {'Content-Type': 'application/json'}
            token = self._get_new_playertoken(token_path, token_url, headers)
        return token

    def get_xvrttoken(self, get_roaming_token=False):
        token_filename = self._ROAMING_XVRTTOKEN_COOKIE if get_roaming_token else self._XVRT_TOKEN_COOKIE
        token_path = self._kodi_wrapper.get_userdata_path() + token_filename
        token = self._get_cached_token(token_path, 'X-VRT-Token')

        if token is None:
            token = self._get_new_xvrttoken(token_path, get_roaming_token)
        return token

    @staticmethod
    def get_cookie_from_cookiejar(cookiename, cookiejar):
        for cookie in cookiejar:
            if cookie.name == cookiename:
                yield cookie

    def _get_new_playertoken(self, path, token_url, headers):
        import json
        req = Request(token_url, data='', headers=headers)
        playertoken = json.loads(urlopen(req).read())
        json.dump(playertoken, open(path, 'w'))
        return playertoken.get('vrtPlayerToken')

    def _get_cached_token(self, path, token_name):
        cached_token = None

        if self._kodi_wrapper.check_if_path_exists(path):
            from datetime import datetime
            import dateutil.parser
            import dateutil.tz
            import json
            token = json.loads(open(path, 'r').read())
            now = datetime.now(dateutil.tz.tzlocal())
            exp = dateutil.parser.parse(token.get('expirationDate'))
            if exp > now:
                self._kodi_wrapper.log_notice('Got cached token')
                cached_token = token.get(token_name)
            else:
                self._kodi_wrapper.log_notice('Cached token deleted')
                self._kodi_wrapper.delete_path(path)
        return cached_token

    def _get_new_xvrttoken(self, path, get_roaming_token):
        import json
        cred = helperobjects.Credentials(self._kodi_wrapper)
        if not cred.are_filled_in():
            self._kodi_wrapper.open_settings()
            cred.reload()
        data = dict(
            loginID=cred.username,
            password=cred.password,
            sessionExpiration='-1',
            APIKey=self._API_KEY,
            targetEnv='jssdk',
        )
        req = Request(self._LOGIN_URL, data=urlencode(data))
        logon_json = json.loads(urlopen(req).read())
        token = None
        if logon_json.get('errorCode') == 0:
            login_token = logon_json.get('sessionInfo', dict()).get('login_token')
            login_cookie = 'glt_%s=%s' % (self._API_KEY, login_token)
            payload = dict(
                uid=logon_json.get('UID'),
                uidsig=logon_json.get('UIDSignature'),
                ts=logon_json.get('signatureTimestamp'),
                email=cred.username,
            )
            headers = {'Content-Type': 'application/json', 'Cookie': login_cookie}
            req = Request(self._TOKEN_GATEWAY_URL, json.dumps(payload), headers)
            cookie_data = urlopen(req).info().getheader('Set-Cookie').split('X-VRT-Token=')[1].split('; ')
            xvrttoken = TokenResolver._create_token_dictionary_from_urllib(cookie_data)
            if get_roaming_token:
                xvrttoken = self._get_roaming_xvrttoken(xvrttoken)
            if xvrttoken is not None:
                token = xvrttoken.get('X-VRT-Token')
                json.dump(xvrttoken, open(path, 'w'))
        else:
            self._handle_error(logon_json, cred)
        return token

    def _handle_error(self, logon_json, cred):
        error_message = logon_json.get('errorDetails')
        title = self._kodi_wrapper.get_localized_string(30051)
        if error_message == 'invalid loginID or password':
            cred.reset()
            message = self._kodi_wrapper.get_localized_string(30052)
        elif error_message == 'loginID must be provided':
            message = self._kodi_wrapper.get_localized_string(30055)
        elif error_message == 'Missing required parameter: password':
            message = self._kodi_wrapper.get_localized_string(30056)
        else:
            message = error_message
        self._kodi_wrapper.show_ok_dialog(title, message)

    def _get_roaming_xvrttoken(self, xvrttoken):
        roaming_xvrttoken = None
        url = 'https://token.vrt.be/vrtnuinitloginEU?destination=https://www.vrt.be/vrtnu/'
        cookie_value = 'X-VRT-Token=' + xvrttoken.get('X-VRT-Token')
        headers = {'Cookie': cookie_value}
        opener = build_opener(NoRedirection, ProxyHandler(self._proxies))
        req = Request(url, headers=headers)
        req_info = opener.open(req).info()
        cookie_value += '; state=' + req_info.getheader('Set-Cookie').split('state=')[1].split('; ')[0]
        url = req_info.getheader('Location')
        url = opener.open(url).info().getheader('Location')
        headers = {'Cookie': cookie_value}
        if url is not None:
            req = Request(url, headers=headers)
            cookie_data = opener.open(req).info().getheader('Set-Cookie').split('X-VRT-Token=')[1].split('; ')
            roaming_xvrttoken = TokenResolver._create_token_dictionary_from_urllib(cookie_data)
        return roaming_xvrttoken

    @staticmethod
    def _create_token_dictionary(cookie_jar):
        token_dictionary = None
        xvrttoken_cookie = next(TokenResolver.get_cookie_from_cookiejar('X-VRT-Token', cookie_jar))
        if xvrttoken_cookie is not None:
            from datetime import datetime
            token_dictionary = {
                xvrttoken_cookie.name: xvrttoken_cookie.value,
                'expirationDate': datetime.utcfromtimestamp(xvrttoken_cookie.expires).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            }
        return token_dictionary

    @staticmethod
    def _create_token_dictionary_from_urllib(cookie_data):
        token_dictionary = None
        from datetime import datetime
        import time
        token_dictionary = {
            'X-VRT-Token': cookie_data[0],
            'expirationDate': datetime(*time.strptime(cookie_data[2].strip('Expires='), '%a, %d %B %Y %H:%M:%S GMT')[0:6]).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        }
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
