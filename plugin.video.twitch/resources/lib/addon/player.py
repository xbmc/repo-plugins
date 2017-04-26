# -*- coding: utf-8 -*-
"""
    Player for handling Callbacks only

    Copyright (C) 2016 Twitch-on-Kodi

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import xbmc
from common import kodi, log_utils
import api, utils, cache
from constants import Keys, LINE_LENGTH
from converter import JsonListItemConverter

ID = kodi.get_id()
monitor = xbmc.Monitor()
converter = JsonListItemConverter(LINE_LENGTH)


class TwitchPlayer(xbmc.Player):
    window = kodi.Window(10000)
    player_keys = {
        'twitch_playing': ID + '-twitch_playing'
    }
    seek_keys = {
        'seek_time': ID + '-seek_time',
    }
    reconnect_keys = {
        'stream': ID + '-livestream'
    }

    def __init__(self, *args, **kwargs):
        log_utils.log('Player: Start', log_utils.LOGDEBUG)
        self.reset()

    def reset(self):
        self.reset_player()
        self.reset_seek()
        self.reset_reconnect()

    def reset_seek(self):
        for k in self.seek_keys.keys():
            self.window.clearProperty(key=self.seek_keys[k])

    def reset_reconnect(self):
        for k in self.reconnect_keys.keys():
            self.window.clearProperty(key=self.reconnect_keys[k])

    def reset_player(self):
        for k in self.player_keys.keys():
            self.window.clearProperty(key=self.player_keys[k])

    def onPlayBackStarted(self):
        twitch_host_matches = ['jtvnw.', 'ttvnw.', 'twitch.tv']
        is_playing = self.window.getProperty(key=self.player_keys['twitch_playing']) == 'True'
        seek_time = self.window.getProperty(key=self.seek_keys['seek_time'])
        if is_playing:
            is_playing = any(host_match in self.getPlayingFile() for host_match in twitch_host_matches)
        log_utils.log('Player: |onPlayBackStarted| isTwitch |{0}| SeekTime |{1}|'.format(is_playing, seek_time), log_utils.LOGDEBUG)
        if not is_playing:
            self.reset()
        else:
            if seek_time:
                seek_time = float(seek_time)
                self.seekTime(seek_time)

    def onPlayBackStopped(self):
        log_utils.log('Player: |onPlayBackStopped|', log_utils.LOGDEBUG)
        self.reset()

    def onPlayBackEnded(self):
        is_playing = self.window.getProperty(key=self.player_keys['twitch_playing']) == 'True'
        log_utils.log('Player: |onPlayBackEnded| isTwitch |{0}|'.format(is_playing), log_utils.LOGDEBUG)
        need_reset = True
        if is_playing:
            reconnect = kodi.get_setting('live_reconnect') == 'true'
            if reconnect:
                live_channel = self.window.getProperty(self.reconnect_keys['stream'])
                if live_channel:
                    channel_id, name, display_name = live_channel.split(',')
                    retries = 0
                    max_retries = 5
                    while not monitor.abortRequested():
                        if monitor.waitForAbort(5):
                            break
                        break
                    if monitor.abortRequested():
                        dialog = None
                    else:
                        dialog = kodi.ProgressDialog(kodi.get_name(), line1=utils.i18n('attempt_reconnect') % display_name,
                                                     line2=utils.i18n('attempt_number') % (retries + 1), line3=utils.i18n('retry_seconds') % 60)
                    if dialog:
                        need_reset = False
                        with dialog:
                            while (not monitor.abortRequested()) and (retries < max_retries) and (not dialog.is_canceled()):
                                wait_time = 0.0
                                abort = False
                                while wait_time <= 120.0:
                                    if monitor.waitForAbort(0.5) or dialog.is_canceled():
                                        abort = True
                                        break
                                    wait_time += 1.0
                                    if (wait_time % 2) == 0:
                                        percent = int(((wait_time / 120) * 100))
                                        dialog.update(percent=percent, line3=utils.i18n('retry_seconds') % ((120.0 - wait_time) / 2))
                                if abort:
                                    break
                                retries += 1
                                try:
                                    try:
                                        cache.reset_cache()
                                    except:
                                        pass
                                    twitch = api.Twitch()
                                    quality = utils.get_default_quality('stream', channel_id)
                                    if quality:
                                        quality = quality[channel_id]['quality']
                                    videos = twitch.get_live(name)
                                    result = twitch.get_channel_stream(channel_id)[Keys.STREAM]
                                    item_dict = converter.stream_to_playitem(result)
                                    video = converter.get_video_for_quality(videos, ask=False, quality=quality)
                                    if video:
                                        log_utils.log('Attempting playback using quality |%s| @ |%s|' % (video['name'], video['url']), log_utils.LOGDEBUG)
                                        item_dict['path'] = video['url']
                                        playback_item = kodi.create_item(item_dict, add=False)
                                        stream_name = result[Keys.CHANNEL][Keys.DISPLAY_NAME] \
                                            if result[Keys.CHANNEL][Keys.DISPLAY_NAME] else result[Keys.CHANNEL][Keys.NAME]
                                        self.window.setProperty(self.reconnect_keys['stream'], '{0},{1},{2}'.format(channel_id, name, stream_name))
                                        self.play(item_dict['path'], playback_item)
                                        if utils.irc_enabled() and twitch.access_token:
                                            username = twitch.get_username()
                                            if username:
                                                utils.exec_irc_script(username, name)
                                        break
                                except:
                                    log_utils.log('Player: |Reconnection| Failed attempt |{0}|'.format(retries), log_utils.LOGERROR)
                                dialog.update(0, line2=utils.i18n('attempt_number') % (retries + 1), line3=utils.i18n('retry_seconds') % 60)
                        if dialog.is_canceled():
                            self.reset()
        if need_reset:
            self.reset()
