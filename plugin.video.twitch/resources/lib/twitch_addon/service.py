# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2019 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""

from six.moves import zip_longest as izip_longest
from six.moves.urllib.parse import quote, unquote

from ast import literal_eval
from datetime import datetime

import threading

from .addon.common import kodi, log_utils
from .addon.constants import Keys
from .addon.utils import BlacklistFilter, i18n, get_stamp_diff, get_vodcast_color
from .addon.player import TwitchPlayer
from .addon import api, cache

import xbmc


class LiveNotificationsThread(threading.Thread):

    def __init__(self):
        super(LiveNotificationsThread, self).__init__()

        self._stopped = threading.Event()

        self.logos = dict()

        self.daemon = True
        self.start()

    def run(self):
        log_utils.log('LiveNotificationsThread: Starting...', log_utils.LOGDEBUG)

        blacklist_filter = BlacklistFilter()
        monitor = xbmc.Monitor()
        window = kodi.Window(10000)

        sleep_time = 1
        delay_time = 300
        notification_duration = 4500
        notification_sleep = (float(notification_duration) / 1000.0) - 0.5  # shift by half second to avoid multiple audible notification
        timestamp = None
        abort = False
        first_run = True

        player = TwitchPlayer(window)

        while not monitor.abortRequested() and not self.stopped():
            time_diff = get_stamp_diff(timestamp)
            if first_run and (timestamp is not None):
                first_run = False
            if (timestamp is None) or (time_diff >= delay_time):
                timestamp = str(datetime.now())
                do_notification, make_audible, start, group_start = self.notify_live()
                if do_notification:
                    try:
                        twitch = api.Twitch()
                    except:
                        twitch = None
                    if twitch:
                        has_token = True if twitch.access_token else False
                        if has_token and do_notification:
                            current_live = self.get_followed_streams(twitch, monitor, blacklist_filter)
                            if current_live is None: break  # if aborted during api requests
                            if current_live:
                                current_online = self.get_online_followed(window)
                                if not first_run or start:
                                    if first_run and group_start:
                                        log_utils.log('Service: Now online |%s|' % current_live, log_utils.LOGDEBUG)
                                        self.set_online_followed(window, value=current_live)
                                        names = [display_name for _id, name, display_name, game in current_live]
                                        triplets = self.grouped(names)
                                        for followed_names in triplets:
                                            message = ', '.join(followed_names)
                                            message = message.rstrip(', ').rstrip(', ')
                                            kodi.notify(i18n('currently_live'), message, duration=notification_duration, sound=make_audible)
                                            if monitor.waitForAbort(notification_sleep):
                                                abort = True
                                                break
                                    else:
                                        log_utils.log('Service: Was online |%s|' % current_online, log_utils.LOGDEBUG)
                                        current_online = [match for match in current_online if match in current_live]
                                        new_online = [match for match in current_live if match not in current_online]
                                        current_online = [match for match in current_online if not any(match[0] == cmp_match[0] for cmp_match in new_online)]
                                        log_utils.log('Service: New online |%s|' % new_online, log_utils.LOGDEBUG)
                                        current_online += new_online
                                        log_utils.log('Service: Now online |%s|' % current_online, log_utils.LOGDEBUG)
                                        self.set_online_followed(window, current_online)

                                        for followed_tuple in new_online:
                                            display_name = followed_tuple[2] if followed_tuple[2] else followed_tuple[1]
                                            game = '' if not followed_tuple[3] else followed_tuple[3]
                                            icon = None if not self.logos.get(followed_tuple[0]) else self.logos.get(followed_tuple[0])
                                            kodi.notify(display_name,
                                                        i18n('started_streaming') %
                                                        (display_name, game),
                                                        duration=notification_duration,
                                                        sound=make_audible, icon_path=icon)
                                            if monitor.waitForAbort(notification_sleep):
                                                abort = True
                                                break
                                else:
                                    log_utils.log('Service: Now online |%s|' % current_live, log_utils.LOGDEBUG)
                                    self.set_online_followed(window, value=current_live)
            if monitor.waitForAbort(sleep_time) or abort or self.stopped():
                break

    @staticmethod
    def grouped(items):
        args = [iter(items)] * 3
        return izip_longest(fillvalue='', *args)

    @staticmethod
    def notify_live():
        notify = kodi.get_setting('live_notify') == 'true'
        audible = group = start = False
        if notify:
            audible = kodi.get_setting('live_notify_audible') == 'true'
            start = kodi.get_setting('live_notify_at_start') == 'true'
            if start:
                group = kodi.get_setting('live_notify_group_start') == 'true'
        return notify, audible, start, group

    def get_followed_streams(self, twitch_api, monitor, blacklist_filter):
        streams = {Keys.TOTAL: 0}
        offset = 0
        all_followed = {Keys.STREAMS: []}
        while streams[Keys.TOTAL] > (offset - 100):
            if offset > 0:
                if monitor.waitForAbort(1):
                    return None
            try:
                streams = twitch_api.get_followed_streams(stream_type='live', offset=offset, limit=100)
            except:
                break
            if streams[Keys.TOTAL] == 0:
                break
            if (streams[Keys.TOTAL] > 0) and (Keys.STREAMS in streams):
                for stream in streams[Keys.STREAMS]:
                    all_followed[Keys.STREAMS].append(stream)
                if streams[Keys.TOTAL] <= (offset + 100):
                    break
                else:
                    offset += 100
        filtered = \
            blacklist_filter.by_type(all_followed, Keys.STREAMS, parent_keys=[Keys.CHANNEL], id_key=Keys._ID, list_type='user')
        filtered = \
            blacklist_filter.by_type(filtered, Keys.STREAMS, game_key=Keys.GAME, list_type='game')
        colorized = []

        for stream in filtered[Keys.STREAMS]:
            if not self.logos.get(stream[Keys.CHANNEL][Keys._ID]):
                self.logos[stream[Keys.CHANNEL][Keys._ID]] = stream[Keys.CHANNEL][Keys.LOGO]
            if stream.get(Keys.STREAM_TYPE) != 'live':
                color = get_vodcast_color()
                if stream[Keys.CHANNEL].get(Keys.DISPLAY_NAME):
                    stream[Keys.CHANNEL][Keys.DISPLAY_NAME] = u'[COLOR={color}]{name}[/COLOR]'.format(name=stream[Keys.CHANNEL][Keys.DISPLAY_NAME], color=color)
                if stream[Keys.CHANNEL].get(Keys.NAME):
                    stream[Keys.CHANNEL][Keys.NAME] = u'[COLOR={color}]{name}[/COLOR]'.format(name=stream[Keys.CHANNEL][Keys.NAME], color=color)
            colorized.append(stream)
        followed_tuples = [(stream[Keys.CHANNEL][Keys._ID], stream[Keys.CHANNEL][Keys.NAME],
                            stream[Keys.CHANNEL][Keys.DISPLAY_NAME], stream[Keys.GAME])
                           for stream in colorized]
        return followed_tuples

    @staticmethod
    def set_online_followed(window, value):
        window.setProperty(key='%s-online_followers' % kodi.get_id(), value=quote(str(value)))

    @staticmethod
    def get_online_followed(window):
        result = unquote(window.getProperty(key='%s-online_followers' % kodi.get_id()))
        if result:
            return literal_eval(result)
        else:
            return []

    def stop(self):
        log_utils.log('LiveNotificationsThread: Stopping...', log_utils.LOGDEBUG)
        self._stopped.set()

    def stopped(self):
        return self._stopped.is_set()


