# -*- coding: utf-8 -*-
""" VTM GO Authentication API """

from __future__ import absolute_import, division, unicode_literals

import hashlib
import json
import random
import requests

from resources.lib.kodiwrapper import LOG_DEBUG, from_unicode, LOG_INFO


class InvalidLoginException(Exception):
    """ Is thrown when the credentials are invalid """


class LoginErrorException(Exception):
    """ Is thrown when we could not login """

    def __init__(self, code):
        super(LoginErrorException, self).__init__()
        self.code = code


class VtmGoAuth:
    """ VTM GO Authentication API """

    def __init__(self, kodi):
        """ Initialise object
        :type kodi: resources.lib.kodiwrapper.KodiWrapper
        """
        self._kodi = kodi
        self._proxies = kodi.get_proxies()

        self._token = None
        # self._name = None
        # self._accountId = None

    def has_credentials_changed(self):
        """ Check if credentials have changed """
        old_hash = self._kodi.get_setting('credentials_hash')
        new_hash = ''
        if self._kodi.get_setting('username') or self._kodi.get_setting('password'):
            new_hash = hashlib.md5((self._kodi.get_setting('username') + self._kodi.get_setting('password')).encode('utf-8')).hexdigest()
        if new_hash != old_hash:
            self._kodi.set_setting('credentials_hash', new_hash)
            return True
        return False

    def clear_token(self):
        """ Remove the cached JWT. """
        self._kodi.log('Clearing token cache', LOG_DEBUG)
        self._token = None
        path = self._kodi.get_userdata_path() + 'token.json'
        if self._kodi.check_if_path_exists(path):
            self._kodi.delete_file(path)
        self._kodi.set_setting('profile', None)

    def get_token(self):
        """ Return a JWT that can be used to authenticate the user.
        :rtype str
        """
        # Don't return a token when we have no password or username.
        if not self._kodi.get_setting('username') or not self._kodi.get_setting('password'):
            self._kodi.log('Skipping since we have no username or password', LOG_INFO)
            return None

        # Return if we already have the token in memory.
        if self._token:
            self._kodi.log('Returning token from memory', LOG_DEBUG)
            return self._token

        # Try to load from cache
        path = self._kodi.get_userdata_path() + 'token.json'
        if self._kodi.check_if_path_exists(path):
            self._kodi.log('Returning token from cache', LOG_DEBUG)

            with self._kodi.open_file(path) as fdesc:
                self._token = fdesc.read()

            if self._token:
                return self._token

        # Authenticate with VTM GO and store the token
        self._token = self._login()
        self._kodi.log('Returning token from VTM GO', LOG_DEBUG)

        with self._kodi.open_file(path, 'w') as fdesc:
            fdesc.write(from_unicode(self._token))

        return self._token

    def get_profile(self):
        """ Return the profile that is currently selected. """
        profile = self._kodi.get_setting('profile')
        try:
            return profile.split(':')[0]
        except IndexError:
            return None

    def _login(self):
        """ Executes a login and returns the JSON Web Token.
        :rtype str
        """
        # Create new session object. This keeps the cookies across requests.
        session = requests.sessions.session()

        # Get login form. This sets some cookies we need.
        session.get('https://login.persgroep.net/authorize', params={
            'redirect_uri': 'vtmgo://callback/oidc',
            'client_id': 'vtm-go-android',
            'response_type': 'code',
            'state': self._generate_random_id(22),
            'nonce': self._generate_random_id(22),
            'scope': 'openid profile'
        }, headers={
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Mobile Safari/537.36'
        }, proxies=self._proxies)

        # Now, send the login details. We will be redirected to vtmgo:// when we succeed. We then can extract an authorizationCode that we need to continue.
        try:
            response = session.post('https://login2.vtm.be/login/emailfirst/password?client_id=vtm-go-android', data={
                'userName': self._kodi.get_setting('username'),
                'password': self._kodi.get_setting('password'),
                'jsEnabled': 'true',
            }, proxies=self._proxies)

            if 'errorBlock-OIDC-004' in response.text:  # E-mailadres is niet gekend.
                raise InvalidLoginException()

            if 'errorBlock-OIDC-003' in response.text:  # Wachtwoord is niet correct.
                raise InvalidLoginException()

            if 'OIDC-999' in response.text:  # Ongeldige login.
                raise InvalidLoginException()

            raise LoginErrorException(code=100)  # Unknown error while logging in

        except requests.exceptions.InvalidSchema as exc:
            # We get back an url like this: vtmgo://callback/oidc?state=yyyyyyyyyyyyyyyyyyyyyy&code=xxxxxxxxxxxxxxxxxxxxxxxxxx-xxxxxxxxxxxxxxxx
            # I found no other way to get this url then by parsing the Exception message. :(
            import re
            matches = re.search(r"code=([^']+)", str(exc))
            if matches:
                code = matches.group(1)
            else:
                raise LoginErrorException(code=101)  # Could not extract authentication code

        # Okay, final stage. We now need to use our authorizationCode to get a valid JWT.
        response = session.post('https://lfvp-api.dpgmedia.net/authorize', json={
            'authorizationCode': code,
            'authorizationCodeCallbackUrl': 'vtmgo://callback/oidc',
            'clientId': 'vtm-go-android',
        }, headers={
            'x-app-version': '8',
            'x-persgroep-mobile-app': 'true',
            'x-persgroep-os': 'android',
            'x-persgroep-os-version': '23',
        }, proxies=self._proxies)

        if response.status_code == 426:
            raise LoginErrorException(code=102)  # Update required

        if response.status_code not in [200, 204]:
            raise Exception('Error %s.' % response.status_code)

        tokens = json.loads(response.text)

        self._token = tokens.get('jsonWebToken')
        # self._name = tokens.get('name')
        # self._accountId = tokens.get('accountId')

        return self._token

    @staticmethod
    def _generate_random_id(length=32):
        """ Generate a random id of the specified length.
        :type length: int
        :rtype str
        """
        letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        return ''.join(random.choice(letters) for i in range(length))
