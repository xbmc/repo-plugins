# -*- coding: utf-8 -*-
""" Player module """

from __future__ import absolute_import, division, unicode_literals

import logging

from resources.lib import kodiutils
from resources.lib.modules.menu import Menu
from resources.lib.viervijfzes import CHANNELS, ResolvedStream
from resources.lib.viervijfzes.auth import AuthApi
from resources.lib.viervijfzes.aws.cognito_idp import AuthenticationException, InvalidLoginException
from resources.lib.viervijfzes.content import CACHE_PREVENT, ContentApi, GeoblockedException, UnavailableException

try:  # Python 3
    from urllib.parse import quote, urlencode
except ImportError:  # Python 2
    from urllib import quote, urlencode

_LOGGER = logging.getLogger(__name__)


class Player:
    """ Code responsible for playing media """

    def __init__(self):
        """ Initialise object """
        auth = AuthApi(kodiutils.get_setting('username'), kodiutils.get_setting('password'), kodiutils.get_tokens_path())
        self._api = ContentApi(auth, cache_path=kodiutils.get_cache_path())

        # Workaround for Raspberry Pi 3 and older
        kodiutils.set_global_setting('videoplayer.useomxplayer', True)

    @staticmethod
    def live(channel):
        """ Play the live channel.
        :type channel: string
        """
        # TODO: this doesn't work correctly, playing a live program from the PVR won't play something from the beginning
        # Lookup current program
        # broadcast = self._epg.get_broadcast(channel, datetime.datetime.now().isoformat())
        # if broadcast and broadcast.video_url:
        #     self.play_from_page(broadcast.video_url)
        #     return

        channel_name = CHANNELS.get(channel, dict(name=channel))
        kodiutils.ok_dialog(message=kodiutils.localize(30718, channel=channel_name.get('name')))  # There is no live stream available for {channel}.
        kodiutils.end_of_directory()

    def play_from_page(self, path):
        """ Play the requested item.
        :type path: string
        """
        if not path:
            kodiutils.ok_dialog(message=kodiutils.localize(30712))  # The video is unavailable...
            return

        # Get episode information
        episode = self._api.get_episode(path, cache=CACHE_PREVENT)
        resolved_stream = None

        if episode is None:
            kodiutils.ok_dialog(message=kodiutils.localize(30712))
            return

        if episode.stream:
            # We already have a resolved stream. Nice!
            # We don't need credentials for these streams.
            resolved_stream = ResolvedStream(
                uuid=episode.uuid,
                url=episode.stream,
            )
            _LOGGER.debug('Already got a resolved stream: %s', resolved_stream)

        if episode.uuid:
            # Lookup the stream
            resolved_stream = self._resolve_stream(episode.uuid, episode.islongform)
            _LOGGER.debug('Resolved stream: %s', resolved_stream)

        if resolved_stream:
            titleitem = Menu.generate_titleitem(episode)
            if resolved_stream.license_url:
                # Generate license key
                license_key = self.create_license_key(resolved_stream.license_url,
                                                      key_headers=dict(
                                                          customdata=resolved_stream.auth,
                                                      ))
            else:
                license_key = None

            kodiutils.play(resolved_stream.url,
                           resolved_stream.stream_type,
                           license_key,
                           info_dict=titleitem.info_dict,
                           art_dict=titleitem.art_dict,
                           prop_dict=titleitem.prop_dict)

    def play(self, uuid, islongform):
        """ Play the requested item.
        :type uuid: string
        :type islongform: bool
        """
        if not uuid:
            kodiutils.ok_dialog(message=kodiutils.localize(30712))  # The video is unavailable...
            return

        # Lookup the stream
        resolved_stream = self._resolve_stream(uuid, islongform)
        if resolved_stream.license_url:
            # Generate license key
            license_key = self.create_license_key(resolved_stream.license_url, key_headers=dict(
                customdata=resolved_stream.auth,
            ))
        else:
            license_key = None

        kodiutils.play(resolved_stream.url, resolved_stream.stream_type, license_key)

    @staticmethod
    def _resolve_stream(uuid, islongform):
        """ Resolve the stream for the requested item
        :type uuid: string
        :type islongform: bool
        """
        try:
            # Check if we have credentials
            if not kodiutils.get_setting('username') or not kodiutils.get_setting('password'):
                confirm = kodiutils.yesno_dialog(
                    message=kodiutils.localize(30701))  # To watch a video, you need to enter your credentials. Do you want to enter them now?
                if confirm:
                    kodiutils.open_settings()
                kodiutils.end_of_directory()
                return None

            # Fetch an auth token now
            try:
                auth = AuthApi(kodiutils.get_setting('username'), kodiutils.get_setting('password'), kodiutils.get_tokens_path())

                # Get stream information
                resolved_stream = ContentApi(auth).get_stream_by_uuid(uuid, islongform)
                return resolved_stream

            except (InvalidLoginException, AuthenticationException) as ex:
                _LOGGER.exception(ex)
                kodiutils.ok_dialog(message=kodiutils.localize(30702, error=str(ex)))
                kodiutils.end_of_directory()
                return None

        except GeoblockedException:
            kodiutils.ok_dialog(message=kodiutils.localize(30710))  # This video is geo-blocked...
            return None

        except UnavailableException:
            kodiutils.ok_dialog(message=kodiutils.localize(30712))  # The video is unavailable...
            return None

    @staticmethod
    def create_license_key(key_url, key_type='R', key_headers=None, key_value=None):
        """ Create a license key string that we need for inputstream.adaptive.

        :param str key_url:
        :param str key_type:
        :param dict[str, str] key_headers:
        :param str key_value:
        :rtype: str
        """
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
