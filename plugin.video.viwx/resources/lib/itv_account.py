# ----------------------------------------------------------------------------------------------------------------------
#  Copyright (c) 2022-2024 Dimitri Kroon.
#  This file is part of plugin.video.viwx.
#  SPDX-License-Identifier: GPL-2.0-or-later
#  See LICENSE.txt
# ----------------------------------------------------------------------------------------------------------------------
import sys
import time
import os
import json
import logging

from codequick.support import logger_id

from . import utils
from . import fetch
from . import kodi_utils
from .errors import *


logger = logging.getLogger(logger_id + '.account')
SESS_DATA_VERS = 2


class ItvSession:
    def __init__(self):
        self._user_id = ''
        self._user_nickname = ''
        self._expire_time = 0
        self.account_data = {}
        self.read_account_data()

    @property
    def access_token(self):
        """Return the cached access token, but refresh first if it has expired.
        Raise AuthenticationError when the token is not present.

        """
        try:
            return self.account_data['itv_session']['access_token']
        except (KeyError, TypeError):
            logger.debug("Cannot produce access token from account data: %s.", self.account_data)
            return ''

    @property
    def cookie(self):
        """Return a dict containing the cookie required for authentication"""
        try:
            return self.account_data['cookies']
        except (KeyError, TypeError):
            logger.debug("Cannot produce cookies from account data: %s.", self.account_data)
            return {}

    @property
    def user_id(self):
        return self._user_id or ''

    @property
    def user_nickname(self):
        return self._user_nickname or ''

    def read_account_data(self):
        session_file = os.path.join(utils.addon_info.profile, "itv_session")
        logger.debug("Reading account data from file: %s", session_file)
        try:
            with open(session_file, 'r') as f:
                acc_data = json.load(f)
        except (OSError, IOError, ValueError) as err:
            logger.error("Failed to read account data: %r" % err)
            self.account_data = {}
            return

        if acc_data.get('vers') != SESS_DATA_VERS:
            logger.info("Converting account data from version '%s' to version '%s'",
                        acc_data.get('vers'), SESS_DATA_VERS)
            self.account_data = convert_session_data(acc_data)
            self.save_account_data()
        else:
            self.account_data = acc_data
        access_token = self.account_data.get('itv_session', {}).get('access_token')
        self._user_id, self._user_nickname, self._expire_time = parse_token(access_token)

    def save_account_data(self):
        session_file = os.path.join(utils.addon_info.profile, "itv_session")
        data_str = json.dumps(self.account_data)
        with open(session_file, 'w') as f:
            f.write(data_str)
        logger.info("ITV account data saved to file.")

    def login(self, uname: str, passw: str):
        """Sign in to itv account with `uname` and `passw`.

        Returns True on success, raises exception on failure.
        Raises AuthenticationError if login fails, or other exceptions as they occur, like e.g. FetchError.
        """
        import requests
        from resources.lib.telemetry_data import telemetry_factory
        self.account_data = {}

        req_data = {
            'grant_type': 'password',
            'nonce': 'cerberus-auth-request-' + str(int(time.time() * 1000)),
            'username': uname,
            'password': passw,
            'scope': 'content'
        }

        logger.info("Trying to sign in to ITV account")
        try:
            # Post credentials
            resp = requests.post(
                'https://auth.prd.user.itv.com/v2/auth',
                json=req_data,
                headers={
                    'user-agent':           fetch.USER_AGENT,
                    'accept':               'application/vnd.user.auth.v2+json',
                    'accept-language':      'en-GB,en;q=0.5',
                    'accept-encoding':      'gzip, deflate',
                    'content-type':         'application/json',
                    'akamai-bm-telemetry':  telemetry_factory.get_data(),
                    'origin':               'https://www.itv.com',
                    'referer':              'https://www.itv.com/',
                    'sec-fetch-dest':       'empty',
                    'sec-fetch-mode':       'cors',
                    'sec-fetch-site':       'same-site',
                    'priority':             'u=1',
                    'te':                   'trailers'
                },
                timeout=fetch.WEB_TIMEOUT
            )
            resp.raise_for_status()
            session_data = resp.json()
            self.account_data = {
                'vers': SESS_DATA_VERS,
                'refreshed': time.time(),
                'itv_session': session_data,
                'cookies': {'Itv.Session': build_cookie(session_data)}
            }
        except requests.HTTPError as e:
            logger.error("Error signing in to ITV account: %r" % e)
            status_code = e.response.status_code
            if status_code in (400, 403):
                msg = {
                    400: 'Invalid username or password',
                    403: 'Forbidden\nIf this error persists wait a few hours before trying again.'
                }.get(status_code, 'Sign in failed.')
                logger.info("Sign in failed: %r: %r", e, e.response.content)
                raise AuthenticationError(msg) from None
            else:
                raise
        except:
            logger.error("Error signing in to ITV account:\n", exc_info=True)
            raise
        else:
            logger.info("Sign in successful.")
            self._user_id, self._user_nickname, self._expire_time = parse_token(session_data.get('access_token'))
            self.save_account_data()
            return True

    def refresh(self):
        """Refresh tokens.
        Perform a get request with the current renew token in the param string. ITV hub will
        return a json formatted string containing a new access token and a new renew-token.

        """
        logger.debug("Refreshing ITV account tokens...")
        try:
            token = self.account_data['itv_session']['refresh_token']
            url = 'https://auth.prd.user.itv.com/token?grant_type=refresh_token&' \
                  'token=content_token refresh_token&refresh=' + token
            # Refresh requests require no authorization header and no cookies at all
            resp = fetch.get_json(
                url,
                headers={'Accept': 'application/vnd.user.auth.v2+json'},
                timeout=10
            )
            new_tokens = resp
            session_data = self.account_data['itv_session']
            session_data.update(new_tokens)
            sess_cookie_str = build_cookie(session_data)
            logger.debug("New Itv.Session cookie: %s" % sess_cookie_str)
            self.account_data['cookies']['Itv.Session'] = sess_cookie_str
            self.account_data['refreshed'] = time.time()
            self._user_id, self._user_nickname, self._expire_time = parse_token(session_data.get('access_token'))
            self.save_account_data()
            logger.info("Tokens refreshed.")
            return True
        except (KeyError, ValueError, FetchError) as e:
            logger.warning("Failed to refresh ITVtokens - %s: %s" % (type(e), e))
        except TypeError:
            logger.warning("Failed to refresh ITV tokens - No account data present.")
        return False

    def log_out(self):
        logger.info("Signing out to ITV account")
        self.account_data = {}
        self.save_account_data()
        self._user_id = None
        self._user_nickname = None
        return True