def run():
    log_utils.log('Service: Start', log_utils.LOGNOTICE)

    monitor = xbmc.Monitor()

    check_adaptive()

    try:
        cache.reset_cache()
    except:
        pass

    live_notifications_thread = LiveNotificationsThread()

    while not monitor.abortRequested():

        if monitor.waitForAbort(1.0):
            break

    live_notifications_thread.stop()
    live_notifications_thread.join()

    log_utils.log('Service: Shutdown', log_utils.LOGNOTICE)


def check_adaptive():
    adaptive_addon = False
    adaptive_builtin = False

    kodi_version = kodi.get_kodi_version()
    if (kodi_version.major >= 17) and (kodi_version.application == 'Kodi'):
        adaptive_addon = kodi.addon_enabled('inputstream.adaptive') is not None
    elif (kodi_version.major >= 16) and (kodi_version.minor >= 5) and (kodi_version.application == 'SPMC'):
        adaptive_builtin = True
    else:
        kodi.set_setting('video_quality_ia', 'false')

    kodi.set_setting('video_support_ia_builtin', str(adaptive_builtin).lower())
    kodi.set_setting('video_support_ia_addon', str(adaptive_addon).lower())
    log_utils.log('Startup: detected {0}, setting IA_SUPPORT_BUILTIN = {1}, IA_SUPPORT_ADDON = {2}'
                  .format(kodi_version, adaptive_builtin, adaptive_addon), log_utils.LOGDEBUG)
