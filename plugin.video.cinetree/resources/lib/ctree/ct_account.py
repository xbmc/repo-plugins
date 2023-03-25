
# ------------------------------------------------------------------------------
#  Copyright (c) 2022 Dimitri Kroon
#
#  SPDX-License-Identifier: GPL-2.0-or-later
#  This file is part of plugin.video.cinetree
# ------------------------------------------------------------------------------

from __future__ import unicode_literals
import time
import os
import json
import logging

from codequick.support import logger_id

from resources.lib import fetch, kodi_utils
from resources.lib import utils
from resources.lib.errors import *


logger = logging.getLogger(logger_id + '.ct_account')


class Session:
    def __init__(self):
        self.account_data = {}
        self.read_account_data()
        self.uname = self.account_data.get('uname')

    @property
    def access_token(self):
        """Return the cached access token, but refresh first if it has expired.
        Raise AuthenticationError when the token is not present.

        """
        try:
            if self.account_data['refreshed'] < time.time() - 4 * 3600:
                # renew tokens periodically
                logger.debug("Token cache time has expired.")
                self.refresh()

            return self.account_data['login_session']['token']
        except (KeyError, TypeError):
            logger.debug("Cannot produce access token from account data: %s", self.account_data)
            raise AuthenticationError

    def read_account_data(self):
        session_file = os.path.join(utils.addon_info['profile'], "session_data")
        logger.debug("Reading account data from file: %s", session_file)
        try:
            with open(session_file, 'r') as f:
                acc_data = json.load(f)
        except (OSError, IOError, ValueError) as err:
            logger.error("Failed to read account data: %r" % err)
            acc_data = {}
        self.account_data = acc_data

    def save_account_data(self):
        session_file = os.path.join(utils.addon_info['profile'], "session_data")
        with open(session_file, 'w') as f:
            json.dump(self.account_data, f)
        logger.debug("Account data saved to file")

    def login(self, uname=None, passw=None):
        """Login to account.

        The user is asked for username and password and a login attempt is made at
        Cinetree.nl
        Returns True on success, False when loging has been canceled (by the user).

        Raises AuthenticationError if login fails (and the user does not want to try
        again), or other exceptions as they occur, like e.g. FetchError.
        """
        self.account_data = {}

        if uname is None:
            uname = self.uname

        uname, passw = kodi_utils.ask_credentials(uname, passw)
        if not all((uname, passw)):
            return False

        self.uname = uname

        req_data = {
            'username': uname,
            'password': passw,
        }
        logger.info("Trying to login to account")
        try:
            session_data = fetch.post_json('https://api.cinetree.nl/login', req_data, timeout=8)
            self.account_data = {
                'uname': self.uname,
                'refreshed': time.time(),
                'login_session': session_data,
            }
        except AuthenticationError as e:
            if kodi_utils.ask_login_retry(str(e)):
                return self.login(uname, passw)
            else:
                raise
        except Exception as e:
            logger.info("Error logging in to account: %r" % e)
            raise
        else:
            logger.info("login successful")
            kodi_utils.show_login_result(success=True)
            self.save_account_data()
            return True

    def refresh(self):
        """Refresh tokens.
        Perform a get request with the current renew token in the param string. Cinetree will
        return a json formatted string containing a new access token and a new refresh token.

        """
        logger.debug("Refreshing account tokens...")
        try:
            session_data = self.account_data['login_session']
            url = 'https://api.cinetree.nl/login/refresh'
            # Refresh requests require no authorization header and no cookies at all
            resp = fetch.post_json(
                url,
                {'refreshToken': session_data['refreshToken']},
                {'Authorization': 'Bearer ' + session_data['token']},
                timeout=10
            )
            new_tokens = resp
            session_data.update(new_tokens)

            self.account_data['refreshed'] = time.time()
            self.save_account_data()
            return True
        except (KeyError, ValueError, FetchError) as e:
            logger.warning("Failed to refresh tokens - %s: %s" % (type(e), e))
        except TypeError:
            logger.warning("Failed to refresh tokens - No account data present.")
        return False

    def log_out(self):
        self.account_data = {}
        self.save_account_data()
        return True


_session_obj = None


def session():
    global _session_obj
    if _session_obj is None:
        _session_obj = Session()
    return _session_obj