def parse_token(token):
    """Return user_id, user nickname and token expiration time obtained from an access token.

    Token has other fields which we currently don't parse, like:
    accountProfileIdInUse
    auth_time
    scope
    nonce
    iat
    """
    import binascii
    try:
        token_parts = token.split('.')
        # Since some padding errors have been observed with refresh tokens, add the maximum just
        # to be sure padding errors won't occur. a2b_base64 automatically removes excess padding.
        token_data = binascii.a2b_base64(token_parts[1] + '==')
        data = json.loads(token_data)
        return data['sub'], data['name'], data['exp']
    except (KeyError, AttributeError, IndexError, binascii.Error) as err:
        logger.error("Failed to parse token: '%r'", err)
        return None, None, int(time.time()) + time.timezone


def build_cookie(session_data):
    cookiestr = json.dumps({
        'sticky': True,
        'tokens': {'content': session_data}
    })
    return cookiestr


_itv_session_obj = None


def itv_session():
    global _itv_session_obj
    if _itv_session_obj is None:
        _itv_session_obj = ItvSession()
    return _itv_session_obj


def fetch_authenticated(funct, url, login=True, **kwargs):
    """Call one of the fetch function with user authentication.

    Call the specified function with authentication header and return the result.
    If the server responds with an authentication error, refresh tokens, or
    login and try once again.

    To prevent headers argument to turn up as both positional and keyword argument,
    accept keyword arguments only, apart from the callable and url.

    """
    account = itv_session()
    logger.debug("making authenticated request")

    for tries in range(2):
        try:
            access_token = account.access_token
            auth_cookies = account.cookie
            if not (access_token and auth_cookies):
                raise AuthenticationError

            try:
                if account.account_data['refreshed'] < time.time() - 4 * 3600:
                    # renew tokens periodically
                    logger.debug("Token cache time has expired.")
                    raise AuthenticationError
            except (KeyError, TypeError):
                raise AuthenticationError

            cookies = kwargs.setdefault('cookies', {})
            headers = kwargs.setdefault('headers', {})
            headers['authorization'] = 'Bearer ' + account.access_token
            cookies.update(auth_cookies)
            return funct(url=url, **kwargs)
        except AuthenticationError:
            if tries > 0:
                logger.warning("Authentication failed on second attempt")
                raise AccessRestrictedError

            logger.debug("Authentication failed on first attempt")
            if account.refresh() is False:
                if login:
                    if kodi_utils.show_msg_not_logged_in():
                        from xbmc import executebuiltin
                        executebuiltin('Addon.OpenSettings({})'.format(utils.addon_info.id))
                    sys.exit(1)
                else:
                    raise


def convert_session_data(acc_data: dict) -> dict:
    acc_data['vers'] = SESS_DATA_VERS
    sess_data = acc_data.get('itv_session', '')
    acc_data['cookies'] = {'Itv.Session': build_cookie(sess_data)}
    acc_data.pop('passw', None)
    acc_data.pop('uname', None)
    return acc_data
