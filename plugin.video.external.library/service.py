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

import logging

import xbmc

from libs.exception_logger import catch_exception
from libs.kodi_service import initialize_logging
from libs.monitor import PlayMonitor

initialize_logging()
logger = logging.getLogger(__name__)

with catch_exception(logger.error):
    logger.debug('Starting playback monitoring service...')
    kodi_monitor = xbmc.Monitor()
    play_monitor = PlayMonitor()
    while not kodi_monitor.waitForAbort(1.0):
        if (play_monitor.isPlayingVideo()
                and not xbmc.getCondVisibility('Player.Paused')
                and play_monitor.is_monitoring):
            play_monitor.update_time()
logger.debug('Stopped playback monitoring service.')
