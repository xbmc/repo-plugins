# -*- coding: utf-8 -*-
""" VTM GO Authentication API """

from __future__ import absolute_import, division, unicode_literals

import json
import logging
import os
import re
from hashlib import md5
from uuid import uuid4

from requests import HTTPError

from resources.lib.vtmgo import API_ENDPOINT, Profile, util
from resources.lib.vtmgo.exceptions import InvalidLoginException, LoginErrorException, NoLoginException

try:  # Python 3
    import jwt
except ImportError:  # Python 2
    # The package is named pyjwt in Kodi 18: https://github.com/lottaboost/script.module.pyjwt/pull/1
    import pyjwt as jwt

_LOGGER = logging.getLogger(__name__)


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


class VtmGoAuth:
    """ VTM GO Authentication API """

    TOKEN_FILE = 'auth-tokens.json'

    def __init__(self, username, password, loginprovider, profile, token_path):
        """ Initialise object """
        self._username = username
        self._password = password
        self._loginprovider = loginprovider
        self._profile = profile
        self._token_path = token_path

        if not self._username or not self._password:
            raise NoLoginException()

        # Load existing account data
        self._account = AccountStorage()
        self._load_cache()

        # Do login so we have valid tokens
        self.login()

        # Apply profile and product
        if self._profile:
            parts = self._profile.split(':')
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

    def get_profiles(self, products='VTM_GO,VTM_GO_KIDS'):
        """ Returns the available profiles """
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

    def logout(self):
        """ Clear the session tokens. """
        self._account.jwt_token = None
        self._save_cache()

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
        # Yes, we have accepted the cookies
        util.SESSION.cookies.clear()
        util.SESSION.cookies.set('authId', str(uuid4()))

        # Start login flow
        util.http_get('https://vtm.be/vtmgo/aanmelden?redirectUrl=https://vtm.be/vtmgo')

        # Send login credentials
        try:
            response = util.http_post('https://login2.vtm.be/login?client_id=vtm-go-web', form={
                'userName': self._username,
                'password': self._password,
                'jsEnabled': 'true',
            })
        except HTTPError as exc:
            if exc.response.status_code == 400:
                raise InvalidLoginException()
            raise

        if 'errorBlock-OIDC-004' in response.text:  # E-mailadres is niet gekend.
            raise InvalidLoginException()

        if 'errorBlock-OIDC-003' in response.text:  # Wachtwoord is niet correct.
            raise InvalidLoginException()

        if 'OIDC-999' in response.text:  # Ongeldige login.
            raise InvalidLoginException()

        # Follow login
        response = util.http_get('https://login2.vtm.be/authorize/continue?client_id=vtm-go-web')

        # Extract state and code
        matches_state = re.search(r'name="state" value="([^"]+)', response.text)
        if matches_state:
            state = matches_state.group(1)
        else:
            raise LoginErrorException(code=101)  # Could not extract authentication code

        matches_code = re.search(r'name="code" value="([^"]+)', response.text)
        if matches_code:
            code = matches_code.group(1)
        else:
            raise LoginErrorException(code=101)  # Could not extract authentication code

        # Okay, final stage. We now need to POST our state and code to get a valid JWT.
        util.http_post('https://vtm.be/vtmgo/login-callback', form={
            'state': state,
            'code': code,
        })

        # Get JWT from cookies
        self._account.jwt_token = util.SESSION.cookies.get('lfvp_auth')

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
