import hashlib
import time

from ..constants import *

__author__ = 'bromix'


class AccessManager(object):
    def __init__(self, settings):
        self._settings = settings
        pass

    def has_login_credentials(self):
        """
        Returns True if we have a username and password.
        :return: True if username and password exists
        """
        username = self._settings.get_string(SETTING_LOGIN_USERNAME, '')
        password = self._settings.get_string(SETTING_LOGIN_PASSWORD, '')
        return username != '' and password != ''

    def get_login_credentials(self):
        """
        Returns the username and password (Tuple)
        :return: (username, password)
        """
        username = self._settings.get_string(SETTING_LOGIN_USERNAME, '')
        password = self._settings.get_string(SETTING_LOGIN_PASSWORD, '')
        return username, password

    def is_new_login_credential(self, update_hash=True):
        """
        Returns True if username or/and password are new.
        :return:
        """
        username = self._settings.get_string(SETTING_LOGIN_USERNAME, '')
        password = self._settings.get_string(SETTING_LOGIN_PASSWORD, '')

        m = hashlib.md5()
        m.update(username.encode('utf-8')+password.encode('utf-8'))
        current_hash = m.hexdigest()
        old_hash = self._settings.get_string(SETTING_LOGIN_HASH, '')
        if current_hash != old_hash:
            if update_hash:
                self._settings.set_string(SETTING_LOGIN_HASH, current_hash)
                pass
            return True

        return False

    def get_access_token(self):
        """
        Returns the access token for some API
        :return: access_token
        """
        return self._settings.get_string(SETTING_ACCESS_TOKEN, '')

    def is_access_token_expired(self):
        """
        Returns True if the access_token is expired otherwise False.
        If no expiration date was provided and an access_token exists
        this method will always return True
        :return:
        """

        # with no access_token it must be expired
        if not self._settings.get_string(SETTING_ACCESS_TOKEN, ''):
            return True

        # in this case no expiration date was set
        expires = self._settings.get_int(SETTING_ACCESS_TOKEN_EXPIRES, -1)
        if expires == -1:
            return False

        now = time.time()
        return expires <= now

    def update_access_token(self, access_token, time_in_seconds=None):
        """
        Updates the old access token with the new one.
        :param access_token:
        :return:
        """
        self._settings.set_string(SETTING_ACCESS_TOKEN, access_token)
        if time_in_seconds is not None:
            self._settings.set_int(SETTING_ACCESS_TOKEN_EXPIRES, int(time_in_seconds))
            pass
        pass

    pass
