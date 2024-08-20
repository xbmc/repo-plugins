from jurialmunkey.parser import try_type


class PropertySetter():
    @property
    def property_window(self):
        try:
            return self._property_window
        except AttributeError:
            import xbmcgui
            try:
                self._property_window = xbmcgui.Window(10000)
            except RuntimeError:  # If window id does not exist
                return
            return self._property_window

    def get_property(self, name, set_property=None, clear_property=False, is_type=None):
        if not self.property_window:
            return
        name = f'TMDbHelper.{name}'
        ret_property = set_property or self.property_window.getProperty(name)
        if clear_property:
            self.property_window.clearProperty(name)
        if set_property is not None:
            self.property_window.setProperty(name, f'{set_property}')
        return try_type(ret_property, is_type or str)
