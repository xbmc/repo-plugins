# -*- coding: utf-8 -*-
""" VTM GO Authentication API """

from __future__ import absolute_import, division, unicode_literals

import hashlib
import logging
import os
import re

import requests

from resources.lib.kodiwrapper import from_unicode

_LOGGER = logging.getLogger('vtmgoauth')


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
        _LOGGER.debug('Clearing token cache')
        path = os.path.join(self._kodi.get_userdata_path(), 'token.json')
        if self._kodi.check_if_path_exists(path):
            self._kodi.delete_file(path)
        self._token = None

    def get_token(self):
        """ Return a JWT that can be used to authenticate the user.
        :rtype str
        """
        userdata_path = self._kodi.get_userdata_path()

        # Don't return a token when we have no password or username.
        if not self._kodi.get_setting('username') or not self._kodi.get_setting('password'):
            _LOGGER.debug('Skipping since we have no username or password')
            return None

        # Return if we already have the token in memory.
        if self._token:
            _LOGGER.debug('Returning token from memory')
            return self._token

        # Try to load from cache
        path = os.path.join(userdata_path, 'token.json')
        if self._kodi.check_if_path_exists(path):
            _LOGGER.debug('Returning token from cache')

            with self._kodi.open_file(path) as fdesc:
                self._token = fdesc.read()

            if self._token:
                return self._token

        # Authenticate with VTM GO and store the token
        self._token = self._login()
        _LOGGER.debug('Returning token from VTM GO')

        # Make sure the path exists
        if not self._kodi.check_if_path_exists(userdata_path):
            self._kodi.mkdirs(userdata_path)

        with self._kodi.open_file(path, 'w') as fdesc:
            fdesc.write(from_unicode(self._token))

        return self._token

    def get_profile(self):
        """ Return the profile that is currently selected. """
        profile = self._kodi.get_setting('profile')
        try:
            return profile.split(':')[0]
        except (IndexError, AttributeError):
            return None

    def _login(self):
        """ Executes a login and returns the JSON Web Token.
        :rtype str
        """
        # Create new session object. This keeps the cookies across requests.
        session = requests.sessions.session()

        # Yes, we have accepted the cookies
        session.cookies.set('pws', 'functional|analytics|content_recommendation|targeted_advertising|social_media')
        session.cookies.set('pwv', '1')

        # Start login flow
        response = session.get('https://vtm.be/vtmgo/aanmelden?redirectUrl=https://vtm.be/vtmgo', proxies=self._proxies)
        response.raise_for_status()

        # Send login credentials
        response = session.post('https://login2.vtm.be/login/emailfirst/password?client_id=vtm-go-web', data={
            'userName': self._kodi.get_setting('username'),
            'password': self._kodi.get_setting('password'),
            'jsEnabled': 'true',
        }, proxies=self._proxies)
        response.raise_for_status()

        if 'errorBlock-OIDC-004' in response.text:  # E-mailadres is niet gekend.
            raise InvalidLoginException()

        if 'errorBlock-OIDC-003' in response.text:  # Wachtwoord is niet correct.
            raise InvalidLoginException()

        if 'OIDC-999' in response.text:  # Ongeldige login.
            raise InvalidLoginException()

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
        response = session.post('https://vtm.be/vtmgo/login-callback', data={
            'state': state,
            'code': code,
        }, proxies=self._proxies)
        response.raise_for_status()

        # Get JWT from cookies
        self._token = session.cookies.get('lfvp_auth')

        return self._token
