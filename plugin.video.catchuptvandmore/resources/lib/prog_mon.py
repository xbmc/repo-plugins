# Copyright (c) 2023-2025 Dimitri Kroon.
# SPDX-License-Identifier: GPL-2.0-or-later
# see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt


"""
Module prog_mon
---------------

This module provides some classes and function to provide add-ons an
easy way to track the playing progress of a stream and report the play
position back to the web service at regular intervals. The primary
intention is to allow an add-on to implement a feature like 'continue
watching'.

### Contents:

* **start_progress_monitor** - For most implementations this is the only
  function an add-on needs to support tracking.
* **ProgressEvent** - The Main class that implements tracking of a
  stream.
* **ProgressEvent** - A dataclass holding various data about the play
  state of the stream at the time an event is issued.
* **PlayState** - Enum, providing constants the indicate the play
  state (playing, stopped, paused) of a stream.

"""

from __future__ import annotations

import time
import logging
from enum import Enum
from dataclasses import dataclass
from collections.abc import Callable

from xbmc import Player, Monitor

import urlquick
from codequick.support import logger_id


logger = logging.getLogger('.'.join((logger_id, __name__.split('.', 2)[-1])))


class PlayState(Enum):
    UNDEFINED = 0
    PLAYING = 1
    PAUSED = 2
    STOPPED = 3


@dataclass
class ProgressEvent:
    """An object that contains the play state of a video.

    ProgressEvent objects are created by ProgressMonitor when playing starts,
    stops, or at regular intervals while the video plays.

    Available data fields:
    - evt_type (str):
        The type of event. Can be one of the following values:
        - 'initialize' when the video is about to start playing.
        - 'heartbeat' at regular intervals while the video plays.
        - 'stopped' when the video has stopped playing.
    - playtime (float):
        The current play position of the video in seconds.
    - total_time (float):
        The length of the video in seconds.
    - play_state (PlayState):
        One of the members of :class:`PlayState`, indicating whether the video
        is playing, paused, or stopped

    """
    evt_type: str
    play_time: float
    total_time: float
    play_state: PlayState

    @property
    def time_left(self):
        return self.total_time - self.play_time

    @property
    def is_fully_played(self):
        return self.total_time - self.play_time < 5


