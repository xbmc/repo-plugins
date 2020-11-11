# -*- coding: utf-8 -*-
""" Background service code """

from __future__ import absolute_import, division, unicode_literals

import logging
from time import time

from xbmc import Monitor, Player, getInfoLabel

from resources.lib import kodilogging, kodiutils
from resources.lib.vtmgo.exceptions import NoLoginException

kodilogging.config()
_LOGGER = logging.getLogger('service')


class BackgroundService(Monitor):
    """ Background service code """

    def __init__(self):
        Monitor.__init__(self)
        self._player = PlayerMonitor()
        self.update_interval = 24 * 3600  # Every 24 hours
        self.cache_expiry = 30 * 24 * 3600  # One month

    def run(self):
        """ Background loop for maintenance tasks """
        _LOGGER.debug('Service started')

        while not self.abortRequested():
            # Update every `update_interval` after the last update
            if kodiutils.get_setting_bool('metadata_update') and int(kodiutils.get_setting('metadata_last_updated', 0)) + self.update_interval < time():
                self._update_metadata()

            # Stop when abort requested
            if self.waitForAbort(10):
                break

        _LOGGER.debug('Service stopped')

    def _update_metadata(self):
        """ Update the metadata for the listings """
        from resources.lib.modules.metadata import Metadata

        # Clear outdated metadata
        kodiutils.invalidate_cache(self.cache_expiry)

        def update_status(_i, _total):
            """ Allow to cancel the background job """
            return self.abortRequested() or not kodiutils.get_setting_bool('metadata_update')

        try:
            success = Metadata().fetch_metadata(callback=update_status)
        except NoLoginException:
            # We have no login yet, but that's okay, we will retry later
            success = True

        # Update metadata_last_updated
        if success:
            kodiutils.set_setting('metadata_last_updated', str(int(time())))


class PlayerMonitor(Player):
    """ A custom Player object to check subtitles """

    def __init__(self):
        """ Initialises a custom Player object """
        self.__listen = False
        self.__av_started = False
        self.__path = None
        self.__subtitle_path = None
        Player.__init__(self)

    def onPlayBackStarted(self):  # pylint: disable=invalid-name
        """ Will be called when Kodi player starts """
        self.__path = getInfoLabel('Player.FilenameAndPath')
        if not self.__path.startswith('plugin://plugin.video.vtm.go/'):
            self.__listen = False
            return
        self.__listen = True
        _LOGGER.debug('Player: [onPlayBackStarted] called')
        self.__subtitle_path = None
        self.__av_started = False

    def onAVStarted(self):  # pylint: disable=invalid-name
        """ Will be called when Kodi has a video or audiostream """
        if not self.__listen:
            return
        _LOGGER.debug('Player: [onAVStarted] called')
        self.__subtitle_path = self.__get_subtitle_path()
        self.__av_started = True
        self.__check_subtitles()

    def onAVChange(self):  # pylint: disable=invalid-name
        """ Will be called when Kodi has a video, audio or subtitle stream. Also happens when the stream changes """
        if not self.__listen:
            return
        _LOGGER.debug('Player: [onAVChange] called')
        self.__check_subtitles()

    def __check_subtitles(self):
        """ Check subtitles """

        # Check if subtitles are enabled before making any changes
        response = kodiutils.jsonrpc(method='Player.GetProperties', params=dict(playerid=1, properties=['currentsubtitle', 'subtitleenabled', 'subtitles']))
        subtitle_enabled = response.get('result').get('subtitleenabled')

        # Make sure an internal InputStream Adaptive subtitle is selected, if available
        available_subtitles = self.getAvailableSubtitleStreams()
        if available_subtitles:
            for i, subtitle in enumerate(available_subtitles):
                if '(External)' not in subtitle and '(External)' in self.getSubtitles():
                    self.setSubtitleStream(i)
                    break
        elif self.__av_started:
            _LOGGER.debug('Player: No internal subtitles found')

            # Add external subtitles
            if self.__subtitle_path:
                _LOGGER.debug('Player: Adding external subtitles %s', self.__subtitle_path)
                self.setSubtitles(self.__subtitle_path)

        # Enable subtitles if needed
        show_subtitles = kodiutils.get_setting_bool('showsubtitles')
        if show_subtitles and not subtitle_enabled:
            _LOGGER.debug('Player: Enabling subtitles')
            self.showSubtitles(True)
        elif not subtitle_enabled:
            _LOGGER.debug('Player: Disabling subtitles')
            self.showSubtitles(False)

    def onPlayBackSeek(self, time, seekOffset):  # pylint: disable=invalid-name, unused-argument, redefined-outer-name
        """ Will be called when user seeks to a time """
        if not self.__listen:
            return
        _LOGGER.debug('Player: [onPlayBackSeek] called')

    def onPlayBackEnded(self):  # pylint: disable=invalid-name
        """ Will be called when [Kodi] stops playing a file """
        if not self.__listen:
            return
        _LOGGER.debug('Player: [onPlayBackEnded] called')
        self.__av_started = False
        self.__subtitle_path = None

    def onPlayBackStopped(self):  # pylint: disable=invalid-name
        """ Will be called when [user] stops Kodi playing a file """
        if not self.__listen:
            return
        _LOGGER.debug('Player: [onPlayBackStopped] called')
        self.__av_started = False
        self.__subtitle_path = None

    def onPlayBackError(self):  # pylint: disable=invalid-name
        """ Will be called when playback stops due to an error. """
        if not self.__listen:
            return
        _LOGGER.debug('Player: [onPlayBackError] called')
        self.__av_started = False
        self.__subtitle_path = None

    @staticmethod
    def __get_subtitle_path():
        """ Get the external subtitles path """
        temp_path = kodiutils.addon_profile() + 'temp/'
        files = None
        if kodiutils.exists(temp_path):
            _, files = kodiutils.listdir(temp_path)
        if files and len(files) == 1:
            return temp_path + kodiutils.to_unicode(files[0])
        _LOGGER.debug('Player: No subtitle path')
        return None


def run():
    """ Run the BackgroundService """
    BackgroundService().run()
