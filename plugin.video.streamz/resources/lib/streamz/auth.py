# -*- coding: utf-8 -*-
""" Streamz Authentication API """

from __future__ import absolute_import, division, unicode_literals

import base64
import hashlib
import json
import logging
import os
import random
import re
import string

from requests import HTTPError

from resources.lib.streamz import API_ENDPOINT, Profile, util
from resources.lib.streamz.exceptions import (InvalidLoginException, InvalidTokenException, NoLoginException, NoStreamzSubscriptionException,
                                              NoTelenetSubscriptionException)

try:  # Python 3
    from urllib.parse import parse_qs, urlparse
except ImportError:  # Python 2
    from urlparse import parse_qs, urlparse

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
    CLIENT_ID = '6sMlUPtp8BsujHOvtkvtC9DJv0gZjP3p'

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
        new_hash = hashlib.md5((self._username + ':' + self._password + ':' + self._loginprovider).encode('utf-8')).hexdigest()

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
            self._do_login()

    def get_tokens(self):
        """ Return the tokens.

        :return:
        :rtype: AccountStorage
        """
        return self._account

    def _do_login(self):
        """ Executes an android login and returns the JSON Web Token.
        :rtype str
        """
        # We should start fresh
        util.SESSION.cookies.clear()

        # Generate random state and nonce parameters
        state = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(32))
        nonce = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(32))
        code_verifier = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(64))
        code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode('ascii')).digest()).decode('ascii')[:-1]

        # Start login flow
        response = util.http_get('https://login.streamz.be/authorize', params={
            'scope': 'openid',
            'auth0Client': 'eyJuYW1lIjoiQXV0aDAuQW5kcm9pZCIsImVudiI6eyJhbmRyb2lkIjoiMjMifSwidmVyc2lvbiI6IjEuMjMuMCJ9',
            'client_id': self.CLIENT_ID,
            'code_challenge_method': 'S256',
            'state': state,
            'response_type': 'code',
            'redirect_uri': 'streamz://login.streamz.be/android/be.dpgmedia.streamz/callback',
            'code_challenge': code_challenge,
            'nonce': nonce,
        })
        params = parse_qs(urlparse(response.url).query)
        form_state = params.get('state')[0]

        if self._loginprovider == LOGIN_STREAMZ:
            # Send login credentials
            try:
                response = util.http_post('https://login.streamz.be/usernamepassword/login',
                                          form={
                                              # '_csrf': 'Mz6HKTgr-LccVcPgnJzXJO_yO1ISsseYwN20',
                                              '_intstate': 'deprecated',
                                              'client_id': self.CLIENT_ID,
                                              'connection': 'Username-Password-Authentication',
                                              'nonce': nonce,
                                              'password': self._password,
                                              'redirect_uri': 'streamz://login.streamz.be/android/be.dpgmedia.streamz/callback',
                                              'response_type': 'code',
                                              'scope': 'openid',
                                              'state': form_state,
                                              'tenant': 'streamz',
                                              'username': self._username
                                          })
            except InvalidTokenException:
                raise InvalidLoginException

            # This page makes a POST to the next url, but we have to do this manually.
            # Extract wa, wresult and wctx
            matches = re.findall(r'name="([^"]+)"\s+value="([^"]+)"', response.text, flags=re.DOTALL)
            form = dict(matches)
            form['wctx'] = form['wctx'].replace('&#34;', '"')

            response = util.http_post('https://login.streamz.be/login/callback', form=form)

            # We will be redirected to a streamz:// url where we can obtain the state and code
            params = parse_qs(urlparse(response.url).query)
            code = params.get('code')[0]
            # state = params.get('state')[0]

        elif self._loginprovider == LOGIN_TELENET:
            # Start a new login flow with Telenet
            util.http_get('https://login.streamz.be/authorize', params={
                'scope': 'openid',
                'auth0Client': 'eyJuYW1lIjoiYXV0aDAuanMiLCJ2ZXJzaW9uIjoiOS4xMy40In0=',
                'client_id': self.CLIENT_ID,
                'state': state,
                'response_type': 'code',
                'redirect_uri': 'streamz://login.streamz.be/android/be.dpgmedia.streamz/callback',
                'nonce': nonce,
                'connection': 'TN',
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

            # We will be redirected to a streamz:// url where we can obtain the state and code
            params = parse_qs(urlparse(response.url).query)
            code = params.get('code')[0]
            # state = params.get('code')[0]

        else:
            raise ValueError('Unknown Login Provider: %s' % self._loginprovider)

        # Okay, final stage. We now need to authorize our code and code_verifier to get an id_token.
        response = util.http_post('https://login.streamz.be/oauth/token', data={
            "client_id": self.CLIENT_ID,
            "code": code,
            "code_verifier": code_verifier,
            "grant_type": "authorization_code",
            "redirect_uri": "streamz://login.streamz.be/android/be.dpgmedia.streamz/callback"
        })
        data = json.loads(response.text)

        # Get JWT from reply
        id_token = data.get('id_token')

        # Authenticate with our id_token to get a jwt_token
        response = util.http_post('https://lfvp-api.dpgmedia.net/authorize/idToken', data={
            "clientId": self.CLIENT_ID,
            "pipIdToken": id_token,
        })

        self._account.jwt_token = json.loads(response.text).get('jsonWebToken')

        # Get a list of profiles so we can check our authentication
        try:
            self.get_profiles()
        except HTTPError as exc:
            if exc.response.status_code == 402:
                if self._loginprovider == LOGIN_STREAMZ:
                    raise NoStreamzSubscriptionException
                raise NoTelenetSubscriptionException
            raise

        self._save_cache()

        return self._account

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
