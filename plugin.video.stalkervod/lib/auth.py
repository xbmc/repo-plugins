"""Module for auth"""
from __future__ import absolute_import, division, unicode_literals
import os
import json
import dataclasses
import requests
import xbmcvfs
import xbmcgui
from .globals import G
from .utils import Logger


@dataclasses.dataclass
class Token:
    """Token"""
    value: str = None


class Auth:
    """Auth API"""

    __TOKEN_FILE = 'token.json'

    def __init__(self):
        self.__token_path = os.path.join(G.addon_config.token_path, self.__TOKEN_FILE)
        self.__token = Token()
        self.__load_cache()
        self.__url = G.portal_config.portal_url
        self.__mac_cookie = G.portal_config.mac_cookie
        self.__referrer = G.portal_config.server_address

    def get_token(self, refresh_token):
        """Get Token"""
        Logger.debug('Token path {}'.format(self.__token_path))
        if self.__token.value:
            if refresh_token:
                self.__refresh_token()
            return self.__token.value
        self.clear_cache()
        Logger.debug('Getting token from {}'.format(self.__url))
        response = requests.get(url=self.__url,
                                headers={'Cookie': self.__mac_cookie, 'X-User-Agent': 'Model: MAG250; Link: WiFi',
                                         'Referrer': self.__referrer},
                                params={'type': 'stb', 'action': 'handshake'},
                                timeout=30
                                )
        if response.status_code != 200 or response.text.find('Authorization failed') != -1:
            Logger.error('Error getting token, statusCode={}'.format(response.status_code))
            Logger.debug('Token Response {}'.format(response.text))
            xbmcgui.Dialog().ok(G.addon_config.name, "Error getting token")
            raise Exception
        self.__token.value = response.json()['js']['token']
        self.__refresh_token()
        self.__save_cache()
        return self.__token.value

    def clear_cache(self):
        """Clear token from cache"""
        self.__token = Token()
        if xbmcvfs.exists(self.__token_path):
            xbmcvfs.delete(self.__token_path)

    def __refresh_token(self):
        """Refresh token"""
        Logger.debug('Refreshing token')
        requests.get(url=self.__url,
                     headers={'Cookie': self.__mac_cookie, 'Authorization': 'Bearer ' + self.__token.value,
                              'X-User-Agent': 'Model: MAG250; Link: WiFi', 'Referrer': self.__referrer},
                     params={
                         'type': 'stb',
                         'action': 'get_profile',
                         'hd': '1',
                         'auth_second_step': '0',
                         'num_banks': '1',
                         'stb_type': 'MAG250',
                         'image_version': '216',
                         'hw_version': '1.7-BD-00',
                         'not_valid_token': '0',
                         'device_id': G.portal_config.device_id,
                         'device_id2': G.portal_config.device_id_2,
                         'signature': G.portal_config.signature,
                         'sn': G.portal_config.serial_number,
                         'ver': 'ImageDescription:%200.2.18-r23-pub-254;%20ImageDate:%20Wed%20Aug%2029%2010:49:26'
                                '%20EEST%202018;%20PORTAL%20version:%205.1.1;%20API%20Version:%20JS%20API'
                                '%20version:%20328;%20STB%20API%20version:%20134;%20Player%20Engine%20version'
                                ':%200x566'
                     },
                     timeout=30
                     )
        requests.get(url=self.__url,
                     headers={'Cookie': self.__mac_cookie, 'Authorization': 'Bearer ' + self.__token.value,
                              'X-User-Agent': 'Model: MAG250; Link: WiFi', 'Referrer': self.__referrer},
                     params={
                         'type': 'watchdog', 'action': 'get_events',
                         'init': '0', 'cur_play_type': '1', 'event_active_id': '0'
                     },
                     timeout=30
                     )

    def __load_cache(self):
        """ Load tokens from cache """
        Logger.debug('Loading token from cache')
        try:
            with xbmcvfs.File(self.__token_path, 'r') as f:
                self.__token.__dict__ = json.loads(f.read())
        except (IOError, TypeError, ValueError):
            Logger.warn('We could not use the cache since it is invalid or non-existent.')

    def __save_cache(self):
        """ Store tokens in cache """
        Logger.debug('Saving token to cache')
        with xbmcvfs.File(self.__token_path, 'w') as f:
            json.dump(self.__token.__dict__, f, indent=2)
