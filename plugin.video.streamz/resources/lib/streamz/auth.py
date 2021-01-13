# -*- coding: utf-8 -*-
""" Streamz Authentication API """

from __future__ import absolute_import, division, unicode_literals

import json
import logging
import os
import re
from hashlib import md5

from resources.lib.streamz import API_ENDPOINT, Profile, util
from resources.lib.streamz.exceptions import (InvalidLoginException, LoginErrorException, NoLoginException, NoStreamzSubscriptionException,
                                              NoTelenetSubscriptionException)

try:  # Python 3
    from urllib.parse import parse_qs, urlsplit
except ImportError:  # Python 2
    from urlparse import parse_qs, urlsplit

try:  # Python 3
    import jwt
except ImportError:  # Python 2
    # The package is named pyjwt in Kodi 18: https://github.com/lottaboost/script.module.pyjwt/pull/1
    import pyjwt as jwt

_LOGGER = logging.getLogger(__name__)

LOGIN_STREAMZ = '0'
LOGIN_TELENET = '1'


class AccountStorage:
    """ Data storage for account info """
    login_token = ''
    jwt_token = ''
    profile = ''
    product = ''

    # Credentials hash
    hash = ''

    def is_valid_token(self):
        """ Validate the JWT to see if it's still valid.

        :rtype: boolean
        """
        if not self.jwt_token:
            # We have no token
            return False

        try:
            # Verify our token to see if it's still valid.
            jwt.decode(self.jwt_token,
                       algorithms=['HS256'],
                       options={'verify_signature': False, 'verify_aud': False})
        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.debug('JWT is NOT valid: %s', exc)
            return False

        _LOGGER.debug('JWT is valid')
        return True


