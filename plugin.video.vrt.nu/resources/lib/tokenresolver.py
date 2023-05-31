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
    from urllib.error import HTTPError
except ImportError:  # Python 2
    from urllib2 import HTTPError


class TokenResolver:
    """Get, refresh and cache tokens for VRT MAX API authentication."""

    _SSO_INIT_URL = 'https://www.vrt.be/vrtnu/sso/login?scope=openid,mid'
    _SSO_LOGIN_URL = 'https://login.vrt.be/perform_login'
    _SSO_REFRESH_URL = 'https://www.vrt.be/vrtnu/sso/refresh'
    _PLAYERTOKEN_URL = 'https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v2/tokens'
    _TOKEN_CACHE_DIR = 'tokens'

    def __init__(self):
        """Initialize Token Resolver class"""
        self.token_dict = {}

    @staticmethod
    def _get_token_filename(name, variant=None):
        """Create token filename following predefined file naming rules"""
        prefix = variant + '_' if variant else ''
        token_filename = prefix + name.replace('-', '') + '.tkn'
        return token_filename

    def _set_cached_token(self, token, variant=None):
        """Save token to cache"""
        if not token:
            return

        # Get token name
        keys = list(token.keys())
        keys.remove('expirationDate')
        name = keys[0]

        # Save to memory
        self.token_dict[name] = token

        # Save to disk
        cache_file = self._get_token_filename(name, variant)
        from json import dumps
        update_cache(cache_file, dumps(token), self._TOKEN_CACHE_DIR)

    def _get_cached_token(self, name, variant=None):
        """Return a cached token"""

        # Get from memory
        if self.token_dict.get(name):
            expiration_date = self.token_dict.get(name).get('expirationDate', None)
            if expiration_date:
                from datetime import datetime
                import dateutil.parser
                import dateutil.tz
                now = datetime.now(dateutil.tz.tzlocal())
                exp = dateutil.parser.parse(expiration_date)
                if exp <= now:
                    log(2, "Memory token expired: '{name}'", name=name)
                    return None
            return self.token_dict.get(name)

        # Get from disk
        cache_file = self._get_token_filename(name, variant)
        token = get_cache(cache_file, cache_dir=self._TOKEN_CACHE_DIR)
        if token:
            return token
        return None

    def _extract_tokens(self, response):
        """Extract tokens from http response"""
        tokens = []
        try:  # Python 3
            cookie_data = response.info().get_all('Set-Cookie')
        except AttributeError:  # Python 2
            cookie_data = response.info().getheaders('Set-Cookie')
        for cookie in cookie_data:
            # Create token dictionary
            token = self._create_token_dictionary(cookie)

            # Cache token
            self._set_cached_token(token)
            # Store token
            tokens.append(token)
        return tokens

    @staticmethod
    def _create_token_dictionary(cookie_data):
        """Create a dictionary with token name and token expirationDate from a Set-Cookie http header"""
        if cookie_data is None:
            return None

        # Get token dict from http header
        import dateutil.parser
        cookie_name = cookie_data.split('=')[0]
        cookie_info = cookie_data.split(cookie_name + '=')[1].split('; ')
        expires = None
        if 'Expires' in cookie_info[1]:
            expires = cookie_info[1].split('=')[1].split(' (')[0]
        elif expires is None and 'Max-Age' in cookie_info[1]:
            from datetime import datetime, timedelta
            expires = (datetime.utcnow() + timedelta(seconds=int(cookie_info[1].split('=')[1]))).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        else:
            expires = 'Mon, 1 Jan 2052 06:00:00 GMT'

        if cookie_info[0] == 'deleted':
            return None

        token_dictionary = {
            cookie_name: cookie_info[0],
            'expirationDate': dateutil.parser.parse(expires).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        }
        return token_dictionary

    def _get_login_info(self):
        """Get login info"""
        # Init login
        response = open_url(self._SSO_INIT_URL, follow_redirects=False)
        self._extract_tokens(response)

        # Authorize
        response = open_url(response.info().get('Location'))
        self._extract_tokens(response)

        # Perform login
        oidcxsrf = self.get_token('OIDCXSRF')
        headers = {
            'Content-Type': 'application/json',
            'OIDCXSRF': oidcxsrf,
            'Cookie': 'SESSION={}; OIDCXSRF={}'.format(self.get_token('SESSION'), oidcxsrf),
        }
        payload = {
            'clientId': 'vrtnu-site',
            'loginID': from_unicode(get_setting('username')),
            'password': from_unicode(get_setting('password')),
        }
        from json import dumps
        data = dumps(payload).encode()
        return get_url_json(self._SSO_LOGIN_URL, headers=headers, data=data, fail={})

    def login(self, refresh=False):
        """Kodi GUI login flow"""
        # If no credentials, ask user for credentials
        if not has_credentials():
            if refresh:
                return open_settings()
            open_settings()
            if not self._credentials_changed():
                return None

        # Check credentials
        login_info = self._get_login_info()

        # Bad credentials
        while login_info.get('errorCode') != 0:
            # Show localized login error messages in Kodi GUI
            message = login_info.get('errorDetails')
            if not message:
                message = login_info or localize(30951)  # Login failed!
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
            login_info = self._get_login_info()

        redirect_url = login_info.get('redirectUrl')

        # Get new access token
        return self._get_new_token(name='vrtnu-site_profile_at', redirect_url=redirect_url)

    def _get_new_token(self, name, variant=None, redirect_url=None, roaming=False):
        """Return a new token"""
        if name == 'vrtPlayerToken':
            return self._get_playertoken(variant, roaming)

        if not redirect_url:
            return self.login()

        headers = {
            'Content-Type': 'application/json',
            'Cookie': 'SESSION=' + self.get_token('SESSION') + '; oidcstate=' + self.get_token('oidcstate'),
        }
        response = open_url(redirect_url, headers=headers, follow_redirects=False)

        next_location = response.info().get('Location')
        if not next_location:
            ok_dialog(heading=localize(30970), message=localize(30971))
            return None

        response = open_url(next_location, headers=headers, follow_redirects=False)

        if response:
            tokens = self._extract_tokens(response)
            for token in tokens:
                if token.get(name):
                    return token
        return None

    def get_token(self, name, variant=None, roaming=False):
        """Get a token"""

        # Try to get a cached token
        if not roaming:
            token = self._get_cached_token(name, variant)
            if token:
                return token.get(name)

        # Try to refresh a token
        if name.startswith('vrtnu'):
            refresh_token = self._get_cached_token('vrtnu-site_profile_rt')
            if refresh_token:
                token = self._get_fresh_token(refresh_token.get('vrtnu-site_profile_rt'), name)
                if token:
                    return token.get(name)

        # Get a new token
        token = self._get_new_token(name, variant, roaming=roaming)
        if token:
            return token.get(name)

        return None

    def _get_fresh_token(self, refresh_token, name):
        """Refresh expired profile tokens"""
        headers = {'Cookie': 'vrtnu-site_profile_rt=' + refresh_token}
        try:
            response = open_url(self._SSO_REFRESH_URL, headers=headers, raise_errors=[401])
        except HTTPError:
            ok_dialog(heading=localize(30970), message=localize(30971))
        tokens = self._extract_tokens(response)
        for token in tokens:
            if token.get(name):
                return token
        return None

    def _get_playertoken(self, variant, roaming):
        """Get a vrtPlayerToken"""
        from json import dumps
        headers = {'Content-Type': 'application/json'}
        playerinfo = self._generate_playerinfo()
        payload = {
            'playerInfo': playerinfo
        }
        if roaming or variant == 'ondemand':
            if roaming:
                # Delete cached vrtPlayerToken
                cache_file = self._get_token_filename('vrtPlayerToken', variant)
                delete_cache(cache_file, self._TOKEN_CACHE_DIR)
            videotoken = self.get_token('vrtnu-site_profile_vt')
            if videotoken is None:
                return None
            payload['identityToken'] = videotoken
        data = dumps(payload).encode()
        playertoken = get_url_json(url=self._PLAYERTOKEN_URL, headers=headers, data=data)
        if playertoken:
            # Cache token
            self._set_cached_token(playertoken, variant)
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
            header = {
                'alg': 'HS256',
                'kid': kid
            }
            payload = {
                'exp': time.time() + 1000,
                'platform': 'desktop',
                'app': {
                    'type': 'browser',
                    'name': 'Firefox',
                    'version': '102.0'
                },
                'device': 'undefined (undefined)',
                'os': {
                    'name': 'Linux',
                    'version': 'x86_64'
                },
                'player': {
                    'name': 'VRT web player',
                    'version': player_version
                }
            }
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
            self.login(refresh=True)

    def cleanup_userdata(self):
        """Cleanup userdata"""

        # Delete token cache
        self.delete_tokens()

        # Delete user-related caches
        invalidate_caches(
            'continue-*.json', 'favorites.json', 'my-offline-*.json', 'my-recent-*.json',
            'resume_points.json')

    def logged_in(self):
        """Whether there is an active login"""
        cache_file = self._get_token_filename('vrtnu-site_profile_at')
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
