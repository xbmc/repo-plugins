import xbmc
import xbmcgui
from contextlib import contextmanager
from resources.lib.addon.plugin import kodi_log, kodi_traceback, format_name
from timeit import default_timer as timer


class ProgressDialog(object):
    """ Wrapper class for using ProgressDialog in with statement """

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


def try_except_log(log_msg, notification=True):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                kodi_traceback(exc, log_msg, notification)
        return wrapper
    return decorator


@contextmanager
def busy_dialog(is_enabled=True):
    if is_enabled:
        xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
    try:
        yield
    finally:
        if is_enabled:
            xbmc.executebuiltin('Dialog.Close(busydialognocancel)')


def busy_decorator(func):
    def wrapper(*args, **kwargs):
        with busy_dialog:
            response = func(*args, **kwargs)
        return response
    return wrapper


def timer_report(func_name):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            """ Syntactic sugar to time a class function """
            timer_a = timer()
            response = func(self, *args, **kwargs)
            timer_z = timer()
            total_time = timer_z - timer_a
            if total_time > 0.001:
                timer_name = u'{}.{}.'.format(self.__class__.__name__, func_name)
                timer_name = format_name(timer_name, *args, **kwargs)
                kodi_log(u'{}\n{:.3f} sec'.format(timer_name, total_time), 1)
            return response
        return wrapper
    return decorator


@contextmanager
def timer_func(timer_name):
    timer_a = timer()
    try:
        yield
    finally:
        timer_z = timer()
        total_time = timer_z - timer_a
        if total_time > 0.05:
            kodi_log(u'{}\n{:.3f} sec'.format(timer_name, total_time), 1)


def log_output(func_name):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            """ Syntactic sugar to log output of function """
            response = func(self, *args, **kwargs)
            log_text = u'{}.{}.'.format(self.__class__.__name__, func_name)
            log_text = format_name(log_text, *args, **kwargs)
            kodi_log(log_text, 1)
            kodi_log(response, 1)
            return response
        return wrapper
    return decorator
