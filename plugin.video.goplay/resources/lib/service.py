# -*- coding: utf-8 -*-
""" Background service code """

from __future__ import absolute_import, division, unicode_literals

import hashlib
import logging
from threading import Event, Thread

from xbmc import Monitor, Player, getInfoLabel

from resources.lib import kodilogging, kodiutils
from resources.lib.goplay.auth import AuthApi
from resources.lib.goplay.content import ContentApi

_LOGGER = logging.getLogger(__name__)


class BackgroundService(Monitor):
    """ Background service code """

    def __init__(self):
        Monitor.__init__(self)
        self.update_interval = 24 * 3600  # Every 24 hours
        self.cache_expiry = 30 * 24 * 3600  # One month
        self._auth = AuthApi(kodiutils.get_setting('username'), kodiutils.get_setting('password'), kodiutils.get_tokens_path())
        self._kodiplayer = KodiPlayer()

    def run(self):
        """ Background loop for maintenance tasks """
        _LOGGER.debug('Service started')

        while not self.abortRequested():
            # Stop when abort requested
            if self.waitForAbort(10):
                break

        _LOGGER.debug('Service stopped')

    def onSettingsChanged(self):  # pylint: disable=invalid-name
        """ Callback when a setting has changed """
        if self._has_credentials_changed():
            _LOGGER.debug('Clearing auth tokens due to changed credentials')
            self._auth.clear_tokens()

            # Refresh container
            kodiutils.container_refresh()

    @staticmethod
    def _has_credentials_changed():
        """ Check if credentials have changed """
        old_hash = kodiutils.get_setting('credentials_hash')
        new_hash = ''
        if kodiutils.get_setting('username') or kodiutils.get_setting('password'):
            new_hash = hashlib.md5((kodiutils.get_setting('username') + kodiutils.get_setting('password')).encode('utf-8')).hexdigest()
        if new_hash != old_hash:
            kodiutils.set_setting('credentials_hash', new_hash)
            return True
        return False


class KodiPlayer(Player):
    """Communication with Kodi Player"""

    def __init__(self):
        """KodiPlayer initialisation"""
        Player.__init__(self)
        self.listen = False
        self.path = None
        self.av_started = False
        self.stream_path = None
        self._auth = AuthApi(kodiutils.get_setting('username'), kodiutils.get_setting('password'), kodiutils.get_tokens_path())
        self._api = ContentApi(self._auth, cache_path=kodiutils.get_cache_path())
        self.positionthread = None
        self.quit = Event()
        self.last_pos = None
        self.total = None

    def onPlayBackStarted(self):  # pylint: disable=invalid-name
        """Called when user starts playing a file"""
        self.path = getInfoLabel('Player.FilenameAndPath')
        if self.path.startswith('plugin://plugin.video.goplay/'):
            self.listen = True
        else:
            self.listen = False
            return
        _LOGGER.debug('KodiPlayer onPlayBackStarted')
        self.av_started = False
        self.stream_path = self.getPlayingFile()

    def onAVStarted(self):  # pylint: disable=invalid-name
        """Called when Kodi has a video or audiostream"""
        if not self.listen:
            return
        _LOGGER.debug('KodiPlayer onAVStarted')
        self.av_started = True

        # Only start a single thread
        if not self.positionthread:
            self.quit.clear()
            self.positionthread = Thread(target=self.stream_position, name='StreamPosition')
            self.positionthread.start()
            _LOGGER.debug('KodiPlayer position thread started')

    def onAVChange(self):  # pylint: disable=invalid-name
        """Called when Kodi has a video, audio or subtitle stream. Also happens when the stream changes."""
        if not self.listen:
            return
        _LOGGER.debug('KodiPlayer onAVChange')

    def onPlayBackSeek(self, time, seekOffset):  # pylint: disable=invalid-name, redefined-outer-name
        """Called when user seeks to a time"""
        if not self.listen:
            return
        _LOGGER.debug('KodiPlayer onPlayBackSeek time=%s offset=%s', time, seekOffset)
        # Update position to seek time
        self.last_pos = time // 1000

    def onPlayBackPaused(self):  # pylint: disable=invalid-name
        """Called when user pauses a playing file"""
        if not self.listen:
            return
        _LOGGER.debug('KodiPlayer onPlayBackPaused')
        self.update_resume()

    def onPlayBackResumed(self):  # pylint: disable=invalid-name
        """Called when user resumes a paused file or a next playlist item is started"""
        if not self.listen:
            return
        _LOGGER.debug('KodiPlayer onPlayBackResumed')

    def onPlayBackError(self):  # pylint: disable=invalid-name
        """Called when playback stops due to an error"""
        if not self.listen:
            return
        _LOGGER.debug('KodiPlayer onPlayBackError')
        self.quit.set()

    def onPlayBackStopped(self):  # pylint: disable=invalid-name
        """Called when user stops Kodi playing a file"""
        if not self.listen:
            return
        _LOGGER.debug('KodiPlayer onPlayBackStopped')
        self.quit.set()
        if not self.av_started:
            # Check stream path
            import requests
            response = requests.get(self.stream_path, timeout=5)
            if response.status_code == 403:
                message_id = 30720
            else:
                message_id = 30719
            kodiutils.ok_dialog(message=kodiutils.localize(message_id))

    def onPlayBackEnded(self):  # pylint: disable=invalid-name
        """Called when Kodi has ended playing a file"""
        if not self.listen:
            return
        _LOGGER.debug('KodiPlayer onPlayBackEnded')
        self.quit.set()

    def onPlayerExit(self):  # pylint: disable=invalid-name
        """Called when player exits"""
        _LOGGER.debug('KodiPlayer onPlayerExit')
        # Clear threading
        self.positionthread = None
        _LOGGER.debug('KodiPlayer position thread stopped')
        self.update_resume()

    def update_position(self):
        """Update the player position, when possible"""
        try:
            pos = self.getTime()
            _LOGGER.debug('KodiPlayer update position to %s', pos)
            # Kodi Player sometimes returns a time of 0.0
            if pos > 0.0:
                self.last_pos = pos
        except RuntimeError:
            pass


    def update_total(self):
        """Update the total video time"""
        try:
            tot = self.getTotalTime()
            # Kodi Player sometimes returns a total time of 0.0
            if tot > 0.0:
                self.total = tot
        except RuntimeError:
            pass

    def update_resume(self):
        """ Update resume position to goplay api """
        video_id = self.path.split('/')[-2]
        # When seeking, Kodi Player sometimes returns a position greater than the total time
        if self.last_pos >= self.total:
            self._api.delete_position(video_id)
            #self._api.update_position(video_id, 1200)
            return
        _LOGGER.debug('KodiPlayer video %s set resumetime to %s/%s', video_id, self.last_pos, self.total)
        self._api.update_position(video_id, int(self.last_pos))


    def stream_position(self):
        """Get latest stream position while playing"""
        # Store total video time
        self.update_total()
        while self.isPlaying() and not self.quit.is_set():
            self.update_position()
            if self.quit.wait(timeout=0.2):
                break
        self.onPlayerExit()


def run():
    """ Run the BackgroundService """
    kodilogging.config()
    BackgroundService().run()
