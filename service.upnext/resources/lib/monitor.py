# -*- coding: utf-8 -*-
# GNU General Public License v2.0 (see COPYING or https://www.gnu.org/licenses/gpl-2.0.txt)

from __future__ import absolute_import, division, unicode_literals
from xbmc import Monitor
from api import Api
from playbackmanager import PlaybackManager
from player import UpNextPlayer
from statichelper import from_unicode
from utils import decode_json, get_property, get_setting_bool, log as ulog


class UpNextMonitor(Monitor):
    """Service monitor for Kodi"""

    def __init__(self):
        """Constructor for Monitor"""
        self.player = UpNextPlayer()
        self.api = Api()
        self.playback_manager = PlaybackManager()
        Monitor.__init__(self)

    def log(self, msg, level=1):
        """Log wrapper"""
        ulog(msg, name=self.__class__.__name__, level=level)

    def run(self):
        """Main service loop"""
        self.log('Service started', 0)

        while not self.abortRequested():
            # check every 1 sec
            if self.waitForAbort(1):
                # Abort was requested while waiting. We should exit
                break

            if not self.player.is_tracking():
                continue

            if bool(get_property('PseudoTVRunning') == 'True'):
                self.player.disable_tracking()
                continue

            if get_setting_bool('disableNextUp'):
                # Next Up is disabled
                self.player.disable_tracking()
                continue

            if self.player.isExternalPlayer():
                self.log('Up Next tracking stopped, external player detected', 2)
                self.player.disable_tracking()
                continue

            last_file = self.player.get_last_file()
            try:
                current_file = self.player.getPlayingFile()
            except RuntimeError:
                self.log('Up Next tracking stopped, failed player.getPlayingFile()', 2)
                self.player.disable_tracking()
                continue

            if last_file and last_file == current_file:
                # Already processed this playback before
                continue

            try:
                total_time = self.player.getTotalTime()
            except RuntimeError:
                self.log('Up Next tracking stopped, failed player.getTotalTime()', 2)
                self.player.disable_tracking()
                continue

            if total_time == 0:
                self.log('Up Next tracking stopped, no file is playing', 2)
                self.player.disable_tracking()
                continue

            try:
                play_time = self.player.getTime()
            except RuntimeError:
                self.log('Up Next tracking stopped, failed player.getTime()', 2)
                self.player.disable_tracking()
                continue

            notification_time = self.api.notification_time(total_time=total_time)
            if total_time - play_time > notification_time:
                # Media hasn't reach notification time yet, waiting a bit longer...
                continue

            self.player.set_last_file(from_unicode(current_file))
            self.log('Show notification as episode (of length %d secs) ends in %d secs' % (total_time, notification_time), 2)
            self.playback_manager.launch_up_next()
            self.log('Up Next style autoplay succeeded', 2)
            self.player.disable_tracking()

        self.log('Service stopped', 0)

    def onNotification(self, sender, method, data):  # pylint: disable=invalid-name
        """Notification event handler for accepting data from add-ons"""
        if not method.endswith('upnext_data'):  # Method looks like Other.upnext_data
            return

        decoded_data, encoding = decode_json(data)
        if decoded_data is None:
            self.log('Received data from sender %s is not JSON: %s' % (sender, data), 2)
            return

        decoded_data.update(id='%s_play_action' % sender.replace('.SIGNAL', ''))
        self.api.addon_data_received(decoded_data, encoding=encoding)
