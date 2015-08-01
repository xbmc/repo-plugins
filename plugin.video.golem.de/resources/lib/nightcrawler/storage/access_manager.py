__author__ = 'bromix'

import hashlib
import time


class AccessManager(object):
    ACCESS_SETTING_KEYS = ['access_token', 'refresh_token', 'expires_in']

    def __init__(self, settings):
        self._settings = settings
        pass

    def do_login_and_refresh_token(self, login_method, refresh_token_method):
        self.do_login(login_method)
        return self.do_refresh_token(refresh_token_method)

    def do_login(self, login_method):
        if not self._has_login_credentials():
            return {}

        if not self._is_new_login_credential():
            return self._get_access()

        username, password = self._get_login_credentials()
        access_data = login_method(username=username, password=password)
        self._update_access_data(access_data)
        return self._get_access()

    def _update_access_data(self, access_data):
        for key in self.ACCESS_SETTING_KEYS:
            if key in access_data:
                settings_id = 'login.%s' % key
                if key == 'expires_in':
                    self._settings.set_int(settings_id, access_data[key])
                    pass
                else:
                    self._settings.set_string(settings_id, access_data[key])
                    pass
                pass
            pass
        pass

    def do_refresh_token(self, refresh_token_method):
        if not self._has_refresh_token():
            return self._get_access()

        if not self._is_access_token_expired():
            return self._get_access()

        access_data = refresh_token_method(self._get_access())
        self._update_access_data(access_data)
        return self._get_access()

    def _get_access(self):
        result = {}
        for key in self.ACCESS_SETTING_KEYS:
            settings_id = 'login.%s' % key
            if key == 'expires_in':
                result[key] = self._settings.get_int(settings_id, -1)
                pass
            else:
                result[key] = self._settings.get_string(settings_id, u'')
                pass
            pass
        return result

    def _get_login_credentials(self):
        """
        Returns the username and password (Tuple)
        :return: (username, password)
        """
        username = self._settings.get_string(self._settings.LOGIN_USERNAME, '')
        password = self._settings.get_string(self._settings.LOGIN_PASSWORD, '')
        return username, password

    def _has_login_credentials(self):
        """
        Returns True if we have a username and password.
        :return: True if username and password exists
        """
        username, password = self._get_login_credentials()
        return username and password

    def _is_new_login_credential(self):
        """
        Returns True if username or/and password are new.
        :return:
        """
        username, password = self._get_login_credentials()

        m = hashlib.md5()
        m.update(username.encode('utf-8') + password.encode('utf-8'))
        current_hash = m.hexdigest()
        old_hash = self._settings.get_string(self._settings.LOGIN_HASH, '')
        if current_hash != old_hash:
            self._settings.set_string(self._settings.LOGIN_HASH, current_hash)
            return True

        return False

    def remove_login_credentials(self):
        self._settings.set_string(self._settings.LOGIN_USERNAME, '')
        self._settings.set_string(self._settings.LOGIN_PASSWORD, '')
        self._settings.set_string(self._settings.LOGIN_HASH, '')
        pass

    def get_access_token(self):
        """
        Returns the nightcrawler token for some API
        :return: access_token
        """
        return self._settings.get_string(self._settings.LOGIN_ACCESS_TOKEN, '')

    def _has_access_token(self):
        return self.get_access_token() != ''

    def get_refresh_token(self):
        """
        Returns the refresh token
        :return: refresh token
        """
        return self._settings.get_string(self._settings.LOGIN_REFRESH_TOKEN, '')

    def _has_refresh_token(self):
        return self.get_refresh_token() != ''

    def _is_access_token_expired(self):
        """
        Returns True if the access_token is expired otherwise False.
        If no expiration date was provided and an access_token exists
        this method will always return True
        :return:
        """

        # with no access_token it must be expired
        if not self._has_access_token():
            return True

        # in this case no expiration date was set
        expires = self._settings.get_int(self._settings.LOGIN_ACCESS_TOKEN_EXPIRES, -1)
        if expires == -1:
            return False

        now = int(time.time())
        return expires <= now

    def update_access_token(self, access_token, unix_timestamp=None, refresh_token=None):
        """
        Updates the old nightcrawler token with the new one.
        :param access_token:
        :return:
        """
        self._settings.set_string(self._settings.LOGIN_ACCESS_TOKEN, access_token)
        if unix_timestamp is not None:
            self._settings.set_int(self._settings.LOGIN_ACCESS_TOKEN_EXPIRES, int(unix_timestamp))
            pass

        if refresh_token is not None:
            self._settings.set_string(self._settings.LOGIN_REFRESH_TOKEN, refresh_token)
        pass

    pass
