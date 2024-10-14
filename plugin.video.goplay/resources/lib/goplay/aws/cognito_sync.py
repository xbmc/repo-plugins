# -*- coding: utf-8 -*-
""" Amazon Cognito Sync implementation without external dependencies """

from __future__ import absolute_import, division, unicode_literals

import datetime
import hashlib
import hmac
import json
import logging

import requests

try:  # Python 3
    from urllib.parse import quote, urlparse
except ImportError:  # Python 2
    from urllib import quote

    from urlparse import urlparse

_LOGGER = logging.getLogger(__name__)


class CognitoSync:
    """ Amazon Cognito Sync """

    def __init__(self, identity_pool_id, identity_id, credentials):
        """

        See https://docs.aws.amazon.com/cognitosync/latest/APIReference/Welcome.html.

        :param str identity_pool_id:
        :param str identity_id:
        :param dict credentials:
        """
        self.identity_pool_id = identity_pool_id
        self.identity_id = identity_id
        self.credentials = credentials

        self.region = self.identity_pool_id.split(":")[0]
        self.url = "https://cognito-sync.%s.amazonaws.com" % self.region
        self._session = requests.session()

    def _sign(self, request, service='cognito-sync'):
        """ Sign the request.

        More info at https://docs.aws.amazon.com/general/latest/gr/signature-version-4.html.

        :param requests.PreparedRequest request:        A prepared request that should be signed.
        :param str service:                             The service where this request is going to.
        """

        def sign(key, msg):
            """ Sign this message. """
            return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

        def get_signature_key(key, date_stamp, region_name, service_name):
            """ Generate a signature key. """
            k_date = sign(('AWS4' + key).encode('utf-8'), date_stamp)
            k_region = sign(k_date, region_name)
            k_service = sign(k_region, service_name)
            k_signing = sign(k_service, 'aws4_request')
            return k_signing

        # Parse the URL
        url_parsed = urlparse(request.url)

        # Create a date for headers and the credential string
        now = datetime.datetime.utcnow()
        amzdate = now.strftime('%Y%m%dT%H%M%SZ')
        datestamp = now.strftime('%Y%m%d')  # Date w/o time, used in credential scope

        # Step 1. Create a canonical request
        canonical_uri = quote(url_parsed.path)
        canonical_querystring = url_parsed.query  # TODO: sort when using multiple values
        canonical_headers = ('host:' + url_parsed.netloc + '\n' +
                             'x-amz-date:' + amzdate + '\n')
        signed_headers = 'host;x-amz-date'

        if request.body:
            payload_hash = hashlib.sha256(request.body).hexdigest()
        else:
            # SHA256 of empty string
            payload_hash = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'

        canonical_request = (request.method + '\n' +
                             canonical_uri + '\n' +
                             canonical_querystring + '\n' +
                             canonical_headers + '\n' +
                             signed_headers + '\n' +
                             payload_hash)

        # Step 2. Create a string to sign
        algorithm = 'AWS4-HMAC-SHA256'
        credential_scope = '%s/%s/%s/%s' % (datestamp, self.region, service, 'aws4_request')
        string_to_sign = (algorithm + '\n' +
                          amzdate + '\n' +
                          credential_scope + '\n' +
                          hashlib.sha256(canonical_request.encode('utf-8')).hexdigest())
        signing_key = get_signature_key(self.credentials.get('SecretKey'), datestamp, self.region, service)

        # Step 3. Calculate the signature
        signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

        authorization_header = '%s Credential=%s/%s, SignedHeaders=%s, Signature=%s' % (
            algorithm, self.credentials.get('AccessKeyId'), credential_scope, signed_headers, signature)

        # Step 4. Add the signature to the request
        request.headers.update({
            'x-amz-date': amzdate,
            'Authorization': authorization_header
        })

    def list_records(self, dataset, key):
        """ Return the values of this dataset.

        :param str dataset:            The name of the dataset to request.
        :param str key:                The name of the key to request.
        :return The requested dataset
        :rtype: dict
        """
        # Prepare the request
        request = requests.Request(
            method='GET',
            params={
                'maxResults': 1024,
            },
            url=self.url + '/identitypools/{identity_pool_id}/identities/{identity_id}/datasets/{dataset}/records'.format(
                identity_pool_id=self.identity_pool_id,
                identity_id=self.identity_id,
                dataset=dataset
            ),
            headers={
                'x-amz-security-token': self.credentials.get('SessionToken'),
            }).prepare()

        # Sign the request
        self._sign(request)

        # Send the request
        reply = self._session.send(request)
        reply.raise_for_status()
        result = json.loads(reply.text)

        _LOGGER.debug("Got results: %s", result.get('Records'))

        # Return the records
        try:
            record = next(record for record in result.get('Records', []) if record.get('Key') == key)
            value = json.loads(record.get('Value'))
            sync_count = record.get('SyncCount')
        except StopIteration:
            value = None
            sync_count = 0

        return value, result.get('SyncSessionToken'), sync_count

    def update_records(self, dataset, key, value, session_token, sync_count):
        """ Return the values of this dataset.

        :param str dataset:            The name of the dataset to request.
        :param any value:              The value.
        :param str session_token:      The session token from the list_records call.
        :param int sync_count:         The last SyncCount value, so we refuse race conditions.
        """
        # Prepare the request
        request = requests.Request(
            method='POST',
            url=self.url + '/identitypools/{identity_pool_id}/identities/{identity_id}/datasets/{dataset}'.format(
                identity_pool_id=self.identity_pool_id,
                identity_id=self.identity_id,
                dataset=dataset
            ),
            headers={
                'x-amz-security-token': self.credentials.get('SessionToken'),
            },
            json={
                "SyncSessionToken": session_token,
                "RecordPatches": [
                    {
                        "Key": key,
                        "Op": "replace",
                        "SyncCount": sync_count,
                        "Value": json.dumps(value),
                    }
                ]
            }).prepare()

        # Sign the request
        self._sign(request)

        # Send the request
        reply = self._session.send(request)
        reply.raise_for_status()
