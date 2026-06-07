import xbmcgui
from resources.lib.addon.plugin import executebuiltin
from resources.lib.addon.logger import kodi_log
""" Top level module only import plugin/constants/logger """


class ProgressDialog(object):
    """ ContextManager for DialogProgressBG use in with statement """

    def __init__(self, title='', message='', total=100, logging=1):
        self.logging = logging
        self._create(title, message, total)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _create(self, title='', message='', total=100):
        self._pd = xbmcgui.DialogProgressBG()
        self._pd.create(title, message)
        self._count = 0
        self._total = total
        self._title = title
        kodi_log([self._title, ' - 00 ', message], self.logging)
        return self._pd

    def update(self, message='', count=1, total=None):
        if not self._pd:
            return
        if total:  # Reset counter if given new total
            self._count = count
            self._total = total
        self._count += count
        self._progr = (((self._count) * 100) // self._total)
        self._pd.update(self._progr, message=message) if message else self._pd.update(self._progr)
        kodi_log([self._title, ' - ', self._progr, ' ', message], self.logging)
        return self._progr

    def close(self):
        if not self._pd:
            return
        kodi_log([self._title, ' - Done!'], self.logging)
        self._pd.close()


class BusyDialog():
    def __init__(self, is_enabled=True):
        """ ContextManager for DialogBusy in with statement """
        if is_enabled:
            executebuiltin('ActivateWindow(busydialognocancel)')
        self.is_enabled = is_enabled

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if not self.is_enabled:
            return
        executebuiltin('Dialog.Close(busydialognocancel)')


def busy_decorator(func):
    def wrapper(*args, **kwargs):
        """ Decorator for wrappingBusyDialog around a function """
        with BusyDialog():
            response = func(*args, **kwargs)
        return response
    return wrapper
