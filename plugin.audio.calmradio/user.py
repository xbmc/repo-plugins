from xbmcaddon import Addon
from config import config
from xbmc import log
import requests
import json
import time


ADDON = Addon()
LOGIN_EXPIRATION = 60 * 60 * 24


class User(object):
    def __init__(self):
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
        if (ADDON.getSetting('username') and
                ADDON.getSetting('password') and
                ADDON.getSetting('token') and
                time.time() - float(ADDON.getSetting('timestamp')) < LOGIN_EXPIRATION):
                    log('User is authenticated')
                    return True

        log('User is not authenticated')
        return False

    def check_sua(self):
        """
        Verifies that user is not connected already on other devices
        :return: True if user is already connected, False otherwise
        """

        username = ADDON.getSetting('username')
        password = ADDON.getSetting('password')

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

        self.username = ADDON.getSetting('username')
        self.password = ADDON.getSetting('password')

        # validate input:
        if self.username and self.password:
            # check if user is already logged in
            if self.is_authenticated():
                self.token = ADDON.getSetting('token')
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
                ADDON.setSetting('timestamp', str(time.time()))
                ADDON.setSetting('token', response['token'])
                self.token = response['token']
                return True

        return False

    def invalidate(self):
        """
        Logs current user out
        :return:
        """
        ADDON.setSetting('timestamp', None)
        ADDON.setSetting('token', None)