class Auth:
    """ Streamz Authentication API """

    TOKEN_FILE = 'auth-tokens.json'
    CLIENT_ID = 'WWl9F97L9m56SrPcTmC2hYkCCKcmxevS'  # Website

    # CLIENT_ID = '6sMlUPtp8BsujHOvtkvtC9DJv0gZjP3p'  # Android APP

    def __init__(self, username, password, loginprovider, profile, token_path):
        """ Initialise object """
        self._username = username
        self._password = password
        self._loginprovider = loginprovider
        self._profile = profile

        if not self._username or not self._password:
            raise NoLoginException()

        self._token_path = token_path

        # Load existing account data
        self._account = AccountStorage()
        self._load_cache()

        # Do login so we have valid tokens
        self.login()

        # Apply profile and product
        if profile:
            parts = profile.split(':')
            try:
                self._account.profile = parts[0]
            except (IndexError, AttributeError):
                self._account.profile = None
            try:
                self._account.product = parts[1]
            except (IndexError, AttributeError):
                self._account.product = None

    def _check_credentials_change(self):
        """ Check if credentials have changed.

        :return:                        The hash of the current credentials.
        :rtype: str
        """
        old_hash = self._account.hash
        new_hash = md5((self._username + ':' + self._password + ':' + self._loginprovider).encode('utf-8')).hexdigest()

        if new_hash != old_hash:
            return new_hash
        return None

    def get_profiles(self, products='STREAMZ,STREAMZ_KIDS'):
        """ Returns the available profiles.

        :return:                        A list of profiles.
        :rtype: list[Profile]
         """
        response = util.http_get(API_ENDPOINT + '/profiles', {'products': products}, token=self._account.jwt_token)
        result = json.loads(response.text)

        profiles = [
            Profile(
                key=profile.get('id'),
                product=profile.get('product'),
                name=profile.get('name'),
                gender=profile.get('gender'),
                birthdate=profile.get('birthDate'),
                color=profile.get('color', {}).get('start'),
                color2=profile.get('color', {}).get('end'),
            )
            for profile in result
        ]

        return profiles

    def login(self, force=False):
        """ Make a login request.

        :param bool force:              Force authenticating from scratch without cached tokens.

        :return:
        :rtype: AccountStorage
        """
        # Check if credentials have changed
        new_hash = self._check_credentials_change()
        if new_hash:
            _LOGGER.debug('Credentials have changed, forcing a new login.')
            self._account.hash = new_hash
            force = True

        # Use cached token if it is still valid
        if force or not self._account.is_valid_token():
            # Do actual login
            self._web_login()

    def get_tokens(self):
        """ Return the tokens.

        :return:
        :rtype: AccountStorage
        """
        return self._account

    def _web_login(self):
        """ Executes a login and returns the JSON Web Token.
        :rtype str
        """
        # Start login flow
        util.SESSION.cookies.clear()
        util.http_get('https://account.streamz.be/login')

        # Generate random state and nonce parameters
        import random
        import string
        state = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(32))
        nonce = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(32))

        if self._loginprovider == LOGIN_STREAMZ:

            # Send login credentials
            response = util.http_post('https://login.streamz.be/co/authenticate',
                                      data={
                                          "client_id": self.CLIENT_ID,
                                          "username": self._username,
                                          "password": self._password,
                                          "realm": "Username-Password-Authentication",
                                          "credential_type": "http://auth0.com/oauth/grant-type/password-realm"
                                      },
                                      headers={
                                          'Origin': 'https://account.streamz.be',
                                          'Referer': 'https://account.streamz.be',
                                      })
            login_data = json.loads(response.text)

            # Obtain authorization
            response = util.http_get('https://login.streamz.be/authorize',
                                     params={
                                         'audience': 'https://streamz.eu.auth0.com/api/v2/',
                                         'domain': 'login.streamz.be',
                                         'client_id': self.CLIENT_ID,
                                         'response_type': 'id_token token',
                                         'redirect_uri': 'https://account.streamz.be/callback',
                                         'scope': 'read:current_user profile email openid',
                                         'state': state,
                                         'nonce': nonce,
                                         'auth0Client': 'eyJuYW1lIjoiYXV0aDAuanMiLCJ2ZXJzaW9uIjoiOS4xMy4yIn0=',
                                         # base64 encoded {"name":"auth0.js","version":"9.13.2"}
                                         'realm': 'Username-Password-Authentication',
                                         'login_ticket': login_data.get('login_ticket'),
                                     })

        elif self._loginprovider == LOGIN_TELENET:

            # Obtain authorization
            util.http_get('https://login.streamz.be/authorize',
                          params={
                              'audience': 'https://streamz.eu.auth0.com/api/v2/',
                              'domain': 'login.streamz.be',
                              'client_id': self.CLIENT_ID,
                              'response_type': 'id_token token',
                              'redirect_uri': 'https://account.streamz.be/callback',
                              'scope': 'read:current_user profile email openid',
                              'connection': 'TN',
                              'state': state,
                              'nonce': nonce,
                              'auth0Client': 'eyJuYW1lIjoiYXV0aDAuanMiLCJ2ZXJzaW9uIjoiOS4xMy4yIn0=',  # base64 encoded {"name":"auth0.js","version":"9.13.2"}
                          })

            # Send login credentials
            response = util.http_post('https://login.prd.telenet.be/openid/login.do',
                                      form={
                                          'j_username': self._username,
                                          'j_password': self._password,
                                          'rememberme': 'true',
                                      })

            if 'Je gebruikersnaam en/of wachtwoord zijn verkeerd' in response.text:
                raise InvalidLoginException

        else:
            raise Exception('Unsupported login method: %s' % self._loginprovider)

        # Extract login_token
        params = parse_qs(urlsplit(response.url).fragment)
        if params:
            self._account.login_token = params.get('access_token')[0]
        else:
            raise LoginErrorException(code=103)  # Could not extract parameter

        # Check login token
        self.check_status()

        # Login to the actual app
        response = util.http_get('https://www.streamz.be/streamz/aanmelden')

        # Extract state and code
        matches_state = re.search(r'name="state" value="([^"]+)', response.text)
        if matches_state:
            state = matches_state.group(1)
        else:
            raise LoginErrorException(code=101)  # Could not extract authentication state

        matches_code = re.search(r'name="code" value="([^"]+)', response.text)
        if matches_code:
            code = matches_code.group(1)
        else:
            raise LoginErrorException(code=102)  # Could not extract authentication code

        # Okay, final stage. We now need to POST our state and code to get a valid JWT.
        util.http_post('https://www.streamz.be/streamz/login-callback', form={
            'state': state,
            'code': code,
        })

        # Get JWT from cookies
        self._account.jwt_token = util.SESSION.cookies.get('lfvp_auth')

        self._save_cache()

        return self._account

    def check_status(self):
        """ Check customer status """
        response = util.http_get('https://customer-api.streamz.be/onboarding/customer-status',
                                 headers={
                                     'authorization': 'Bearer ' + self._account.login_token,
                                 })

        status = json.loads(response.text)

        if status.get('customerStatus') == 'NOT_AUTHORIZED':
            raise NoStreamzSubscriptionException()

        if status.get('customerStatus') == 'NOT_AUTHORIZED_TELENET':
            raise NoTelenetSubscriptionException()

    def _load_cache(self):
        """ Load tokens from cache """
        try:
            with open(os.path.join(self._token_path, self.TOKEN_FILE), 'r') as fdesc:
                self._account.__dict__ = json.loads(fdesc.read())  # pylint: disable=attribute-defined-outside-init
        except (IOError, TypeError, ValueError):
            _LOGGER.warning('We could not use the cache since it is invalid or non-existent.')

    def _save_cache(self):
        """ Store tokens in cache """
        if not os.path.exists(self._token_path):
            os.makedirs(self._token_path)

        with open(os.path.join(self._token_path, self.TOKEN_FILE), 'w') as fdesc:
            json.dump(self._account.__dict__, fdesc, indent=2)
