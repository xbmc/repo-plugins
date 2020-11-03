# -*- coding: utf-8 -*-
""" Player module """

from __future__ import absolute_import, division, unicode_literals

import logging

from resources.lib import kodiutils
from resources.lib.kodiplayer import KodiPlayer
from resources.lib.streamz.api import Api
from resources.lib.streamz.auth import Auth
from resources.lib.streamz.exceptions import LimitReachedException, StreamGeoblockedException, StreamUnavailableException, UnavailableException
from resources.lib.streamz.stream import Stream

_LOGGER = logging.getLogger(__name__)


class Player:
    """ Code responsible for playing media """

    def __init__(self):
        """ Initialise object """
        self._auth = Auth(kodiutils.get_setting('username'),
                          kodiutils.get_setting('password'),
                          kodiutils.get_setting('loginprovider'),
                          kodiutils.get_setting('profile'),
                          kodiutils.get_tokens_path())
        self._api = Api(self._auth)
        self._stream = Stream(self._auth)

    def play(self, category, item):
        """ Play the requested item.

        :type category: string
        :type item: string
        """
        # Check if inputstreamhelper is correctly installed
        if not self._check_inputstream():
            kodiutils.end_of_directory()
            return

        try:
            # Get stream information
            resolved_stream = self._stream.get_stream(category, item)

        except StreamGeoblockedException:
            kodiutils.ok_dialog(message=kodiutils.localize(30710))  # This video is geo-blocked...
            kodiutils.end_of_directory()
            return

        except StreamUnavailableException:
            kodiutils.ok_dialog(message=kodiutils.localize(30712))  # The video is unavailable...
            kodiutils.end_of_directory()
            return

        except LimitReachedException:
            kodiutils.ok_dialog(message=kodiutils.localize(30713))  # You have reached the maximum amount of concurrent streams...
            kodiutils.end_of_directory()
            return

        info_dict = {
            'tvshowtitle': resolved_stream.program,
            'title': resolved_stream.title,
            'duration': resolved_stream.duration,
        }

        prop_dict = {}

        stream_dict = {
            'duration': resolved_stream.duration,
        }

        upnext_data = None

        # Lookup metadata
        try:
            if category in ['movies', 'oneoffs']:
                info_dict.update({'mediatype': 'movie'})

                # Get details
                movie_details = self._api.get_movie(item)
                if movie_details:
                    info_dict.update({
                        'plot': movie_details.description,
                        'year': movie_details.year,
                        'aired': movie_details.aired,
                    })

            elif category == 'episodes':
                info_dict.update({'mediatype': 'episode'})

                # There is no direct API to get episode details, so we go trough the cached program details
                program = self._api.get_program(resolved_stream.program_id)
                if program:
                    episode_details = self._api.get_episode_from_program(program, item)
                    if episode_details:
                        info_dict.update({
                            'plot': episode_details.description,
                            'season': episode_details.season,
                            'episode': episode_details.number,
                        })

                        # Lookup the next episode
                        next_episode_details = self._api.get_next_episode_from_program(program, episode_details.season, episode_details.number)

                        # Create the data for Up Next
                        if next_episode_details:
                            upnext_data = self.generate_upnext(episode_details, next_episode_details)

            else:
                _LOGGER.warning('Unknown category %s', category)

        except UnavailableException:
            # We continue without details.
            # This allows to play some programs that don't have metadata (yet).
            pass

        license_key = self._stream.create_license_key(resolved_stream.license_url)

        # Play this item
        kodiutils.play(resolved_stream.url, license_key, resolved_stream.title, {}, info_dict, prop_dict, stream_dict)

        # Wait for playback to start
        kodi_player = KodiPlayer()
        if not kodi_player.waitForPlayBack(url=resolved_stream.url):
            # Playback didn't start
            return

        # Send Up Next data
        if upnext_data and kodiutils.get_setting_bool('useupnext'):
            _LOGGER.debug("Sending Up Next data: %s", upnext_data)
            self.send_upnext(upnext_data)

    @staticmethod
    def _check_inputstream():
        """ Check if inputstreamhelper and inputstream.adaptive are fine.

        :rtype boolean
        """
        try:
            from inputstreamhelper import Helper
            is_helper = Helper('mpd', drm='com.widevine.alpha')
            if not is_helper.check_inputstream():
                # inputstreamhelper has already shown an error
                return False

        except ImportError:
            kodiutils.ok_dialog(message=kodiutils.localize(30708))  # Please reboot Kodi
            return False

        return True

    @staticmethod
    def generate_upnext(current_episode, next_episode):
        """ Construct the data for Up Next.

        :type current_episode: resources.lib.streamz.api.Episode
        :type next_episode: resources.lib.streamz.api.Episode
        """
        upnext_info = dict(
            current_episode=dict(
                episodeid=current_episode.episode_id,
                tvshowid=current_episode.program_id,
                title=current_episode.name,
                art={
                    'thumb': current_episode.cover,
                },
                season=current_episode.season,
                episode=current_episode.number,
                showtitle=current_episode.program_name,
                plot=current_episode.description,
                playcount=None,
                rating=None,
                firstaired=current_episode.aired[:10] if current_episode.aired else '',
                runtime=current_episode.duration,
            ),
            next_episode=dict(
                episodeid=next_episode.episode_id,
                tvshowid=next_episode.program_id,
                title=next_episode.name,
                art={
                    'thumb': next_episode.cover,
                },
                season=next_episode.season,
                episode=next_episode.number,
                showtitle=next_episode.program_name,
                plot=next_episode.description,
                playcount=None,
                rating=None,
                firstaired=next_episode.aired[:10] if next_episode.aired else '',
                runtime=next_episode.duration,
            ),
            play_url='plugin://plugin.video.streamz/play/catalog/episodes/%s' % next_episode.episode_id,
        )

        return upnext_info

    @staticmethod
    def send_upnext(upnext_info):
        """ Send a message to Up Next with information about the next Episode.

        :type upnext_info: object
        """
        from base64 import b64encode
        from json import dumps
        data = [kodiutils.to_unicode(b64encode(dumps(upnext_info).encode()))]
        sender = '{addon_id}.SIGNAL'.format(addon_id='plugin.video.streamz')
        kodiutils.notify(sender=sender, message='upnext_data', data=data)