class ProgressMonitor(Player):
    """A class to keep track of the playing progress of one single stream.

    Intended to be used by video add-ons to report back the playing time of a
    stream to the web service. This is often required to implement features
    like `continue watching`.

    For most implementations it is advised to use the convenience function
    `start_progress_monitor(...)` provided in this module. Read the function's
    documentations for a detailed description and example.

    """
    POLL_PERIOD = 1

    def __init__(self,
                 stream_url: str = None,
                 callback: Callable[..., bool] = None,
                 callb_kwargs: dict = None,
                 heartbeat_interval: int | float = 20):
        """

        :param callback: The function that will be invoked at each event.
        :param callb_kwargs: Optional keyword arguments that are to be passed
            to `callback` on each event.
        :param stream_url: The url of the stream. This should be the same url
            as set to `Listitem.path()`,
            or `resolver_proxy.get_stream_with_quality()`.
            This url is used by the monitor to check if it is tracking the
            right stream. If no video_url is passed, ProgressMonitor will just
            track the first stream that starts to play.
        :param heartbeat_interval: Optional number of seconds between each
            heartbeat event. (Default is 20)
        """
        super(ProgressMonitor, self).__init__()
        self._strm_url = stream_url
        self._callb = callback
        self._callb_kwargs = callb_kwargs if callb_kwargs is not None else {}
        self._hbt_interval = heartbeat_interval
        self._playtime = 0
        self._totaltime = 0
        self.monitor = Monitor()
        self._status = PlayState.UNDEFINED

    @property
    def playtime(self):
        """The last known playtime in second."""
        return self._playtime

    @property
    def stream_url(self):
        """The URL of the stream being tracked."""
        return self._strm_url

    def onAVStarted(self) -> None:
        # noinspection PyBroadException
        if self._status is not PlayState.UNDEFINED:
            logger.debug("onAvStarted - ProgressMonitor is already initialised")
            return

        playing_file = self.getPlayingFile()
        if self._strm_url is None:
            logger.info("No stream URL specified; accepted the first stream to start playing")
            self._strm_url = playing_file
        if playing_file != self._strm_url:
            logger.warning("Not playing the expected file '%s', but '%s'", self._strm_url, playing_file)
            return

        try:
            self._playtime = self.getTime()
            self._totaltime = self.getTotalTime()
            self._status = PlayState.PLAYING
            logger.info("Tracking '%s' - total time = %s minutes",
                        self._strm_url, self._totaltime / 60)
            self.issue_event('initialize')
        except Exception as e:
            logger.critical("ProgressMonitor.onAVStarted: %r", e)
            self._playtime = 0
            self._status = PlayState.STOPPED

    def onAVChange(self) -> None:
        if self._status != PlayState.UNDEFINED:
            # There can be a multitude of av changes before one file stops and another has started
            return
        try:
            playing_file = self.getPlayingFile()
        except RuntimeError:
            playing_file = None
        if self._strm_url != playing_file:
            logger.debug("onAvChange: playing has stopped. Now playing file '%s'", playing_file)
            self.onPlayBackStopped()

    def onPlayBackStopped(self) -> None:
        cur_state = self._status
        self._status = PlayState.STOPPED
        if cur_state in (PlayState.UNDEFINED, PlayState.STOPPED):
            return
        self.issue_event('stopped')

    def onPlayBackEnded(self) -> None:
        self.onPlayBackStopped()

    def onPlayBackError(self) -> None:
        self.onPlayBackStopped()

    # noinspection PyShadowingNames,PyPep8Naming
    def onPlayBackSeek(self, time: int, seekOffset: int) -> None:
        if time / 1000 > self._totaltime - 10:
            # Skipped to or beyond the end of the stream.
            self._playtime = self._totaltime
            self.onPlayBackStopped()

    def wait_until_playing(self, timeout: int | float) -> bool:
        """Wait and return `True` when the player has started playing.

        Return `False` when `timeout` expires, or when playing has been
        aborted before the actual playing started.

        """
        end_t = time.monotonic() + timeout
        while self._status is PlayState.UNDEFINED:
            if time.monotonic() >= end_t:
                return False
            if self.monitor.waitForAbort(0.2):
                logger.debug("wait_until_playing ended: abort requested")
                return False
        return self._status is not PlayState.STOPPED

    def monitor_progress(self) -> None:
        """Wait while the player is playing and return when playing the file
        has stopped.

        Returns immediately if the player is not playing.

        """
        if self._status is PlayState.UNDEFINED:
            return
        logger.debug("ProgressMonitor started")
        next_hbt_t = time.monotonic() + self._hbt_interval
        while not (self.monitor.waitForAbort(self.POLL_PERIOD)
                   or self._status is PlayState.STOPPED):
            try:
                self._playtime = self.getTime()
            except RuntimeError:  # Player just stopped playing
                self.onPlayBackStopped()
                break
            if time.monotonic() >= next_hbt_t:
                next_hbt_t += self._hbt_interval
                self.issue_event('heartbeat')
        logger.info("ProgressMonitor stopped")

    def issue_event(self, event_type):
        if not self._callb:
            return
        try:
            progr_evt = ProgressEvent(event_type,
                                      self._playtime,
                                      self._totaltime,
                                      self._status)
            if self._callb(progr_evt, **self._callb_kwargs) is not True:
                self._status = PlayState.STOPPED
        except (urlquick.ReadTimeout, urlquick.ConnectionError) as err:
            logger.debug("Ignoring error in event callback: %r", err)
            # On network errors keep the monitor alive until the stream stops
            pass


