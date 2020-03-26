# -*- coding: utf-8 -*-
""" Player module """

from __future__ import absolute_import, division, unicode_literals

from resources.lib.kodiwrapper import TitleItem, LOG_WARNING, to_unicode, KodiPlayer
from resources.lib.vtmgo.vtmgo import VtmGo, UnavailableException
from resources.lib.vtmgo.vtmgostream import VtmGoStream, StreamGeoblockedException, StreamUnavailableException


class Player:
    """ Code responsible for playing media """

    def __init__(self, kodi):
        """ Initialise object
        :type kodi: resources.lib.kodiwrapper.KodiWrapper
        """
        self._kodi = kodi
        self._vtm_go = VtmGo(self._kodi)
        self._vtm_go_stream = VtmGoStream(self._kodi)

    def play_or_live(self, category, item, channel):
        """ Ask to play the requested item or switch to the live channel
        :type category: str
        :type item: str
        :type channel: str
        """
        if not self._check_credentials():
            self._kodi.end_of_directory()
            return

        res = self._kodi.show_context_menu([self._kodi.localize(30103), self._kodi.localize(30105)])  # Watch Live | Play from Catalog
        if res == -1:  # user has cancelled
            return
        if res == 0:  # user selected "Watch Live"
            # Play live
            self.play('channels', channel)
            return

        # Play this program
        self.play(category, item)

    def play(self, category, item):
        """ Play the requested item.
        :type category: string
        :type item: string
        """
        if not self._check_credentials():
            self._kodi.end_of_directory()
            return

        # Check if inputstreamhelper is correctly installed
        if not self._check_inputstream():
            return

        try:
            # Get stream information
            resolved_stream = self._vtm_go_stream.get_stream(category, item)

        except StreamGeoblockedException:
            self._kodi.show_ok_dialog(heading=self._kodi.localize(30709), message=self._kodi.localize(30710))  # This video is geo-blocked...
            return

        except StreamUnavailableException:
            self._kodi.show_ok_dialog(heading=self._kodi.localize(30711), message=self._kodi.localize(30712))  # The video is unavailable...
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
                movie_details = self._vtm_go.get_movie(item)
                if movie_details:
                    info_dict.update({
                        'plot': movie_details.description,
                        'year': movie_details.year,
                        'aired': movie_details.aired,
                    })

            elif category == 'episodes':
                info_dict.update({'mediatype': 'episode'})

                # There is no direct API to get episode details, so we go trough the cached program details
                program = self._vtm_go.get_program(resolved_stream.program_id)
                if program:
                    episode_details = self._vtm_go.get_episode_from_program(program, item)
                    if episode_details:
                        info_dict.update({
                            'plot': episode_details.description,
                            'season': episode_details.season,
                            'episode': episode_details.number,
                        })

                        # Lookup the next episode
                        next_episode_details = self._vtm_go.get_next_episode_from_program(program, episode_details.season, episode_details.number)

                        # Create the data for Up Next
                        if next_episode_details:
                            upnext_data = self.generate_upnext(episode_details, next_episode_details)

            elif category == 'channels':
                info_dict.update({'mediatype': 'episode'})

                # For live channels, we need to keep on updating the manifest
                # This might not be needed, and could be done with the Location-tag updates if inputstream.adaptive supports it
                # See https://github.com/peak3d/inputstream.adaptive/pull/298#issuecomment-524206935
                prop_dict.update({
                    'inputstream.adaptive.manifest_update_parameter': 'full',
                })

            else:
                self._kodi.log('Unknown category %s' % category, LOG_WARNING)

        except UnavailableException:
            # We continue without details.
            # This allows to play some programs that don't have metadata yet.
            pass

        # Play this item
        self._kodi.play(
            TitleItem(
                title=resolved_stream.title,
                path=resolved_stream.url,
                subtitles_path=resolved_stream.subtitles,
                art_dict={},
                info_dict=info_dict,
                prop_dict=prop_dict,
                stream_dict=stream_dict,
                is_playable=True,
            ),
            license_key=self._vtm_go_stream.create_license_key(resolved_stream.license_url))

        # Wait for playback to start
        kodi_player = KodiPlayer(kodi=self._kodi)
        if not kodi_player.waitForPlayBack(url=resolved_stream.url):
            # Playback didn't start
            return

        # Add subtitles
        if resolved_stream.subtitles:
            self._kodi.log('Setting subtitles')
            kodi_player.setSubtitles(resolved_stream.subtitles[0])

            # Turn on subtitles if needed
            if self._kodi.get_setting_as_bool('showsubtitles'):
                self._kodi.log('Enabling subtitles')
                kodi_player.showSubtitles(True)

        # Send Up Next data
        if upnext_data:
            self._kodi.log("Sending Up Next data: %s" % upnext_data)
            self.send_upnext(upnext_data)

    def _check_credentials(self):
        """ Check if the user has credentials """
        if self._kodi.has_credentials():
            return True

        # You need to configure your credentials before you can access the content of VTM GO.
        confirm = self._kodi.show_yesno_dialog(message=self._kodi.localize(30701))
        if confirm:
            self._kodi.open_settings()
            if self._kodi.has_credentials():
                return True

        return False

    def _check_inputstream(self):
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
            self._kodi.show_ok_dialog(message=self._kodi.localize(30708))  # Please reboot Kodi
            return False

        return True

    @staticmethod
    def generate_upnext(current_episode, next_episode):
        """ Construct the data for Up Next.
        :type current_episode: resources.lib.vtmgo.vtmgo.Episode
        :type next_episode: resources.lib.vtmgo.vtmgo.Episode
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
            play_url='plugin://plugin.video.vtm.go/play/catalog/episodes/%s' % next_episode.episode_id,
        )

        return upnext_info

    def send_upnext(self, upnext_info):
        """ Send a message to Up Next with information about the next Episode.
        :type upnext_info: object
        """
        from base64 import b64encode
        from json import dumps
        data = [to_unicode(b64encode(dumps(upnext_info).encode()))]
        sender = '{addon_id}.SIGNAL'.format(addon_id='plugin.video.vtm.go')
        self._kodi.notify(sender=sender, message='upnext_data', data=data)
