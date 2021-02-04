# -*- coding: utf-8 -*-
""" Player module """

from __future__ import absolute_import, division, unicode_literals

import logging

from resources.lib import kodiutils
from resources.lib.modules.menu import Menu
from resources.lib.solocoo import Channel, Program
from resources.lib.solocoo.auth import AuthApi
from resources.lib.solocoo.channel import ChannelApi
from resources.lib.solocoo.exceptions import InvalidTokenException, NotAvailableInOfferException, UnavailableException

_LOGGER = logging.getLogger(__name__)


class Player:
    """ Code responsible for playing media """

    def __init__(self):
        """ Initialise object. """
        self._auth = AuthApi(username=kodiutils.get_setting('username'),
                             password=kodiutils.get_setting('password'),
                             tenant=kodiutils.get_setting('tenant'),
                             token_path=kodiutils.get_tokens_path())
        self._channel_api = ChannelApi(self._auth)

    def play_asset(self, asset_id):
        """ Play an asset (can be a program of a live channel).

        :param string asset_id:         The ID of the asset to play.
        """
        # Get asset info
        if len(asset_id) == 32:
            # a locId is 32 chars
            asset = self._channel_api.get_asset_by_locid(asset_id)
        else:
            # an asset_id is 40 chars
            asset = self._channel_api.get_asset(asset_id)

        if isinstance(asset, Program):
            item = Menu.generate_titleitem_program(asset)
        elif isinstance(asset, Channel):
            item = Menu.generate_titleitem_channel(asset)
        else:
            raise Exception('Unknown asset type: %s' % asset)

        # Get stream info
        try:
            stream_info = self._channel_api.get_stream(asset.uid)
        except InvalidTokenException:
            # Retry with fresh tokens
            self._auth.login(True)
            stream_info = self._channel_api.get_stream(asset.uid)
        except (NotAvailableInOfferException, UnavailableException) as exc:
            _LOGGER.error(exc)
            kodiutils.ok_dialog(message=kodiutils.localize(30712))  # The video is unavailable and can't be played right now.
            kodiutils.end_of_directory()
            return

        license_key = self._create_license_key(stream_info.drm_license_url, key_headers={'Content-Type': 'application/octet-stream'})

        _LOGGER.debug('Starting playing %s with license key %s', stream_info.url, license_key)
        kodiutils.play(stream_info.url, license_key, item.title, item.art_dict, item.info_dict, item.prop_dict)

    @staticmethod
    def _create_license_key(key_url, key_type='R', key_headers=None, key_value=None):
        """ Create a license key string that we need for inputstream.adaptive.

        :param str key_url:
        :param str key_type:
        :param dict[str, str] key_headers:
        :param str key_value:

        :returns:                       A license key string that can be passed to inputstream.adaptive.
        :rtype: str
        """
        try:  # Python 3
            from urllib.parse import quote, urlencode
        except ImportError:  # Python 2
            from urllib import quote, urlencode

        header = ''
        if key_headers:
            header = urlencode(key_headers)

        if key_type in ('A', 'R', 'B'):
            key_value = key_type + '{SSM}'
        elif key_type == 'D':
            if 'D{SSM}' not in key_value:
                raise ValueError('Missing D{SSM} placeholder')
            key_value = quote(key_value)

        return '%s|%s|%s|' % (key_url, header, key_value)
