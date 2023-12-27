"""Module for auth"""
from __future__ import absolute_import, division, unicode_literals
import os
import json
import dataclasses
import requests
from .globals import G
from .utils import Logger


@dataclasses.dataclass
class Token:
    """Token"""
    value: str = None


def _refresh_token(token):
    """Refresh token"""
    _url = G.portal_config.portal_base_url + G.portal_config.context_path
    _mac_cookie = G.portal_config.mac_cookie
    _portal_url = G.portal_config.portal_url
    requests.get(url=_url,
                 headers={'Cookie': _mac_cookie, 'Authorization': 'Bearer ' + token,
                          'X-User-Agent': 'Model: MAG250; Link: WiFi', 'Referrer': _portal_url},
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
    requests.get(url=_url,
                 headers={'Cookie': _mac_cookie, 'Authorization': 'Bearer ' + token,
                          'X-User-Agent': 'Model: MAG250; Link: WiFi', 'Referrer': _portal_url},
                 params={
                     'type': 'watchdog', 'action': 'get_events',
                     'init': '0', 'cur_play_type': '1', 'event_active_id': '0'
                 },
                 timeout=30
                 )


class Auth:
    """Auth API"""

    TOKEN_FILE = 'token.json'

    def __init__(self):
        self._token_path = G.addon_config.token_path
        self._token = Token()
        self._load_cache()

    def get_token(self, refresh_token):
        """Get Token"""
        Logger.debug('Token path {}'.format(self._token_path))
        if self._token.value:
            if refresh_token:
                _refresh_token(self._token.value)
            return self._token.value

        _url = G.portal_config.portal_base_url + G.portal_config.context_path
        _mac_cookie = G.portal_config.mac_cookie
        _portal_url = G.portal_config.portal_url
        token = requests.get(url=_url,
                             headers={'Cookie': _mac_cookie, 'X-User-Agent': 'Model: MAG250; Link: WiFi',
                                      'Referrer': _portal_url},
                             params={'type': 'stb', 'action': 'handshake'},
                             timeout=30
                             ).json()['js']['token']
        requests.get(url=_url,
                     headers={'Cookie': _mac_cookie, 'Authorization': 'Bearer ' + token,
                              'X-User-Agent': 'Model: MAG250; Link: WiFi', 'Referrer': _portal_url},
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
        requests.get(url=_url,
                     headers={'Cookie': _mac_cookie, 'Authorization': 'Bearer ' + token,
                              'X-User-Agent': 'Model: MAG250; Link: WiFi', 'Referrer': _portal_url},
                     params={
                         'type': 'watchdog', 'action': 'get_events',
                         'init': '0', 'cur_play_type': '1', 'event_active_id': '0'
                     },
                     timeout=30
                     )
        self._token.value = token
        self._save_cache()
        return self._token.value

    def clear_cache(self):
        """Clear token from cache"""
        self._token = Token()
        if os.path.exists(os.path.join(self._token_path, self.TOKEN_FILE)):
            os.remove(os.path.join(self._token_path, self.TOKEN_FILE))

    def _load_cache(self):
        """ Load tokens from cache """
        try:
            with open(os.path.join(self._token_path, self.TOKEN_FILE), 'r') as f_desc:
                self._token.__dict__ = json.loads(f_desc.read())  # pylint: disable=attribute-defined-outside-init
        except (IOError, TypeError, ValueError):
            Logger.warn('We could not use the cache since it is invalid or non-existent.')

    def _save_cache(self):
        """ Store tokens in cache """
        if not os.path.exists(self._token_path):
            os.makedirs(self._token_path)

        with open(os.path.join(self._token_path, self.TOKEN_FILE), 'w') as f_desc:
            json.dump(self._token.__dict__, f_desc, indent=2)
