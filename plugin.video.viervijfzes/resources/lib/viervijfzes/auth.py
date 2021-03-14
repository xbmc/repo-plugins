# -*- coding: utf-8 -*-
""" AUTH API """

from __future__ import absolute_import, division, unicode_literals

import json
import logging
import os
import time

from resources.lib import kodiutils
from resources.lib.viervijfzes.aws.cognito_identity import CognitoIdentity
from resources.lib.viervijfzes.aws.cognito_idp import AuthenticationException, CognitoIdp, InvalidLoginException
from resources.lib.viervijfzes.aws.cognito_sync import CognitoSync

_LOGGER = logging.getLogger(__name__)


class AuthApi:
    """ GoPlay Authentication API """
    COGNITO_REGION = 'eu-west-1'
    COGNITO_POOL_ID = 'eu-west-1_dViSsKM5Y'
    COGNITO_CLIENT_ID = '6s1h851s8uplco5h6mqh1jac8m'
    COGNITO_IDENTITY_POOL_ID = 'eu-west-1:8b7eb22c-cf61-43d5-a624-04b494867234'

    TOKEN_FILE = 'auth-tokens.json'

    def __init__(self, username, password, token_path):
        """ Initialise object """
        self._username = username
        self._password = password
        self._token_path = token_path
        self._id_token = None
        self._expiry = 0
        self._refresh_token = None

        # Load tokens from cache
        try:
            with open(os.path.join(self._token_path, self.TOKEN_FILE), 'r') as fdesc:
                data_json = json.loads(fdesc.read())
                self._id_token = data_json.get('id_token')
                self._refresh_token = data_json.get('refresh_token')
                self._expiry = int(data_json.get('expiry', 0))
        except (IOError, TypeError, ValueError):
            _LOGGER.warning('We could not use the cache since it is invalid or non-existent.')

    def get_token(self):
        """ Get a valid token """
        now = int(time.time())

        if self._id_token and self._expiry > now:
            # We have a valid id token in memory, use it
            _LOGGER.debug('Got an id token from memory')
            return self._id_token

        if self._refresh_token:
            # We have a valid refresh token, use that to refresh our id token
            # The refresh token is valid for 30 days. If this refresh fails, we just continue by logging in again.
            _LOGGER.debug('Getting an id token by refreshing')
            try:
                self._id_token = self._refresh(self._refresh_token)
                self._expiry = now + 3600
            except (InvalidLoginException, AuthenticationException) as exc:
                _LOGGER.error('Error logging in: %s', str(exc))
                self._id_token = None
                self._refresh_token = None
                self._expiry = 0
                # We continue by logging in with username and password

        if not self._id_token:
            # We have no tokens, or they are all invalid, do a login
            _LOGGER.debug('Getting an id token by logging in')
            id_token, refresh_token = self._authenticate(self._username, self._password)
            self._id_token = id_token
            self._refresh_token = refresh_token
            self._expiry = now + 3600

        # Store new tokens in cache
        if not os.path.exists(self._token_path):
            os.makedirs(self._token_path)
        with open(os.path.join(self._token_path, self.TOKEN_FILE), 'w') as fdesc:
            data = json.dumps(dict(
                id_token=self._id_token,
                refresh_token=self._refresh_token,
                expiry=self._expiry,
            ))
            fdesc.write(kodiutils.from_unicode(data))

        return self._id_token

    def clear_tokens(self):
        """ Remove the cached tokens. """
        if os.path.exists(os.path.join(self._token_path, AuthApi.TOKEN_FILE)):
            os.unlink(os.path.join(self._token_path, AuthApi.TOKEN_FILE))

    @staticmethod
    def _authenticate(username, password):
        """ Authenticate with Amazon Cognito and fetch a refresh token and id token. """
        idp_client = CognitoIdp(AuthApi.COGNITO_POOL_ID, AuthApi.COGNITO_CLIENT_ID)
        return idp_client.authenticate(username, password)

    @staticmethod
    def _refresh(refresh_token):
        """ Use the refresh token to fetch a new id token. """
        idp_client = CognitoIdp(AuthApi.COGNITO_POOL_ID, AuthApi.COGNITO_CLIENT_ID)
        return idp_client.renew_token(refresh_token)

    def get_dataset(self, dataset, key):
        """ Fetch the value from the specified dataset. """
        identity_client = CognitoIdentity(AuthApi.COGNITO_POOL_ID, AuthApi.COGNITO_IDENTITY_POOL_ID)
        id_token = self.get_token()
        identity_id = identity_client.get_id(id_token)
        credentials = identity_client.get_credentials_for_identity(id_token, identity_id)

        sync_client = CognitoSync(AuthApi.COGNITO_IDENTITY_POOL_ID, identity_id, credentials)
        data, session_token, sync_count = sync_client.list_records(dataset, key)

        sync_info = {
            'identity_id': identity_id,
            'credentials': credentials,
            'session_token': session_token,
            'sync_count': sync_count,
        }

        return data, sync_info

    @staticmethod
    def put_dataset(dataset, key, value, sync_info):
        """ Store the value from the specified dataset. """
        sync_client = CognitoSync(AuthApi.COGNITO_IDENTITY_POOL_ID, sync_info.get('identity_id'), sync_info.get('credentials'))
        sync_client.update_records(dataset, key, value, sync_info.get('session_token'), sync_info.get('sync_count'))
