# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import xbmc  # pylint: disable=import-error
import xbmcaddon  # pylint: disable=import-error

from ..constants import SUBTITLE_LANGUAGE


class Settings:

    def __init__(self, addon=None):
        self._addon = addon
        self._shallow_cache = {}

    def get_bool(self, setting_id):
        return self._get(setting_id, 'bool')

    def set_bool(self, setting_id, setting_value):
        self._set(setting_id, setting_value, 'bool')

    def get_int(self, setting_id):
        return self._get(setting_id, 'int')

    def set_int(self, setting_id, setting_value):
        self._set(setting_id, setting_value, 'int')

    def get_string(self, setting_id):
        return self._get(setting_id, 'string')

    def set_string(self, setting_id, setting_value):
        self._set(setting_id, setting_value, 'string')

    def get_number(self, setting_id):
        return self._get(setting_id, 'number')

    def set_number(self, setting_id, setting_value):
        self._set(setting_id, setting_value, 'number')

    def get(self, setting_id):
        return self._get(setting_id)

    def set(self, setting_id, setting_value):
        self._set(setting_id, setting_value)

    @property
    def addon(self):
        if not self._addon:
            self._addon = xbmcaddon.Addon()
        return self._addon

    @property
    def shallow_cache(self):
        return self._shallow_cache

    def _get(self, setting_id, setting_type=None):
        if setting_id in self.shallow_cache:
            return self.shallow_cache[setting_id]

        if setting_type == 'bool':
            payload = self.addon.getSettingBool(setting_id)

        elif setting_type == 'int':
            payload = self.addon.getSettingInt(setting_id)

        elif setting_type == 'string':
            payload = self.addon.getSettingString(setting_id)

        elif setting_type == 'number':
            payload = self.addon.getSettingNumber(setting_id)

        else:
            payload = self.addon.getSetting(setting_id)

        self.shallow_cache[setting_id] = payload
        return payload

    def _set(self, setting_id, setting_value, setting_type=None):
        self.shallow_cache[setting_id] = setting_value

        if setting_type == 'bool':
            self.addon.setSettingBool(setting_id, setting_value)
            return

        if setting_type == 'int':
            self.addon.setSettingInt(setting_id, setting_value)
            return

        if setting_type == 'string':
            self.addon.setSettingString(setting_id, setting_value)
            return

        if setting_type == 'number':
            self.addon.setSettingNumber(setting_id, setting_value)
            return

        self.addon.setSetting(setting_id, setting_value)
        return

    @property
    def video_quality(self):
        _map = {
            0: 240,
            1: 360,
            2: 480,
            3: 720,
            4: 1080,
            5: 1440,
            6: 2160,
            7: 4320,
            8: 'mp4',
            9: 'webm'
        }

        return _map.get(self.get_int('quality'), 4)

    @property
    def limit_to_30fps(self):
        return self.get_bool('limit30')

    @property
    def hdr(self):
        return self.get_bool('hdr')

    @property
    def language(self):
        return self.get_string('language')

    @language.setter
    def language(self, value):
        self.set_string('language', value)

    @property
    def region(self):
        return self.get_string('region')

    @region.setter
    def region(self, value):
        self.set_string('region', value)

    @property
    def subtitle_language(self):
        _map = {
            0: SUBTITLE_LANGUAGE.NONE,
            1: SUBTITLE_LANGUAGE.PROMPT,
            2: SUBTITLE_LANGUAGE.CURRENT_W_FALLBACK,
            3: SUBTITLE_LANGUAGE.CURRENT,
            4: SUBTITLE_LANGUAGE.CURRENT_WO_ASR,
        }

        return _map.get(self.get_int('subtitle.language'), SUBTITLE_LANGUAGE.NONE)

    @subtitle_language.setter
    def subtitle_language(self, value):
        self.set_int('subtitle.language', int(value))

    @property
    def subtitle_label(self):
        return self.get_string('subtitle.label')

    @subtitle_label.setter
    def subtitle_label(self, value):
        self.set_string('subtitle.label', value)

    @property
    def data_cache_ttl(self):
        return self.get_int('cache.ttl.data')

    @property
    def function_cache_ttl(self):
        return self.get_int('cache.ttl.function')

    @property
    def data_cache_limit(self):
        return self.get_int('cache.limit.data')

    @property
    def reset_function_cache_refresh(self):
        return self.get_bool('cache.clear.function.refresh')

    @property
    def log_api_requests(self):
        return self.get_bool('log.api.requests')

    @property
    def post_play_minimum_progress(self):
        return self.get_int('post.play.min.progress')

    @property
    def autoplay_related(self):
        return self.get_bool('post.play.autoplay.related')

    @property
    def post_play_rate(self):
        if not self.get_bool('post.play.rate'):
            return False

        is_playlist = int(xbmc.PlayList(xbmc.PLAYLIST_VIDEO).size()) >= 2

        if not self.get_bool('post.play.rate.playlist') and is_playlist:
            return False

        return self.get_bool('post.play.rate')

    @property
    def search_history_maximum(self):
        return self.get_int('search.history.items')

    @property
    def favorite_channel_maximum(self):
        return self.get_int('favorite.channel.items')

    @property
    def favorite_playlist_maximum(self):
        return self.get_int('favorite.playlist.items')

    def show_main_menu_item(self, item, value=None):
        if not isinstance(value, bool):
            return self.get_bool('main.menu.%s' % item)

        return self.set_bool('main.menu.%s' % item, value)

    def get_privacy_policy(self):
        return self.get_string('privacy.policy.accepted')

    def set_privacy_policy(self, value):
        return self.set_string('privacy.policy.accepted', value)
