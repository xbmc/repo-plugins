# -*- coding: utf-8 -*-
"""

    Copyright (C) 2019-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import threading

from kodi_six import xbmc  # pylint: disable=import-error

from .constants import CONFIG
from .constants import StreamControl
from .dialogs.skip_intro import SkipIntroDialog
from .logger import Logger
from .strings import encode_utf8
from .strings import i18n
from .up_next import UpNext
from .utils import read_pickled

LOG = Logger('player')


class PlaybackMonitorThread(threading.Thread):
    LOG = Logger('PlaybackMonitorThread')
    MONITOR = xbmc.Monitor()
    PLAYER = xbmc.Player()

    def __init__(self, settings, monitor_dict, window):
        super(PlaybackMonitorThread, self).__init__()  # pylint: disable=super-with-arguments
        self._stopped = threading.Event()
        self._ended = threading.Event()

        self.settings = settings
        self._window = window

        self._monitor_dict = monitor_dict
        self._dialog_skip_intro = None

        self.daemon = True
        self.start()

    def details(self):
        return self._monitor_dict.get('details')

    def media_id(self):
        return self._monitor_dict.get('media_id')

    def playing_file(self):
        return self._monitor_dict.get('playing_file')

    @staticmethod
    def plugin_path():
        return 'plugin://%s/' % CONFIG['id']

    def server(self):
        return self._monitor_dict.get('server')

    def session(self):
        return self._monitor_dict.get('session')

    def stream(self):
        return self._monitor_dict.get('stream')

    def _up_next(self):
        return self._monitor_dict.get('up_next')

    def _markers(self):
        return self.stream().get('intro_markers')

    def _intro_start(self):
        if isinstance(self._markers(), list) and len(self._markers()) == 2:
            return int(self._markers()[0])
        return None

    def _intro_end(self):
        if isinstance(self._markers(), list) and len(self._markers()) == 2:
            return int(self._markers()[1])
        return None

    def full_data(self):
        _stream = self.stream()
        if _stream:
            return _stream.get('full_data', {})
        return {}

    def callback_arguments(self):
        return self._monitor_dict.get('callback_args', {})

    def media_type(self):
        return self.full_data().get('mediatype', 'file').lower()

    def stop(self):
        self.LOG.debug('[%s]: Stop event set...' % self.media_id())
        self._stopped.set()

    def stopped(self):
        return self._stopped.is_set()

    def end(self):
        self.LOG.debug('[%s]: End event set...' % self.media_id())
        self._ended.set()

    def ended(self):
        return self._ended.is_set()

    def _wait_for_playback(self):
        np_wait_time = 0.5
        np_waited = 0.0

        while not self.PLAYER.isPlaying() and not self.MONITOR.abortRequested():
            self.LOG.debug('Waiting for playback to start')

            xbmc.sleep(int(np_wait_time * 1000))
            if np_waited >= 5:
                self.stop()
                return

            np_waited += np_wait_time

    def notify_upnext(self):
        if self.settings.use_up_next() and self.media_type() == 'episode':
            self.LOG('Using Up Next ...')
            if self._up_next():
                UpNext(self.settings, server=self.server(), media_id=self.media_id(),
                       callback_args=self.callback_arguments()).run()
            else:
                self.LOG('Up Next silenced ...')

        elif self.media_type() != 'episode':
            self.LOG('Up Next [%s] is not an episode ...' % self.media_type())
        else:
            self.LOG('Up Next is disabled ...')

    def report_playback_progress(self, current_time, total_time,
                                 progress, played_time=-1):
        if current_time == 0 or total_time == 0:
            return played_time

        if played_time > -1:
            if played_time == current_time:
                self.LOG.debug('Video paused at: %s secs of %s @ %s%%' %
                               (current_time, total_time, progress))
                self.server().report_playback_progress(self.media_id(),
                                                       current_time * 1000,
                                                       state='paused',
                                                       duration=total_time * 1000)
            else:
                self.LOG.debug('Video played time: %s secs of %s @ %s%%' %
                               (current_time, total_time, progress))
                self.server().report_playback_progress(self.media_id(),
                                                       current_time * 1000,
                                                       state='playing',
                                                       duration=total_time * 1000)
                played_time = current_time
        else:
            self.LOG.debug('Playback Stopped: %s secs of %s @ %s%%' %
                           (current_time, total_time, progress))
            # report_playback_progress state=stopped will adjust current time to match duration
            # and mark media as watched if progress >= 98%
            self.server().report_playback_progress(self.media_id(), current_time * 1000,
                                                   state='stopped', duration=total_time * 1000)
        return played_time

    def _is_playing_current_file(self):
        try:
            current_file = self.PLAYER.getPlayingFile()
            if current_file != self.playing_file() and \
                    not (current_file.startswith(self.plugin_path())
                         and self.media_id() in current_file) or self.stopped():
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

    def resume(self, current_time):
        resume_time = float(self.details().get('resume', 0))

        if (resume_time <= 1  # don't resume if only 1 second
                or resume_time <= float(current_time)):  # don't seek backwards or to current time
            return True

        if resume_time > float(current_time):
            # seek to resume time if it's greater than the current time
            self.PLAYER.seekTime(int(resume_time) - 1)
            return True

        return False

    def _skip_intro_dialog(self):
        if self._dialog_skip_intro is not None:
            return

        self._dialog_skip_intro = SkipIntroDialog('skip_intro.xml',
                                                  CONFIG['addon'].getAddonInfo('path'),
                                                  'default', '720p', intro_end=self._intro_end())

    def skip_intro(self):
        if (self.settings.intro_skipping() and
                self._intro_start() is not None and self._intro_end() is not None):
            if (self._dialog_skip_intro and self._dialog_skip_intro.on_hold and
                    (self._intro_start() > self._get_time_ms() or
                     self._get_time_ms() > self._intro_end())):
                self._dialog_skip_intro.on_hold = False

            if self._intro_start() <= self._get_time_ms() < self._intro_end():
                self._skip_intro_dialog()
                self._dialog_skip_intro.show()

            elif self._dialog_skip_intro and self._get_time_ms() >= self._intro_end():
                self._dialog_skip_intro.close()

            elif self._dialog_skip_intro and self._get_time_ms() < self._intro_start():
                self._dialog_skip_intro.close()

    def run(self):
        current_time = 0
        played_time = 0
        progress = 0
        total_time = 0

        if self.session():
            self.LOG.debug('We are monitoring a transcode session')

        self._wait_for_playback()

        if self.stream():
            set_audio_subtitles(self.settings, self.stream())

        wait_time = 0.5
        waited = 0.0

        notified_upnext = False
        resumed = not self.details().get('resuming')

        # Whilst the file is playing back
        while self.PLAYER.isPlaying() and not self.MONITOR.abortRequested():

            if not self._is_playing_current_file():
                break

            current_time, total_time, progress = self._get_playback_progress(total_time)

            self.skip_intro()

            try:
                report = int((float(waited) / 10.0)) >= 1
            except ZeroDivisionError:
                report = False

            if report:  # only report every ~10 seconds, times are updated at 0.5 seconds
                waited = 0.0
                played_time = self.report_playback_progress(current_time, total_time,
                                                            progress, played_time)

            if current_time > 0:
                if not resumed:
                    resumed = self.resume(current_time)

                if not notified_upnext:
                    notified_upnext = True
                    self.notify_upnext()

            if self.MONITOR.waitForAbort(wait_time):
                break

            waited += wait_time

        _ = self.report_playback_progress(current_time, total_time, progress)

        if self._dialog_skip_intro and self._dialog_skip_intro.showing:
            self._dialog_skip_intro.close()

        if self.session() is not None:
            self.LOG.debug('Stopping PMS transcode job with session %s' % self.session())
            self.server().stop_transcode_session(self.session())


class CallbackPlayer(xbmc.Player):
    LOG = Logger('CallbackPlayer')

    def __init__(self, window, settings, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

        self.settings = settings
        self.threads = []
        self.window = window

    def stop_threads(self):
        for thread in self.threads:
            if thread.ended():
                continue

            if not thread.stopped():
                self.LOG.debug('[%s]: stopping...' % thread.media_id())
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
                self.LOG.debug('[%s]: clean up...' % thread.media_id())
            else:
                self.LOG.debug('[%s]: stopping...' % thread.media_id())
                if not thread.stopped():
                    thread.stop()
            try:
                thread.join()
            except RuntimeError:
                pass
        self.LOG.debug('Active monitor threads: |%s|' %
                       ', '.join(map(lambda x: x.media_id(), active_threads)))
        self.threads = active_threads

    def onPlayBackStarted(self):  # pylint: disable=invalid-name
        monitor_playback = not self.settings.playback_monitor_disabled(fresh=True)
        playback_dict = read_pickled('playback_monitor.pickle')

        self.cleanup_threads()
        if monitor_playback and playback_dict:
            self.threads.append(PlaybackMonitorThread(self.settings, playback_dict, self.window))

        elif not monitor_playback:
            self.LOG('Playback monitoring is disabled ...')

        elif not playback_dict:
            self.LOG('Playback monitoring failed to start, missing required {} ...')

    def onPlayBackEnded(self):  # pylint: disable=invalid-name
        self.stop_threads()
        self.cleanup_threads()

    def onPlayBackStopped(self):  # pylint: disable=invalid-name
        self.onPlayBackEnded()

    def onPlayBackError(self):  # pylint: disable=invalid-name
        self.onPlayBackEnded()


def set_audio_subtitles(settings, stream):
    """
        Take the collected audio/sub stream data and apply to the media
        If we do not have any subs then we switch them off
    """

    # If we have decided not to collect any sub data then do not set subs
    player = xbmc.Player()
    control = settings.stream_control(fresh=True)

    if stream['contents'] == 'type':
        LOG.debug('No audio or subtitle streams to process.')

        # If we have decided to force off all subs, then turn them off now and return
        if control == StreamControl.NEVER:
            player.showSubtitles(False)
            LOG.debug('All subs disabled')

        return

    # Set the AUDIO component
    if control == StreamControl.PLEX:
        LOG.debug('Attempting to set Audio Stream')

        audio = stream['audio']

        if stream['audio_count'] == 1:
            LOG.debug('Only one audio stream present - will leave as default')

        elif audio:
            LOG.debug(
                'Attempting to use selected language setting: %s' %
                encode_utf8(audio.get('language', audio.get('languageCode', i18n('Unknown'))))
            )
            LOG.debug('Found preferred language at index %s' % stream['audio_offset'])
            try:
                player.setAudioStream(stream['audio_offset'])
                LOG.debug('Audio set')
            except:  # pylint: disable=bare-except
                LOG.debug('Error setting audio, will use embedded default stream')

    # Set the SUBTITLE component
    if control == StreamControl.PLEX:
        LOG.debug('Attempting to set preferred subtitle Stream')
        subtitle = stream['subtitle']
        if subtitle:
            LOG.debug('Found preferred subtitle stream')
            try:
                player.showSubtitles(False)
                if subtitle.get('key'):
                    player.setSubtitles(subtitle['key'])
                else:
                    LOG.debug('Enabling embedded subtitles at index %s' % stream['sub_offset'])
                    player.setSubtitleStream(int(stream['sub_offset']))

                player.showSubtitles(True)
                return
            except:  # pylint: disable=bare-except
                LOG.debug('Error setting subtitle')

        else:
            LOG.debug('No preferred subtitles to set')
            player.showSubtitles(False)
