from sqlite3 import converters

__author__ = 'bromix'

import re


class AbstractSettings(object):
    # addon
    ADDON_SETUP = 'addon.setup'  # (bool)
    ADDON_CACHE_CLEAR = 'addon.cache.clear'  # (bool)
    ADDON_CACHE_SIZE = 'addon.cache.size'  # (int)
    ADDON_SHOW_FANART = 'addon.fanart.show'  # (bool)
    ADDON_SEARCH_SIZE = 'addon.search.size'  # (int)
    ADDON_ITEMS_PER_PAGE = 'addon.items.per_page'  # (int)

    # video/playback
    VIDEO_QUALITY = 'video.quality'  # (int)
    VIDEO_QUALITY_ASK = 'video.quality.ask'  # (bool)

    # override view
    VIEW_OVERRIDE = 'view.override'  # (bool)
    VIEW_DEFAULT = 'view.override.default'  # (int)
    VIEW_X = 'view.override.%s'  # (int)

    SUPPORT_ALTERNATIVE_PLAYER = 'nightcrawler.support.alternative_player'  # (bool)

    # login
    LOGIN_USERNAME = 'login.username'
    LOGIN_PASSWORD = 'login.password'
    LOGIN_ACCESS_TOKEN = 'login.access_token'
    LOGIN_ACCESS_TOKEN_EXPIRES = 'login.expires_in'
    LOGIN_REFRESH_TOKEN = 'login.refresh_token'
    LOGIN_HASH = 'login.hash'

    def __init__(self):
        object.__init__(self)
        pass

    def get_string(self, setting_id, default_value=None):
        raise NotImplementedError()

    def set_string(self, setting_id, value):
        raise NotImplementedError()

    def get_int(self, setting_id, default_value, converter=None):
        if not converter:
            converter = lambda x: x
            pass

        value = self.get_string(setting_id)
        if value is not None and re.match(r'\d+', value):
            return converter(int(value))

        if not isinstance(default_value, int):
            return -1

        return int(default_value)

    def set_int(self, setting_id, value):
        self.set_string(setting_id, str(value))
        pass

    def set_bool(self, setting_id, value):
        if value:
            self.set_string(setting_id, 'true')
        else:
            self.set_string(setting_id, 'false')

    def get_bool(self, setting_id, default_value):
        value = self.get_string(setting_id)
        if value is not None and value.lower() in ['false', 'true', '1', '0']:
            return value.lower() == 'true' or value.lower() == '1'

        # don't crash, but return always false
        if not isinstance(default_value, bool):
            return False

        return default_value

    def get_items_per_page(self):
        return self.get_int(self.ADDON_ITEMS_PER_PAGE, 50, lambda x: (x + 1) * 5)

    def get_video_quality(self, video_quality_index=None):
        if not video_quality_index:
            video_quality_index = [240, 360, 480, 720, 1080, 2160, 4320]
            pass
        return self.get_int(self.VIDEO_QUALITY, video_quality_index[0], converter=lambda x: video_quality_index[x])

    def ask_for_video_quality(self):
        return self.get_bool(self.VIDEO_QUALITY_ASK, False)

    def show_fanart(self):
        return self.get_bool(self.ADDON_SHOW_FANART, True)

    def get_search_history_size(self):
        return self.get_int(self.ADDON_SEARCH_SIZE, 50, lambda x: x * 10)

    def is_setup_wizard_enabled(self):
        return self.get_bool(self.ADDON_SETUP, False)

    def is_override_view_enabled(self):
        return self.get_bool(self.VIEW_OVERRIDE, False)

    def is_support_alternative_player_enabled(self):
        return self.get_bool(self.SUPPORT_ALTERNATIVE_PLAYER, False)

    def is_clear_cache_enabled(self):
        return self.get_bool(self.ADDON_CACHE_CLEAR, False)

    def disable_clear_cache(self):
        self.set_bool(self.ADDON_CACHE_CLEAR, False)

    pass