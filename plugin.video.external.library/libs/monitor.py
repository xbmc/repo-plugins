# Copyright (C) 2023, Roman Miroshnychenko aka Roman V.M.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# pylint: disable=broad-exception-caught,attribute-defined-outside-init
"""Playback progress monitor"""

import logging
from urllib.parse import quote

import xbmc

from libs import json_rpc_api
from libs.kodi_service import ADDON, ADDON_ID
from libs.mem_storage import MemStorage

logger = logging.getLogger(__name__)


class PlayMonitor(xbmc.Player):
    """
    Monitors playback status and updates watches status
    for an episode or a movie from an external library
    """
    def __init__(self):
        super().__init__()
        self._mem_storage = MemStorage()
        self._clear_state()

    def _clear_state(self):
        self.is_monitoring = False
        self._current_time = -1
        self._total_time = -1
        self._playing_file = None
        self._item_info = None

    def onPlayBackStarted(self):
        self._playing_file = self.getPlayingFile()
        self._item_info = self._get_item_info()
        if self._item_info is None:
            self._clear_state()
            return
        self.is_monitoring = True
        try:
            self._total_time = self.getTotalTime()
        except Exception:
            self._total_time = -1
        logger.debug('Started monitoring %s', self._playing_file)

    def onPlayBackStopped(self):
        self._send_played_file_state()
        self._clear_state()
        logger.debug('Stopped monitoring %s. Playback stopped.', self._playing_file)

    def onPlayBackEnded(self):
        self._send_played_file_state()
        self._clear_state()
        logger.debug('Stopped monitoring %s. Playback ended.', self._playing_file)

    def onPlayBackPaused(self):
        if self._should_send_resume():
            self._send_resume()
        logger.debug('Paused monitoring %s', self._playing_file)

    def update_time(self):
        try:
            self._current_time = self.getTime()
        except Exception:
            self._current_time = -1
        if self._total_time <= 0:
            try:
                self._total_time = self.getTotalTime()
            except Exception:
                self._total_time = -1

    def _get_item_info(self):
        if listing := self._mem_storage.get(f'__{ADDON_ID}_media_list__'):
            files_on_shares = ADDON.getSettingBool('files_on_shares')
            for item in listing:
                if files_on_shares and item['file'] == self._playing_file:
                    return item
                if quote(item['file']) in self._playing_file:
                    return item
        return None

    def _should_send_playcount(self):
        watched_threshold = ADDON.getSettingInt('watched_threshold_percent') / 100
        return (self._current_time != -1 and self._total_time > 0
                and (self._current_time / self._total_time) >= watched_threshold)

    def _send_playcount(self):
        logger.debug('Updating playcount for %s %s', self._item_info, self._playing_file)
        item_id_param = self._item_info['item_id_param']
        new_playcount = self._item_info['playcount'] + 1
        json_rpc_api.update_playcount(item_id_param, self._item_info[item_id_param], new_playcount)

    def _should_send_resume(self):
        return (self._current_time != -1
                and self._total_time != -1
                and self._current_time > ADDON.getSettingInt('playtime_to_skip'))

    def _send_resume(self):
        logger.debug('Updating resume for %s %s', self._item_info, self._playing_file)
        item_id_param = self._item_info['item_id_param']
        json_rpc_api.update_resume(item_id_param, self._item_info[item_id_param],
                                   self._current_time, self._total_time)

    def _send_played_file_state(self):
        if self._should_send_playcount():
            self._send_playcount()
        elif self._should_send_resume():
            self._send_resume()
