__author__ = 'bromix'

import xbmc
import xbmcgui

from ..abstract_context_ui import AbstractContextUI
from ... import utils
from .progress_dialog import KodiProgressDialog
from .progress_dialog_bg import KodiProgressDialogBG


class KodiContextUI(AbstractContextUI):
    def __init__(self, xbmc_addon, context):
        AbstractContextUI.__init__(self)

        self._xbmc_addon = xbmc_addon

        self._context = context
        self._view_mode = None
        pass

    def create_progress_dialog(self, heading, text=None, background=False):
        # only after Frodo
        if background and self._context.get_system_version() > (12, 3):
            return KodiProgressDialogBG(heading, text)

        return KodiProgressDialog(heading, text)

    def get_skin_id(self):
        return xbmc.getSkinDir()

    def on_keyboard_input(self, title, default='', hidden=False):
        # fallback for Frodo
        if self._context.get_system_version() <= (12, 3):
            keyboard = xbmc.Keyboard(default, title, hidden)
            keyboard.doModal()
            if keyboard.isConfirmed() and keyboard.getText():
                text = utils.strings.to_utf8(keyboard.getText())
                return True, text
            else:
                return False, u''
            pass

        # Starting with Gotham (13.X > ...)
        dialog = xbmcgui.Dialog()
        result = dialog.input(utils.strings.to_unicode(title), utils.strings.to_unicode(default),
                              type=xbmcgui.INPUT_ALPHANUM)
        if result != default:
            text = utils.strings.to_unicode(result)
            return True, text

        return False, result

    def on_numeric_input(self, title, default=None):
        if not default:
            default = ''
            pass

        dialog = xbmcgui.Dialog()
        result = dialog.input(title, str(default), type=xbmcgui.INPUT_NUMERIC)
        if result:
            return True, int(result)

        return False, None

    def on_yes_no_input(self, title, text):
        dialog = xbmcgui.Dialog()
        return dialog.yesno(title, text)

    def on_ok(self, title, text):
        dialog = xbmcgui.Dialog()
        return dialog.ok(title, text)

    def on_select(self, title, items, default=-1):
        _dict = {}
        _items = []
        for index, item in enumerate(items):
            if isinstance(item, tuple):
                _dict[index] = item[1]
                _items.append(item[0])
                pass
            else:
                _dict[index] = index
                _items.append(item)
                pass
            pass

        dialog = xbmcgui.Dialog()
        result = dialog.select(title, _items)
        return _dict.get(result, default)

    def show_notification(self, message, header='', image_uri='', time_milliseconds=5000):
        _header = header
        if not _header:
            _header = self._context.get_name()
            pass
        _header = utils.strings.to_utf8(_header)

        _image = image_uri
        if not _image:
            _image = self._context.get_icon()
            pass

        _message = utils.strings.to_unicode(message)
        _message = _message.replace(',', ' ')
        _message = utils.strings.to_utf8(_message)
        _message = _message.replace('\n', ' ')

        xbmc.executebuiltin(
            "Notification(%s, %s, %d, %s)" % (_header, _message, time_milliseconds, _image))
        pass

    def open_settings(self):
        self._xbmc_addon.openSettings()
        pass

    def refresh_container(self):
        xbmc.executebuiltin("Container.Refresh")
        pass

    pass
