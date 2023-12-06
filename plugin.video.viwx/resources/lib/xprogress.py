# ----------------------------------------------------------------------------------------------------------------------
#  Copyright (c) 2023 Dimitri Kroon.
#  This file is part of plugin.video.viwx.
#  SPDX-License-Identifier: GPL-2.0-or-later
#  See LICENSE.txt
# ----------------------------------------------------------------------------------------------------------------------
import threading
import uuid
import time
import logging

from xbmc import Player, Monitor

from codequick.support import logger_id

from resources.lib import fetch
from . itv_account import itv_session
from . itvx import PLATFORM_TAG


logger = logging.getLogger('.'.join((logger_id, __name__.split('.', 2)[-1])))


EVT_URL = 'https://secure.pes.itv.com/1.1.3/event'


class PlayState:
    UNDEFINED = 0xFF00
    PLAYING = 0xFF01
    PAUSED = 0xFF02
    STOPPED = 0xFF03


class PlayTimeMonitor(Player):
    POLL_PERIOD = 1
    REPORT_PERIOD = 30

    def __init__(self, production_id):
        super(PlayTimeMonitor, self).__init__()
        self._instance_id = None
        self._production_id = production_id
        self._event_seq_nr = 0
        self._playtime = 0
        self._user_id = itv_session().user_id
        self.monitor = Monitor()
        self._status = PlayState.UNDEFINED
        self._cur_file = None
        self._post_errors = 0

    @property
    def playtime(self):
        """Return the last known playtime in milliseconds"""
        return int(self._playtime * 1000)

    def onAVStarted(self) -> None:
        # noinspection PyBroadException
        logger.debug("onAVStarted called from thread %s", threading.current_thread().native_id)
        if self._status is not PlayState.UNDEFINED:
            logger.warning("onAvStarted - player is already initialised")
            return

        try:
            self._cur_file = self.getPlayingFile()
            self._playtime = self.getTime()
            self._status = PlayState.PLAYING
            logger.debug("PlayTimeMonitor: total play time = %s", self.playtime/60)
            self._post_event_startup_complete()
        except:
            logger.error("PlayTimeMonitor.onAVStarted:\n", exc_info=True)
            self._playtime = 0
            self._status = PlayState.STOPPED

    def onAVChange(self) -> None:
        if self._cur_file and self._cur_file != self.getPlayingFile():
            logger.debug("onAvChange: playing has stopped. Now playing file '%s'", self.getPlayingFile())
            self.onPlayBackStopped()

    def onPlayBackStopped(self) -> None:
        cur_state = self._status
        self._status = PlayState.STOPPED
        if cur_state in (PlayState.UNDEFINED, PlayState.STOPPED):
            return
        self._post_event_heartbeat()

    def onPlayBackEnded(self) -> None:
        self.onPlayBackStopped()

    def onPlayBackError(self) -> None:
        self.onPlayBackStopped()

    def wait_until_playing(self, timeout) -> bool:
        """Wait and return `True` when the player has started playing.
        Return `False` when `timeout` expires, or when playing has been aborted before
        the actual playing started.

        """
        end_t = time.monotonic() + timeout
        while self._status is PlayState.UNDEFINED:
            if time.monotonic() >= end_t:
                return False
            if self.monitor.waitForAbort(0.2):
                logger.debug("wait_until_playing ended: abort requested")
                return False
        return not self._status is PlayState.STOPPED

    def monitor_progress(self) -> None:
        """Wait while the player is playing and return when playing the file has stopped.
        Returns immediately if the player is not playing.

        """
        if self._status is PlayState.UNDEFINED:
            return
        logger.debug("Playtime Monitor start")
        report_t = time.monotonic() + self.REPORT_PERIOD
        while not (self.monitor.waitForAbort(self.POLL_PERIOD) or self._status is PlayState.STOPPED):
            try:
                self._playtime = self.getTime()
            except RuntimeError:  # Player just stopped playing
                self.onPlayBackStopped()
                break
            if time.monotonic() > report_t:
                report_t += self.REPORT_PERIOD
                self._post_event_heartbeat()
        logger.debug("Playtime Monitor stopped")

    def initialise(self):
        """Initialise play state reports.

        Create an instance ID and post a 'open' event. Subsequent events are to use the
        same instance ID. So if posting fails it's no use going on monitoring and post
        other events.

        """
        logger.debug("Event OPEN of production %s", self._production_id)
        self._instance_id = str(uuid.uuid4())
        data = {
            "_v": "1.2.2",
            "cid": "e029c040-3119-4192-a219-7086414b5e2b",
            "content": self._production_id,
            "device": {
                "group": "firefox",
                "manufacturer": "Firefox",
                "model": fetch.USER_AGENT_VERSION,
                "os": "Ubuntu",
                "userAgent": fetch.USER_AGENT,
                "x-codecs": {
                    "h264_High_3_0": "probably",
                    "h264_High_3_1": "probably",
                    "h264_Main_3_0": "probably",
                    "h264_Main_3_1": "probably",
                    "hevc": "probably",
                    "vp9": "probably"
                }
            },
            "instance": self._instance_id,
            "platform": PLATFORM_TAG,
            # TODO: playback type short for news-like clips
            "playbackType": "vod",
            "seq": self._event_seq_nr,
            "type": "open",
            "user": {
                "entitlements": "",
                "id": self._user_id
            },
            "version": "1.9.64",
            "x-playerType": "shaka",
            "x-resume": "cross"
        }
        resp = fetch.web_request('post', EVT_URL, data=data)
        if resp.content != b'ok':
            logger.warning("Error sending 'open' event for production %s: %s - %s",
                           self._production_id, resp.status_code, resp.text)
            self._status = PlayState.STOPPED

    def _post_event_startup_complete(self):
        logger.debug("Event Startup Complete - position %s", self._playtime)
        data = {'contentPosStartMillis': self.playtime,
                'initialAudioDescriptionStatus': 'disabled',
                'initialSubStatus': 'disabled',
                'mediaType': 'sting',       # news = 'programme', everything else = 'sting'
                'timeTakenMillis': 42}
        self._handle_event(data, 'startUpComplete')

    def _post_event_heartbeat(self):
        """Post the current play position of a video

        Is to be sent every 30 seconds while the video is playing, or paused.
        """
        logger.debug("Event Heartbeat - position %s", self._playtime)
        data = {'bitrateKilobitsPerSec': 2399,
                'contentPosMillis': self.playtime}
        self._handle_event(data, 'heartbeat')

    def _post_event_seek(self, from_position: float):
        """Post a seek event - to be used after skipping forwards or back.

        Not mandatory, currently not used.

        """
        logger.debug("Event Seek - position %s", self._playtime)

        data = {'contentPosFromMillis': from_position,
                'contentPosToMillis': self.playtime,
                'seekButtonInteract': 0}
        self._handle_event(data, 'seek')


    def _post_event_stop(self):
        """Stop event. Only seen on mobile app. Currently not used."""
        self._event_seq_nr += 1
        data = {
            '_v': '1.2.3',
            'content': self._production_id,
            'data': {},
            'instance': self._instance_id,
            'platform': PLATFORM_TAG,
            'seq': self._event_seq_nr,
            'type': 'x-stop'
        }
        fetch.web_request('post', EVT_URL, data=data)

    def _handle_event(self, data:dict, evt_type:str):
        self._event_seq_nr += 1
        post_data = {
            '_v': '1.2.2',
            'content': self._production_id,
            'data': data,
            'instance': self._instance_id,
            'platform': PLATFORM_TAG,
            'seq': self._event_seq_nr,
            'type': evt_type
        }
        resp = fetch.web_request('post', EVT_URL, data=post_data)
        if resp.content == b'ok':
            self._post_errors = 0
        else:
            logger.info("Posting progress event failed with HTTP status: %s - %s", resp.status_code, resp.content)
            self._post_errors += 1
            if self._post_errors > 3:
                # No use going on if event posting continues to fail.
                self._status = PlayState.STOPPED
                logger.warning("Aborting progress monitoring; more than 3 events have failed.")


def playtime_monitor(production_id):
    logger.debug("playtime monitor running from thead %s", threading.current_thread().native_id)
    try:
        player = PlayTimeMonitor(production_id)
        player.initialise()
        player.wait_until_playing(15)
        player.monitor_progress()
    except Exception as e:
        logger.error("Playtime monitoring aborted due to unhandled exception: %r", e)