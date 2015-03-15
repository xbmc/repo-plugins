__author__ = 'bromix'

from .. import constants


class AbstractSettings(object):
    def __init__(self):
        object.__init__(self)
        pass

    def get_string(self, setting_id, default_value=None):
        raise NotImplementedError()

    def set_string(self, setting_id, value):
        raise NotImplementedError()

    def open_settings(self):
        raise NotImplementedError()

    def get_int(self, setting_id, default_value, converter=None):
        if not converter:
            converter = lambda x: x
            pass

        value = self.get_string(setting_id)
        if value is None or value == '':
            return default_value

        try:
            return converter(int(value))
        except Exception, ex:
            from . import log

            log("Failed to get setting '%s' as 'int' (%s)" % setting_id, ex.__str__())
            pass

        return default_value

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
        if value is None or value == '':
            return default_value

        if value != 'false' and value != 'true':
            return default_value

        return value == 'true'

    def get_items_per_page(self):
        return self.get_int(constants.setting.ITEMS_PER_PAGE, 50, lambda x: (x + 1) * 5)

    def get_video_quality(self, quality_map_override=None):
        vq_dict = {0: 240,
                   1: 360,
                   2: 480,  # 576 seems not to work well
                   3: 720,
                   4: 1080,
                   5: 2160,
                   6: 4320}

        if quality_map_override is not None:
            vq_dict = quality_map_override
            pass

        vq = self.get_int(constants.setting.VIDEO_QUALITY, 1)
        return vq_dict[vq]

    def show_fanart(self):
        return self.get_bool(constants.setting.SHOW_FANART, True)

    def get_search_history_size(self):
        return self.get_int(constants.setting.SEARCH_SIZE, 50, lambda x: x * 10)

    def is_setup_wizard_enabled(self):
        return self.get_bool(constants.setting.SETUP_WIZARD, False)

    def is_override_view_enabled(self):
        return self.get_bool(constants.setting.VIEW_OVERRIDE, False)

    def is_support_alternative_player_enabled(self):
        return self.get_bool(constants.setting.SUPPORT_ALTERNATIVE_PLAYER, False)

    pass