def start_progress_monitor(callback: Callable[..., bool],
                           callb_kwargs: dict = None,
                           video_url: str = None,
                           heartbeat_interval: int | float = 20,
                           max_startup_time: int | float = 15):
    """Start tracking playing progress.

    This convenience function creates an instance of ProgressMonitor, waits for
    the video to start and keeps the monitor alive until playing stops. This
    function is intended to be registerd for delayed execution by codequick's
    :method:`Resolver.register_delayd(...)`

    The ProgressMonitor will issue events when the video starts, stops and at
    regular intervals while the video plays. At each event ProgressMonitor will
    invoke `callback` and passes a :class:`ProgressEvent` object and the
    optional keyword arguments from ``callb_kwargs``. The
    :class:`ProgressEvent` object contains various data about the event and the
    current state of playback, like current play position, etc.

    The callback function MUST take at least one argument - the
    :class:`ProgressEvent` object that is passed by default - and all keyword
    arguments from ``callback_kwargs``.

    The callback function MUST return True explicitly. At any other return
    value, even if it evaluates to True, progress monitoring will be stopped.
    Monitoring will also stop on any exception while executing ``callback``,
    except network connection errors. With these errors, monitoring continues
    until playing stops

    :example:

        >>> def report_playing_time(event, video_id):
        >>>     '''Report the playing time back to the web service.'''
        >>>     from resources.lib.prog_mon import PlayState
        >>>
        >>>     if event.type in ('heartbeat', 'stopped'):
        >>>         state = {
        >>>             PlayState.PLAYING: 'playing',
        >>>             PlayState.PAUSED: 'paused',
        >>>             PlayState.STOPPED: 'stopped'
        >>>         }.get(event.play_state)
        >>>
        >>>         resp = urlquick.put(
        >>>             url='https://api.my.streaming.service/resume',
        >>>             json={'playTime': event.play_time,
        >>>                   'pid': video_id,
        >>>                   'evtType': state},
        >>>             timeout=5,
        >>>             max_age=-1)
        >>>     return True
        >>>
        >>>
        >>> @Resolver.register
        >>> def play_vod(plugin, vid):
        >>>     # Get the video data like a resolver would normally do.
        >>>     resp = urlquick.get(STREAM_URL % vid, timeout=5, max_age=-1)
        >>>     strm_data = resp.json()
        >>>     video_url = strm_data['video_href']
        >>>     drm_url = strm_data['lic_href']
        >>>
        >>>     # Register a function to start a progress monitor after the
        >>>     # resolver has finished.
        >>>     from resources.lib.prog_mon import start_progress_monitor
        >>>     plugin.register_delayed(
        >>>             start_progress_monitor,
        >>>             callback=report_playing_time,
        >>>             callb_kwargs={'video_id': vid},
        >>>             video_url=video_url)
        >>>
        >>>     # Continue with the usual resolver activities
        >>>     resolver_proxy.get_stream_with_quality(
        >>>             plugin,
        >>>             video_url=video_url,
        >>>             license_url=drm_url,
        >>>             manifest_type='mpd')

    :param callback: The function that will be called at each event.
    :param callb_kwargs: Optional keyword arguments that are to be passed to
        `callback` on each event.
    :param video_url: The url of the stream. This should be the same url as
        set to `Listitem.path()`, or `resolver_proxy.get_stream_with_quality()`.
        This url is used by the monitor to check if it is tracking the right
        stream. If no video_url is passed, ProgressMonitor will just track the
        first stream that starts to play.
    :param heartbeat_interval: Optional number of seconds between each
        heartbeat event. (Default is 20)
    :param max_startup_time: Optional maximum number of seconds to wait for
        a video to start. (Default is 15)

    """
    # noinspection PyBroadException
    try:
        progr_mon = ProgressMonitor(video_url,
                                    callback,
                                    callb_kwargs,
                                    heartbeat_interval)
        progr_mon.wait_until_playing(max_startup_time)
        progr_mon.monitor_progress()
    except Exception:
        logger.critical("Progress monitoring aborted due to an unhandled exception:\n",
                        exc_info=True)
