# -*- coding: utf-8 -*-
""" Streamz Authentication API """

from __future__ import absolute_import, division, unicode_literals

import json
import logging
import os
import uuid

from requests import HTTPError

from resources.lib.streamz import API_ENDPOINT, PRODUCT_STREAMZ, Profile, util
from resources.lib.streamz.exceptions import NoLoginException

try:  # Python 3
    import jwt
except ImportError:  # Python 2
    # The package is named pyjwt in Kodi 18: https://github.com/lottaboost/script.module.pyjwt/pull/1
    import pyjwt as jwt

_LOGGER = logging.getLogger(__name__)


class AccountStorage:
    """ Data storage for account info """
    device_code = ''
    id_token = ''
    access_token = ''
    refresh_token = ''
    profile = ''
    product = ''

    def is_valid_token(self):
        """ Validate the JWT to see if it's still valid.
        :rtype: boolean
        """
        if not self.access_token:
            # We have no token
            return False

        try:
            # Verify our token to see if it's still valid.
            decoded_jwt = jwt.decode(self.access_token,
                                     algorithms=['HS256'],
                                     options={'verify_signature': False, 'verify_aud': False})

            # Check expiration time
            from datetime import datetime

            import dateutil.parser
            import dateutil.tz
            exp = datetime.fromtimestamp(decoded_jwt.get('exp'), tz=dateutil.tz.gettz('Europe/Brussels'))
            now = datetime.now(dateutil.tz.UTC)
            if exp < now:
                _LOGGER.debug('JWT is expired at %s', exp.isoformat())
                return False
        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.debug('JWT is NOT valid: %s', exc)
            return False
        _LOGGER.debug('JWT is valid')
        return True


class Auth:
    """ Streamz Authentication API """

    TOKEN_FILE = 'auth-tokens2.json'
    CLIENT_ID = '6sMlUPtp8BsujHOvtkvtC9DJv0gZjP3p'

    def __init__(self, token_path):
        """ Initialise object """
        self._token_path = token_path

        # Load existing account data
        self._account = AccountStorage()
        self._load_cache()

    def set_token(self, access_token):
        """ Sets an auth token """
        self._account.access_token = access_token
        self._save_cache()

    def set_profile(self, profile, product):
        """ Sets an auth profile """
        self._account.profile = profile
        self._account.product = product
        self._save_cache()

    def authorize(self):
        """ Start the authorization flow. """
        response = util.http_post('https://login.streamz.be/oauth/device/code', form={
            'client_id': self.CLIENT_ID,
            'scope': 'openid',
        })
        auth_info = json.loads(response.text)

        # We only need the device_code
        self._account.device_code = auth_info.get('device_code')
        self._save_cache()

        return auth_info

    def authorize_check(self):
        """ Check if the authorization has been completed. """
        if not self._account.device_code:
            raise NoLoginException

        try:
            response = util.http_post('https://login.streamz.be/oauth/token', form={
                'device_code': self._account.device_code,
                'client_id': self.CLIENT_ID,
                'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
            })
        except HTTPError as exc:
            if exc.response.status_code == 403:
                return False
            raise

        # Store these tokens
        auth_info = json.loads(response.text)
        self._account.id_token = auth_info.get('id_token')
        self._account.refresh_token = auth_info.get('refresh_token')

        # Fetch an actual token we can use
        response = util.http_post('https://lfvp-api.dpgmedia.net/STREAMZ/tokens', data={
            'device': {
                'id': str(uuid.uuid4()),
                'name': 'Streamz Addon on Kodi',
            },
            'idToken': self._account.id_token,
        })

        self._account.access_token = json.loads(response.text).get('lfvpToken')
        self._save_cache()

        return True

    def get_tokens(self):
        """ Check if we have a token based on our device code. """
        # If we have no access_token, return None
        if not self._account.access_token:
            return None

        # Return our current token if it is still valid.
        if self._account.is_valid_token() and self._account.profile and self._account.product:
            return self._account

        # We can refresh our old token so it's valid again
        response = util.http_post('https://lfvp-api.dpgmedia.net/STREAMZ/tokens/refresh', data={
            'lfvpToken': self._account.access_token,
        })

        # Get JWT from reply
        self._account.access_token = json.loads(response.text).get('lfvpToken')

        # We always use the main profile
        if not self._account.profile:
            profiles = self.get_profiles()
            main_profile = next((p for p in profiles if p.main_profile), None)
            self._account.profile = main_profile.key
            self._account.product = PRODUCT_STREAMZ

        self._save_cache()

        return self._account

    def get_profiles(self):
        """ Returns the available profiles """
        response = util.http_get(API_ENDPOINT + '/STREAMZ/profiles', token=self._account.access_token)
        result = json.loads(response.text)

        profiles = [
            Profile(
                key=profile.get('id'),
                name=profile.get('name'),
                gender=profile.get('gender'),
                birthdate=profile.get('birthDate'),
                color=profile.get('color', {}).get('start'),
                color2=profile.get('color', {}).get('end'),
                main_profile=profile.get('mainProfile'),
                kids_profile=profile.get('kidsProfile'),
            )
            for profile in result.get('profiles')
        ]

        return profiles

    def logout(self):
        """ Clear the session tokens. """
        self._account.__dict__ = {}  # pylint: disable=attribute-defined-outside-init
        self._save_cache()

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
