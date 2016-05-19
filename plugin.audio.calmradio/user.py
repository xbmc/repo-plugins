from config import config
import requests
import json
import time


LOGIN_EXPIRATION = 60 * 60 *24


class User(object):
    def __init__(self, plugin):
        self.plugin = plugin
        self.auth = plugin.get_storage('auth', TTL=24)
        self.username = None
        self.password = None
        self.token = None

    @staticmethod
    def get_json(url):
        r = requests.get(url)
        if r.status_code == 200:
            return json.loads(r.text)

    def is_authenticated(self):
        """
        Checks if user is already logged in
        :return: True if user is logged in, False otherwise
        """
        if (self.plugin.get_setting('username') and
                self.plugin.get_setting('password') and
                'token' in self.auth and
                time.time() - self.auth['timestamp'] < LOGIN_EXPIRATION):
                    self.plugin.log.info('User is authenticated')
                    return True

        self.plugin.log.info('User is not authenticated')
        return False

    def check_sua(self):
        """
        Verifies that user is not connected already on other devices
        :return: True if user is already connected, False otherwise
        """

        username = self.plugin.get_setting('username')
        password = self.plugin.get_setting('password')

        # validate input:
        if username and password:
            # check single user authentication:
            return self.get_json(config['urls']['calm_sua_api'].format(
                username,
                password
            ))['detected']

    def authenticate(self):
        """
        Authenticates user
        :return: True if user is logged in, False otherwise
        """

        self.username = self.plugin.get_setting('username')
        self.password = self.plugin.get_setting('password')

        # validate input:
        if self.username and self.password:
            # check if user is already logged in
            if self.is_authenticated():
                self.token = self.auth['token']
                return True

            # verify that user is not already connected:
            if not self.check_sua():
                # authenticate:
                response = self.get_json(config['urls']['calm_auth_api'].format(
                    self.username,
                    self.password
                ))

                # authentication failed:
                if 'error' in response:
                    return False

                # authentication succeeded:
                self.auth['timestamp'] = time.time()
                self.auth['token'] = response['token']
                self.token = response['token']
                self.auth.sync()
                return True

        return False

    def invalidate(self):
        """
        Logs current user out
        :return:
        """
        del self.auth['timestamp']
        del self.auth['token']
        self.auth.sync()