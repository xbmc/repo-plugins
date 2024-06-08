class TokenHandler:
    from tmdbhelper.lib.addon.plugin import (get_setting as _get_setting,
                                            set_setting as _set_setting,)
    from jurialmunkey.window import get_property as _get_property

    _get_setting = staticmethod(_get_setting)
    _set_setting = staticmethod(_set_setting)
    _get_property = staticmethod(_get_property)

    def __init__(self, name=None, store_as=None):
        self.name = name
        self._value = ''
        self._store_as = store_as

    @property
    def value(self):
        if self._store_as == 'setting':
            return self._get_setting(self.name, 'str')
        if self._store_as == 'property':
            return self._get_property(self.name, is_type=str)
        return self._value

    @value.setter
    def value(self, value):
        if self._store_as == 'setting':
            self._set_setting(self.name, value, 'str')
        elif self._store_as == 'property':
            self._get_property(self.name, set_property=f'{value}')
        else:
            self._value = value
