# -*- coding: utf-8 -*-
""" Solocoo Auth API """

from __future__ import absolute_import, division, unicode_literals

import json
import logging
import os
import time
import uuid
from hashlib import md5

from requests import HTTPError

from resources.lib.solocoo import SOLOCOO_API, TENANTS, util
from resources.lib.solocoo.exceptions import InvalidLoginException, InvalidTokenException

try:  # Python 3
    import jwt
except ImportError:  # Python 2
    # The package is named pyjwt in Kodi 18: https://github.com/lottaboost/script.module.pyjwt/pull/1
    import pyjwt as jwt

try:  # Python 3
    from urllib.parse import parse_qs, urljoin, urlparse
except ImportError:  # Python 2
    from urlparse import parse_qs, urljoin, urlparse

_LOGGER = logging.getLogger(__name__)


class AccountStorage:
    """ Data storage for account info """
    # We will generate a random serial when we don't have any
    device_serial = ''
    device_name = 'Kodi'

    # Challenges we can keep to renew our tokens
    challenge_id = ''
    challenge_secret = ''

    # Cookie token used to authenticate requests to the app
    aspx_token = ''

    # Token used to authenticate a request to the tvapi.solocoo.tv endpoint
    jwt_token = ''

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
            # Verify if token is still valid
            token = jwt.decode(self.jwt_token, algorithms=['HS256'], options={
                'verify_signature': False,
                'verify_aud': False,
                'verify_nbf': False,
                'verify_exp': True,
            })

            # NOTE: verify_signature=False combined with verify_exp=True doesn't work on pyjwt 2.0.0, see https://github.com/jpadilla/pyjwt/issues/599
            from calendar import timegm
            from datetime import datetime
            now = timegm(datetime.utcnow().utctimetuple())
            if int(token["exp"]) < now:
                raise Exception('Signature has expired')

        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.debug('JWT is NOT valid: %s', exc)
            return False

        _LOGGER.debug('JWT is valid')
        return True


