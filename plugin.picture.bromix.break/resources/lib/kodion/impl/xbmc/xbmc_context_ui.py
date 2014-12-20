__author__ = 'bromix'

import xbmc

from ..abstract_context_ui import AbstractContextUI


class XbmcContextUI(AbstractContextUI):
    def __init__(self, xbmc_addon, context):
        AbstractContextUI.__init__(self)

        self._xbmc_addon = xbmc_addon

        self._context = context
        pass

    def on_keyboard_input(self, title, default='', hidden=False):
        keyboard = xbmc.Keyboard(default, title, hidden)
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
            return True, keyboard.getText()

        return False, ''

    def show_notification(self, message, header='', image_uri='', time_milliseconds=5000):
        _header = header
        if not _header:
            _header = self._context.get_name()
            pass

        _image = image_uri
        if not _image:
            _image = self._context.get_icon()
            pass

        xbmc.executebuiltin("Notification(%s, %s, %d, %s)" % (_header, message.replace(',', ' '), time_milliseconds, _image))
        pass

    def open_settings(self):
        self._xbmc_addon.openSettings()
        pass

    def refresh_container(self):
        xbmc.executebuiltin("Container.Refresh")
        pass

    pass
