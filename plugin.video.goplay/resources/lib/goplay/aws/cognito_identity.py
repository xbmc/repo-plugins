# -*- coding: utf-8 -*-
""" Amazon Cognito Identity implementation without external dependencies """

from __future__ import absolute_import, division, unicode_literals

import json
import logging

import requests

_LOGGER = logging.getLogger(__name__)


class CognitoIdentity:
    """ Cognito Identity """

    def __init__(self, pool_id, identity_pool_id):
        """

        See https://docs.aws.amazon.com/cognitoidentity/latest/APIReference/Welcome.html.

        :param str pool_id:
        :param str identity_pool_id:
        """
        self.pool_id = pool_id
        if "_" not in self.pool_id:
            raise ValueError("Invalid pool_id format. Should be <region>_<poolid>.")

        self.identity_pool_id = identity_pool_id
        self.region = self.pool_id.split("_")[0]
        self.url = "https://cognito-identity.%s.amazonaws.com/" % self.region
        self._session = requests.session()

    def get_id(self, id_token):
        """ Get the Identity ID based on the id_token. """
        provider = 'cognito-idp.%s.amazonaws.com/%s' % (self.region, self.pool_id)
        data = {
            "IdentityPoolId": self.identity_pool_id,
            "Logins": {
                provider: id_token,
            }
        }
        response = self._session.post(self.url, json=data, headers={
            'x-amz-target': 'AWSCognitoIdentityService.GetId',
            'content-type': 'application/x-amz-json-1.1',
        })

        result = json.loads(response.text)

        return result.get('IdentityId')

    def get_credentials_for_identity(self, id_token, identity_id):
        """ Get credentials based on the id_token and identity_id. """
        provider = 'cognito-idp.%s.amazonaws.com/%s' % (self.region, self.pool_id)
        data = {
            "IdentityId": identity_id,
            "Logins": {
                provider: id_token,
            }
        }

        response = self._session.post(self.url, json=data, headers={
            'x-amz-target': 'AWSCognitoIdentityService.GetCredentialsForIdentity',
            'content-type': 'application/x-amz-json-1.1',
        })

        result = json.loads(response.text)

        return result.get('Credentials')
