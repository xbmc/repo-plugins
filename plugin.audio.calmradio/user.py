from config import config
from xbmc import log
import requests
import json
import time


LOGIN_EXPIRATION = 60 * 60 * 24


class User(object):
    def __init__(self, addon):
        self.addon = addon
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
        if (self.addon.getSetting('username') and
                self.addon.getSetting('password') and
                self.addon.getSetting('token') and
                time.time() - float(self.addon.getSetting('timestamp')) < LOGIN_EXPIRATION):
                    log('User is authenticated')
                    return True

        log('User is not authenticated')
        return False

    def check_sua(self):
        """
        Verifies that user is not connected already on other devices
        :return: True if user is already connected, False otherwise
        """

        username = self.addon.getSetting('username')
        password = self.addon.getSetting('password')

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

        self.username = self.addon.getSetting('username')
        self.password = self.addon.getSetting('password')

        # validate input:
        if self.username and self.password:
            # check if user is already logged in
            if self.is_authenticated():
                self.token = self.addon.getSetting('token')
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
                self.addon.setSetting('timestamp', str(time.time()))
                self.addon.setSetting('token', response['token'])
                self.token = response['token']
                return True

        return False

    def invalidate(self):
        """
        Logs current user out
        :return:
        """
        self.addon.setSetting('timestamp', None)
        self.addon.setSetting('token', None)
