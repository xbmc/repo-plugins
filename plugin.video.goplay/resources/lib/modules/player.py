# -*- coding: utf-8 -*-
""" Player module """

from __future__ import absolute_import, division, unicode_literals

import logging

from resources.lib import kodiutils
from resources.lib.goplay.auth import AuthApi
from resources.lib.goplay.aws.cognito_idp import AuthenticationException, InvalidLoginException
from resources.lib.goplay.content import ContentApi, GeoblockedException, UnavailableException

_LOGGER = logging.getLogger(__name__)


class Player:
    """ Code responsible for playing media """

    def __init__(self):
        """ Initialise object """
        auth = AuthApi(kodiutils.get_setting('username'), kodiutils.get_setting('password'), kodiutils.get_tokens_path())
        self._api = ContentApi(auth, cache_path=kodiutils.get_cache_path())

        # Workaround for Raspberry Pi 3 and older
        kodiutils.set_global_setting('videoplayer.useomxplayer', True)

    def live(self, uuid):
        """ Play the live channel.
        :type uuid: str
        """
        # TODO: this doesn't work correctly, playing a live program from the PVR won't play something from the beginning
        # Lookup current program
        # broadcast = self._epg.get_broadcast(channel, datetime.datetime.now().isoformat())
        # if broadcast and broadcast.video_url:
        #     self.play_from_page(broadcast.video_url)
        #     return

        self.play(uuid, 'live_channel')

    def play(self, uuid, content_type):
        """ Play the requested item.
        :type uuid: str
        :type content_type: str
        """
        if not uuid:
            kodiutils.ok_dialog(message=kodiutils.localize(30712))  # The video is unavailable...
            return

        # Lookup the stream
        resolved_stream = self._resolve_stream(uuid, content_type)
        if resolved_stream:
            kodiutils.play(resolved_stream.url, resolved_stream.stream_type, resolved_stream.license_key)
        return

    @staticmethod
    def _resolve_stream(uuid, content_type):
        """ Resolve the stream for the requested item
        :type uuid: str
        :type content_type: str
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
                resolved_stream = ContentApi(auth).get_stream(uuid, content_type)
                return resolved_stream

            except (InvalidLoginException, AuthenticationException) as ex:
                _LOGGER.exception(ex)
                kodiutils.ok_dialog(message=kodiutils.localize(30702, error=str(ex)))
                kodiutils.end_of_directory()
                return None

        except GeoblockedException as ex:
            kodiutils.ok_dialog(message=kodiutils.localize(30710, error=str(ex)))  # This video is geo-blocked...
            kodiutils.end_of_directory()
            return None

        except UnavailableException:
            kodiutils.ok_dialog(message=kodiutils.localize(30712))  # The video is unavailable...
            kodiutils.end_of_directory()
            return None
