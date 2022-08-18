# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

# pylint: disable=invalid-name,import-error

import threading

import xbmc

from ..constants import ADDON_ID
from ..constants import SCRIPT_MODES
from .logger import Log
from .pickle import read_pickled
from .utils import event_notification

LOG = Log('lib', __file__)


class CallbackPlayer(xbmc.Player):

    def __init__(self, context, window, *args, **kwargs):
        super().__init__()
        self.context = context
        self.window = window

        self.args = args
        self.kwargs = kwargs

        self.threads = []

    def stop_threads(self):
        for thread in self.threads:
            if thread.ended():
                continue

            if not thread.stopped():
                LOG.debug('[%s]: stopping...' % thread.video_id)
                thread.stop()

        for thread in self.threads:
            if thread.stopped() and not thread.ended():
                try:
                    thread.join()
                except RuntimeError:
                    pass

    def cleanup_threads(self, only_ended=False):
        active_threads = []
        append = active_threads.append

        for thread in self.threads:
            if only_ended and not thread.ended():
                append(thread)
                continue

            if thread.ended():
                LOG.debug('[%s]: clean up...' % thread.video_id)
            else:
                LOG.debug('[%s]: stopping...' % thread.video_id)
                if not thread.stopped():
                    thread.stop()
            try:
                thread.join()
            except RuntimeError:
                pass

        LOG.debug('Active monitor threads: [%s]' %
                  ', '.join(map(lambda x: x.video_id, active_threads)))
        self.threads = active_threads

    def onPlayBackStarted(self):
        player_dict = read_pickled('playback.pickle')

        self.cleanup_threads()
        if player_dict:
            self.threads.append(PlaybackMonitorThread(self.context, self.window, player_dict))
            event_notification('playback.started', player_dict)

        elif not player_dict:
            LOG.debug('Playback monitoring failed to start, missing required {} ...')

    def onPlayBackEnded(self):
        self.stop_threads()
        self.cleanup_threads()

    def onPlayBackStopped(self):
        self.onPlayBackEnded()

    def onPlayBackError(self):
        self.onPlayBackEnded()


class PlaybackMonitorThread(threading.Thread):
    MONITOR = xbmc.Monitor()
    PLAYER = xbmc.Player()

    def __init__(self, context, window, player_dict):
        super().__init__()
        self._stopped = threading.Event()
        self._ended = threading.Event()

        self._context = context
        self._window = window

        self._player_dict = player_dict

        self.playlist_position = str(xbmc.PlayList(xbmc.PLAYLIST_VIDEO).getposition())

        self.daemon = True
        self.start()

    @property
    def context(self):
        return self._context

    @property
    def window(self):
        return self._window

    @property
    def video_id(self):
        return self._player_dict.get('video_id')

    @property
    def playing_file(self):
        return self._player_dict.get('playing_file')

    @property
    def is_live(self):
        return self._player_dict.get('live')

    @property
    def metadata(self):
        return self._player_dict.get('metadata', {})

    @staticmethod
    def plugin_path():
        return 'plugin://%s/' % ADDON_ID

    def stop(self):
        LOG.debug('[%s]: Stop event set...' % self.video_id)
        self._stopped.set()

    def stopped(self):
        return self._stopped.is_set()

    def end(self):
        LOG.debug('[%s]: End event set...' % self.video_id)
        self._ended.set()

    def ended(self):
        return self._ended.is_set()

    def _wait_for_playback(self):
        np_wait_time = 0.5
        np_waited = 0.0

        while not self.PLAYER.isPlaying() and not self.MONITOR.abortRequested():
            LOG.debug('Waiting for playback to start')

            xbmc.sleep(int(np_wait_time * 1000))
            if np_waited >= 5:
                self.stop()
                return

            np_waited += np_wait_time

    def _is_playing_current_file(self):
        try:
            current_file = self.PLAYER.getPlayingFile()
            if current_file != self.playing_file and \
                    not (current_file.startswith(self.plugin_path())
                         and self.video_id in current_file) or self.stopped():
                self.stop()
                return False

        except RuntimeError:
            pass

        return True

    def _get_time_ms(self):
        try:
            current_time = self.PLAYER.getTime()
        except RuntimeError:
            current_time = 0.0
        return 1000 * current_time

    def _get_playback_progress(self, total_time):
        try:
            current_time = int(self.PLAYER.getTime())
            if total_time == 0:
                total_time = int(self.PLAYER.getTotalTime())
        except RuntimeError:
            current_time = 0

        try:
            progress = int((float(current_time) / float(total_time)) * 100)
        except ZeroDivisionError:
            progress = 0

        return current_time, total_time, progress

    def run(self):
        total_time = 0
        progress = 0

        self._wait_for_playback()

        wait_time = 0.5
        waited = 0.0

        # Whilst the file is playing back
        while self.PLAYER.isPlaying() and not self.MONITOR.abortRequested():

            if not self._is_playing_current_file():
                break

            _, total_time, progress = self._get_playback_progress(total_time)

            try:
                report = int((float(waited) / 10.0)) >= 1
            except ZeroDivisionError:
                report = False

            if report:
                waited = 0.0
                # do something here every 10 seconds

            if self.MONITOR.waitForAbort(wait_time):
                break

            waited += wait_time

        if progress >= self.context.settings.post_play_minimum_progress:
            xbmc.executebuiltin('RunScript(%s,mode=%s&video_id=%s&position=%s&live=%s)' %
                                (ADDON_ID, str(SCRIPT_MODES.POST_PLAY), self.video_id,
                                 self.playlist_position, self.is_live))