class AuthApi:
    """ Solocoo Auth API """

    TOKEN_FILE = 'auth-tokens.json'

    def __init__(self, username, password, tenant, token_path):
        """ Initialisation of the class.

        :param str username:            The username of the account.
        :param str password:            The password of the account.
        :param str tenant:              The tenant code of the account (eg. tvv).
        :param str token_path:          The path where we can cache our token.
        """
        self._username = username
        self._password = password

        self._tenant = TENANTS.get(tenant)
        if self._tenant is None:
            raise Exception('Invalid tenant: %s' % tenant)

        self._token_path = token_path

        # Load existing account data
        self._account = AccountStorage()
        self._load_cache()

        # Generate device serial if we have none
        if not self._account.device_serial:
            self._account.device_serial = str(uuid.uuid4())
            self._save_cache()

        # Do login so we have valid tokens
        self.login()

    def get_tenant(self):
        """ Return the tenant information. """
        return self._tenant

    def login(self, force=False):
        """ Make a login request.

        :param bool force:              Force authenticating from scratch without cached tokens.

        :returns:                       An object containing tokens.
        :rtype: AccountStorage
        """
        # Check if credentials have changed
        new_hash = self._check_credentials_change()
        if new_hash:
            _LOGGER.debug('Credentials have changed, forcing a new login.')
            self._account.hash = new_hash
            self._account.challenge_id = None
            self._account.challenge_secret = None
            force = True

        # Use cached token if it is still valid
        if not force and self._account.is_valid_token():
            return self._account

        if not self._account.challenge_id or not self._account.challenge_secret:
            # We don't have an challenge_id or challenge_secret, so we need to request one
            # This challenge can be kept for a longer time
            self._account.challenge_id, self._account.challenge_secret = self._do_challenge(
                self._account.device_name,
                self._account.device_serial,
                self._username,
                self._password,
            )

        # Request the ASPX cookie based on the challenge. The website does this every session.
        try:
            self._account.aspx_token = self._get_aspx_cookie(self._account.challenge_id,
                                                             self._account.challenge_secret,
                                                             self._account.device_serial)
        except HTTPError as ex:
            if ex.response.status_code in [403, 500]:
                # Our challenge_id and challenge_secret isn't valid anymore
                _LOGGER.info('The challenge_id and challenge_secret are not valid anymore. Requesting new ones.')
                self._account.challenge_id, self._account.challenge_secret = self._do_challenge(
                    self._account.device_name,
                    self._account.device_serial,
                    self._username,
                    self._password,
                )

                # Try again with a fresh challenge
                self._account.aspx_token = self._get_aspx_cookie(self._account.challenge_id,
                                                                 self._account.challenge_secret,
                                                                 self._account.device_serial)
            else:
                raise

        # And finally, get our sapi token by using our stored ASPXAUTH token
        # The sapi token token seems to expires in 30 minutes
        sapi_token = self._get_sapi_token(self._account.aspx_token)

        # Request JWT token
        # The JWT token also seems to expires in 30 minutes
        self._account.jwt_token = self._get_jwt_token(sapi_token,
                                                      self._account.device_name,
                                                      self._account.device_serial)

        # Save the tokens we have in a cache
        self._save_cache()

        return self._account

    def _check_credentials_change(self):
        """ Check if credentials have changed.

        :return:                        The hash of the current credentials.
        :rtype: str
        """
        old_hash = self._account.hash
        new_hash = md5((self._username + ':' + self._password).encode('utf-8')).hexdigest()

        if new_hash != old_hash:
            return new_hash
        return None

    def _do_challenge(self, device_name, device_serial, username, password):
        """ Do an authentication challenge.

        :param str device_name:         The device name of this running Kodi instance.
        :param str device_serial:       The device serial of this running Kodi instance.
        :param str username:            The username to authenticate with.
        :param str password:            The password to authenticate with.

        :returns:                       A tuple (challenge_id, challenge_secret) that can be used to fetch a token.
        :rtype: tuple(str, str)
        """
        if username and password:
            # Do authenticated login
            oauth_code = self._get_oauth_code(username, password)
            data = dict(
                autotype='nl',
                app=self._tenant.get('app'),
                prettyname=device_name,
                model='web',
                serial=device_serial,
                oauthcode=oauth_code,
                apikey='',
            )
        else:
            # Do anonymous login
            data = dict(
                autotype='nl',
                app=self._tenant.get('app'),
                prettyname=device_name,
                model='web',
                serial=device_serial,
            )

        reply = util.http_post('https://{domain}/{env}/challenge.aspx'.format(domain=self._tenant.get('domain'),
                                                                              env=self._tenant.get('env')),
                               data=data)
        challenge = json.loads(reply.text)

        return challenge.get('id'), challenge.get('secret')

    def _get_oauth_code(self, username, password):
        """ Do login with the sso and return the OAuth code.

        :param str username:            The username to authenticate with.
        :param str password:            The password to authenticate with.

        :returns:                       An OAuth code we can use to continue authenticating.
        :rtype: string
        """
        # This is probably not necessary for all providers, and this also might need some factory pattern to support
        # other providers.

        # Ask to forward us to the login form.
        login_page = util.http_get(
            'https://{domain}/{env}/sso.aspx'.format(domain=self._tenant.get('domain'),
                                                     env=self._tenant.get('env')),
            params=dict(
                a=self._tenant.get('app'),
                s=time.time() * 100,  # unixtime in milliseconds
            )
        )

        # Extract the path from the form, the form posts to /
        login_url = urljoin(login_page.url, '/')

        # Submit credentials
        reply = util.http_post(
            login_url,
            form=dict(
                Username=username,
                Password=password,
            )
        )

        if 'De gebruikersnaam of het wachtwoord dat u heeft ingegeven is niet correct' in reply.text:
            raise InvalidLoginException

        # Extract query parameters from redirected url
        params = parse_qs(urlparse(reply.url).query)

        return params.get('code')[0]

    def _get_aspx_cookie(self, challenge_id, challenge_secret, device_serial):
        """ Get an ASPX cookie.

        :param str challenge_id:        The challenge ID we got from logging in.
        :param str challenge_secret:    The challenge secret we got from logging in.
        :param str device_serial:       The device serial of this running Kodi instance.

        :returns:                       An ASPX token.
        :rtype: str
        """
        reply = util.http_post(
            'https://{domain}/{env}/login.aspx'.format(domain=self._tenant.get('domain'),
                                                       env=self._tenant.get('env')),
            form=dict(
                secret=challenge_id + '\t' + challenge_secret,
                uid=device_serial,
                app=self._tenant.get('app'),
            )
        )

        # We got redirected, and the last response doesn't contain the cookie we need.
        # We need to get it from the redirect history.
        return reply.history[0].cookies.get('.ASPXAUTH')

    def _get_sapi_token(self, aspx_token):
        """ Get a SAPI token based on the ASPX cookie.

        :param str aspx_token:          The ASPX cookie we can use to authenticate.

        :returns:                        A SAPI token.
        :rtype: str
        """
        reply = util.http_get('https://{domain}/{env}/capi.aspx?z=ssotoken'.format(domain=self._tenant.get('domain'),
                                                                                   env=self._tenant.get('env')),
                              token_cookie=aspx_token)

        return json.loads(reply.text).get('ssotoken')

    def _get_jwt_token(self, sapi_token, device_name, device_serial):
        """ Get a JWT token.

        :param str sapi_token:          The SAPI token we got when authenticating.
        :param str device_name:         The name of this device.
        :param str device_serial:       The serial number of this device.

        :returns:                       A JWT token.
        :rtype: str
        """
        reply = util.http_post(SOLOCOO_API + '/session',
                               data=dict(
                                   sapiToken=sapi_token,
                                   deviceModel=device_name,
                                   deviceType="PC",
                                   deviceSerial=device_serial,
                                   osVersion="Linux undefined",
                                   appVersion="84.0",
                                   memberId="0",
                                   brand=self._tenant.get('app'),
                               ))
        return json.loads(reply.text).get('token')

    def get_tokens(self):
        """ Return the tokens.

        :return:
        :rtype: AccountStorage
        """
        return self._account

    def logout(self):
        """ Clear the session tokens. """
        self._account.aspx_token = None
        self._account.jwt_token = None
        self._account.challenge_id = None
        self._account.challenge_secret = None

        self._save_cache()

    def list_entitlements(self):
        """ Fetch a list of entitlements on this account.

        :rtype: dict
        """
        try:
            reply = util.http_get(SOLOCOO_API + '/entitlements', token_bearer=self._account.jwt_token)
        except InvalidTokenException:
            self.login(True)
            reply = util.http_get(SOLOCOO_API + '/entitlements', token_bearer=self._account.jwt_token)

        entitlements = json.loads(reply.text)

        return dict(
            products=[product.get('id') for product in entitlements.get('products')],
            offers=[offer.get('id') for offer in entitlements.get('offers')],
            assets=[asset.get('id') for asset in entitlements.get('assets')],
        )

    def list_devices(self):
        """ Fetch a list of devices that are registered on this account.

        :rtype: list[dict]
        """
        reply = util.http_get(SOLOCOO_API + '/devices', token_bearer=self._account.jwt_token)

        devices = json.loads(reply.text)
        return devices

    def remove_device(self, uid):
        """ Remove the specified device.

        :param str uid:                 The ID of the device to remove.
        """
        util.http_post(SOLOCOO_API + '/devices', token_bearer=self._account.jwt_token,
                       data={
                           'delete': [uid]
                       })

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
