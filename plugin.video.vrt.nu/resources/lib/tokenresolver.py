# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""This module contains all functionality for VRT MAX API authentication."""

from __future__ import absolute_import, division, unicode_literals
from kodiutils import (addon_profile, delete, delete_cache, exists, get_cache, get_cache_dir, get_setting, open_url,
                       get_url_json, has_credentials, invalidate_caches, listdir,
                       localize, log, log_error, notification, ok_dialog,
                       open_settings, set_setting, update_cache)
from utils import from_unicode

try:  # Python 3
    import http.cookiejar as cookielib
    from urllib.error import HTTPError
    from urllib.parse import urlencode
except ImportError:  # Python 2
    from urllib import urlencode
    from urllib2 import HTTPError
    import cookielib


class TokenResolver:
    """Get, refresh and cache tokens for VRT MAX API authentication."""

    _API_KEY = '3_qhEcPa5JGFROVwu5SWKqJ4mVOIkwlFNMSKwzPDAh8QZOtHqu6L4nD5Q7lk0eXOOG'
    _LOGIN_URL = 'https://accounts.vrt.be/accounts.login'
    _VRT_LOGIN_URL = 'https://login.vrt.be/perform_login'
    _TOKEN_GATEWAY_URL = 'https://token.vrt.be'
    _USER_TOKEN_GATEWAY_URL = 'https://token.vrt.be/vrtnuinitlogin?provider=site&destination=https://www.vrt.be/vrtnu/'
    _ROAMING_TOKEN_GATEWAY_URL = 'https://token.vrt.be/vrtnuinitloginEU?destination=https://www.vrt.be/vrtnu/'
    _TOKEN_CACHE_DIR = 'tokens'

    def __init__(self):
        """Initialize Token Resolver class"""

    @staticmethod
    def _create_token_dictionary(cookie_data, cookie_name='X-VRT-Token'):
        """Create a dictionary with token name and token expirationDate from a Python cookielib.CookieJar or urllib2 Set-Cookie http header"""
        if cookie_data is None:
            return None
        if isinstance(cookie_data, cookielib.CookieJar):
            # Get token dict from cookiejar
            token_cookie = next((cookie for cookie in cookie_data if cookie.name == cookie_name), None)
            if token_cookie is None:
                return None
            from datetime import datetime
            token_dictionary = {
                token_cookie.name: token_cookie.value,
                'expirationDate': datetime.utcfromtimestamp(token_cookie.expires).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            }
        elif cookie_name in cookie_data:
            # Get token dict from http header
            import dateutil.parser
            import re
            cookie_data = cookie_data.split('X-VRT-Token=')[1].split('; ')
            expires_regex = re.compile(r'(?P<expires>[A-Za-z]{3}, \d{2} [A-Za-z]{3} \d{4} \d{2}:\d{2}:\d{2} [A-Za-z]{3})')
            expires = re.search(expires_regex, cookie_data[2]).group('expires')
            token_dictionary = {
                cookie_name: cookie_data[0],
                'expirationDate': dateutil.parser.parse(expires).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            }
        else:
            return None
        return token_dictionary

    @staticmethod
    def _get_token_filename(name, variant=None):
        """Create token filename following predefined file naming rules"""
        prefix = variant + '_' if variant else ''
        token_filename = prefix + name.replace('-', '') + '.tkn'
        return token_filename

    def _get_login_json(self):
        """Get login json"""
        payload = dict(
            loginID=from_unicode(get_setting('username')),
            password=from_unicode(get_setting('password')),
            sessionExpiration='-2',
            APIKey=self._API_KEY,
            targetEnv='jssdk',
        )
        data = urlencode(payload).encode()
        return get_url_json(self._LOGIN_URL, data=data, fail={})

    def login(self, refresh=False, token_variant=None):
        """Kodi GUI login flow"""
        # If no credentials, ask user for credentials
        if not has_credentials():
            if refresh:
                return open_settings()
            open_settings()
            if not self._credentials_changed():
                return None

        # Check credentials
        login_json = self._get_login_json()

        # Bad credentials
        while login_json.get('errorCode') != 0:
            # Show localized login error messages in Kodi GUI
            message = login_json.get('errorDetails')
            if not message:
                message = login_json or localize(30951)  # Login failed!
            log_error('Login failed: {msg}', msg=message)
            if message == 'invalid loginID or password':
                message = localize(30953)  # Invalid login!
            elif message == 'loginID must be provided':
                message = localize(30955)  # Please fill in username
            elif message == 'Missing required parameter: password':
                message = localize(30956)  # Please fill in password
            ok_dialog(heading=localize(30951), message=message)  # Login failed!
            if refresh:
                return open_settings()
            open_settings()
            if not self._credentials_changed():
                return None
            login_json = self._get_login_json()

        # Get new token
        return self._get_new_token('X-VRT-Token', token_variant, login_json)

    def _get_new_token(self, name, variant=None, url=None, roaming=False, login_json=None):
        """Return a new token"""

        if name == 'X-VRT-Token':
            if variant == 'user':
                usertoken = self._get_usertoken('X-VRT-Token', login_json=login_json)
                if usertoken:
                    return usertoken
                return self.login(token_variant='user')
            if variant == 'roaming':
                return self._get_roaming_xvrttoken()

        if name == 'vrtPlayerToken':
            return self._get_playertoken(variant, url, roaming)

        if name in ('vrtlogin-at', 'vrtlogin-expiry', 'vrtlogin-rt', 'SESSION', 'OIDCXSRF', 'state'):
            return self._get_usertoken(name, roaming=roaming)

        return None

    def _get_usertoken(self, name=None, login_json=None, roaming=False):
        """Get a user X-VRT-Token, vrtlogin-at, vrtlogin-expiry, vrtlogin-rt, SESSION, OIDCXSRF or state token"""
        if not login_json:
            login_json = self._get_login_json()
        cookiejar = cookielib.CookieJar()
        open_url(self._USER_TOKEN_GATEWAY_URL, cookiejar=cookiejar)
        xsrf = next((cookie for cookie in cookiejar if cookie.name == 'OIDCXSRF'), None)
        if xsrf is None:
            return None
        payload = dict(
            UID=login_json.get('UID'),
            UIDSignature=login_json.get('UIDSignature'),
            signatureTimestamp=login_json.get('signatureTimestamp'),
            client_id='vrtnu-site',
            _csrf=xsrf.value
        )
        data = urlencode(payload).encode()
        response = open_url(self._VRT_LOGIN_URL, data=data, cookiejar=cookiejar)
        if response is None:
            return None

        destination = response.geturl()
        usertoken = TokenResolver._create_token_dictionary(cookiejar, name)
        if not usertoken and not destination.startswith('https://www.vrt.be/vrtmax'):
            if roaming is False:
                ok_dialog(heading=localize(30970), message=localize(30972))
            return None

        # Cache additional tokens for later use
        refreshtoken = TokenResolver._create_token_dictionary(cookiejar, cookie_name='vrtlogin-rt')
        accesstoken = TokenResolver._create_token_dictionary(cookiejar, cookie_name='vrtlogin-at')
        if refreshtoken is not None:
            from json import dumps
            cache_file = self._get_token_filename('vrtlogin-rt')
            update_cache(cache_file, dumps(refreshtoken), self._TOKEN_CACHE_DIR)
        if accesstoken is not None:
            from json import dumps
            cache_file = self._get_token_filename('vrtlogin-at')
            update_cache(cache_file, dumps(accesstoken), self._TOKEN_CACHE_DIR)
        return usertoken

    def _get_roaming_xvrttoken(self):
        """Get a X-VRT-Token for roaming"""
        vrtlogin_at = self.get_token('vrtlogin-at', roaming=True)
        if vrtlogin_at is None:
            return None
        cookie_value = 'vrtlogin-at=' + vrtlogin_at
        headers = {'Cookie': cookie_value}
        response = open_url(self._ROAMING_TOKEN_GATEWAY_URL, headers=headers, follow_redirects=False)
        if response is None:
            return None
        req_info = response.info()
        cookie_value += '; state=' + req_info.get('Set-Cookie').split('state=')[1].split('; ')[0]
        response = open_url(req_info.get('Location'), follow_redirects=False)
        if response is None:
            return None
        url = response.info().get('Location')
        headers = {'Cookie': cookie_value}
        if url is None:
            return None
        response = open_url(url, headers=headers, follow_redirects=False)
        if response is None:
            return None
        setcookie_header = response.info().get('Set-Cookie')
        return TokenResolver._create_token_dictionary(setcookie_header)

    def get_token(self, name, variant=None, url=None, roaming=False):
        """Get a token"""
        # Try to get a cached token
        if not roaming:
            cache_file = self._get_token_filename(name, variant)
            token = get_cache(cache_file, cache_dir=self._TOKEN_CACHE_DIR)
            if token:
                return token.get(name)
        # Try to refresh a token
        if variant != 'roaming' and name in ('X-VRT-Token', 'vrtlogin-at', 'vrtlogin-rt'):
            cache_file = self._get_token_filename('vrtlogin-rt')
            refresh_token = get_cache(cache_file, cache_dir=self._TOKEN_CACHE_DIR)
            if refresh_token:
                token = self._get_fresh_token(refresh_token.get('vrtlogin-rt'), name)
                if token:
                    # Save token to cache
                    from json import dumps
                    cache_file = self._get_token_filename(list(token.keys())[0], variant)
                    update_cache(cache_file, dumps(token), self._TOKEN_CACHE_DIR)
                    return token.get(name)
        # Get a new token
        token = self._get_new_token(name, variant, url, roaming)
        if token:
            # Save token to cache
            from json import dumps
            cache_file = self._get_token_filename(list(token.keys())[0], variant)
            update_cache(cache_file, dumps(token), self._TOKEN_CACHE_DIR)
            return token.get(name)
        return None

    def _get_fresh_token(self, refresh_token, name):
        """Refresh an expired X-VRT-Token, vrtlogin-at or vrtlogin-rt token"""
        refresh_url = self._TOKEN_GATEWAY_URL + '/refreshtoken?legacy=true'
        cookie_value = 'vrtlogin-rt=' + refresh_token
        headers = {'Cookie': cookie_value}
        cookiejar = cookielib.CookieJar()
        try:
            open_url(refresh_url, headers=headers, cookiejar=cookiejar, raise_errors=[401])
        except HTTPError:
            ok_dialog(heading=localize(30970), message=localize(30971))
        return TokenResolver._create_token_dictionary(cookiejar, name)

    def _get_playertoken(self, variant, url, roaming=False):
        """Get a vrtPlayerToken"""
        from json import dumps
        headers = {'Content-Type': 'application/json'}
        data = b''
        if roaming or variant == 'ondemand':
            if roaming:
                # Delete cached vrtPlayerToken
                cache_file = self._get_token_filename('vrtPlayerToken', variant)
                delete_cache(cache_file, self._TOKEN_CACHE_DIR)
                xvrttoken = self.get_token('X-VRT-Token', 'roaming')
            elif variant == 'ondemand':
                # We need a user X-VRT-Token because the birthdate in the VRT MAX profile is checked when watching age restricted content
                xvrttoken = self.get_token('X-VRT-Token', 'user')
            if xvrttoken is None:
                return None
            player_info = self._generate_playerinfo()
            payload = dict(
                identityToken=xvrttoken,
                playerInfo=player_info
            )
            data = dumps(payload).encode()
        playertoken = get_url_json(url=url, headers=headers, data=data)
        if playertoken:
            return playertoken
        return None

    @staticmethod
    def _generate_playerinfo():
        import time
        from json import dumps
        import base64
        import hmac
        import hashlib
        import re

        playerinfo = None
        data = None

        # Get data from player javascript
        player_url = 'https://player.vrt.be/vrtnu/js/main.js'
        response = open_url(player_url)
        if response:
            data = response.read().decode('utf-8')

        if data:
            # Extract JWT key id and secret
            crypt_rx = re.compile(r'atob\(\"(==[A-Za-z0-9+/]*)\"')
            crypt_data = re.findall(crypt_rx, data)
            if not crypt_data:
                return playerinfo

            kid_source = crypt_data[0]
            secret_source = crypt_data[-1]
            kid = base64.b64decode(kid_source[::-1]).decode('utf-8')
            secret = base64.b64decode(secret_source[::-1]).decode('utf-8')

            # Extract player version
            player_version = '2.4.1'
            pv_rx = re.compile(r'playerVersion:\"(\S*)\"')
            match = re.search(pv_rx, data)
            if match:
                player_version = match.group(1)

            # Generate JWT
            segments = []
            header = dict(
                alg='HS256',
                kid=kid
            )
            payload = dict(
                exp=time.time() + 1000,
                platform='desktop',
                app=dict(
                    type='browser',
                    name='Firefox',
                    version='102.0'
                ),
                device='undefined (undefined)',
                os=dict(
                    name='Linux',
                    version='x86_64'
                ),
                player=dict(
                    name='VRT web player',
                    version=player_version
                )
            )
            json_header = dumps(header).encode()
            json_payload = dumps(payload).encode()
            segments.append(base64.urlsafe_b64encode(json_header).decode('utf-8').replace('=', ''))
            segments.append(base64.urlsafe_b64encode(json_payload).decode('utf-8').replace('=', ''))
            signing_input = '.'.join(segments).encode()
            signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
            segments.append(base64.urlsafe_b64encode(signature).decode('utf-8').replace('=', ''))
            playerinfo = '.'.join(segments)
        return playerinfo

    def delete_tokens(self):
        """Delete all cached tokens"""
        # Remove old tokens
        # FIXME: Deprecate and simplify this part in a future version
        _, files = listdir(addon_profile())
        token_files = [item for item in files if item.endswith('.tkn')]
        # Empty userdata/tokens/ directory
        tokens_path = get_cache_dir(self._TOKEN_CACHE_DIR)
        if exists(tokens_path):
            _, files = listdir(tokens_path)
            token_files += ['tokens/' + item for item in files]
        if token_files:
            for item in token_files:
                delete(addon_profile() + item)
            notification(message=localize(30985))

    def refresh_login(self):
        """Refresh login if necessary"""

        if self._credentials_changed() and has_credentials():
            log(2, 'Credentials have changed, cleaning up userdata')
            self.cleanup_userdata()

            # Refresh login
            log(2, 'Refresh login')
            self.login(refresh=True, token_variant='user')

    def cleanup_userdata(self):
        """Cleanup userdata"""

        # Delete token cache
        self.delete_tokens()

        # Delete user-related caches
        invalidate_caches(
            'continue-*.json', 'favorites.json', 'my-offline-*.json', 'my-recent-*.json',
            'resume_points.json', 'watchlater.json', 'watchlater-*.json')

    def logged_in(self):
        """Whether there is an active login"""
        cache_file = self._get_token_filename('X-VRT-Token', 'user')
        return bool(get_cache(cache_file, cache_dir=self._TOKEN_CACHE_DIR))

    @staticmethod
    def _credentials_changed():
        """Check if credentials have changed"""
        old_hash = get_setting('credentials_hash')
        username = get_setting('username')
        password = get_setting('password')
        new_hash = ''
        if username or password:
            from hashlib import md5
            new_hash = md5((username + password).encode('utf-8')).hexdigest()
        if new_hash != old_hash:
            set_setting('credentials_hash', new_hash)
            return True
        return False
