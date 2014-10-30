class AbstractSettings(object):
    LOGIN_USERNAME = 'kodimon.login.username'
    LOGIN_PASSWORD = 'kodimon.login.password'
    LOGIN_HASH = 'kodimon.login.hash'
    ACCESS_TOKEN = 'kodimon.access_token'
    ACCESS_TOKEN_EXPIRES = 'kodimon.access_token.expires'

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
        import constants
        return self.get_int(constants.SETTING_ITEMS_PER_PAGE, 50, lambda x: (x+1)*5)

    def get_video_quality(self):
        import constants
        vq_dict = {0: 576,
                   1: 720,
                   2: 1080,
                   3: 2160}
        vq = self.get_int(constants.SETTING_VIDEO_QUALITY, 1)
        return vq_dict[vq]

    pass