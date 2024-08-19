
from xbmc import Monitor
from tmdbhelper.lib.addon.plugin import get_setting, encode_url
from tmdbhelper.lib.addon.logger import kodi_log
from tmdbhelper.lib.addon.tmdate import set_timestamp, get_timestamp
from jurialmunkey.window import get_property
import jurialmunkey.thread as jurialmunkey_thread


def has_property_lock(property_name, timeout=5, polling=0.05):
    """ Checks for a window property lock and wait for it to be cleared before continuing
    Returns True after property clears if was locked
    """
    if not get_property(property_name):
        return False
    monitor = Monitor()
    timeend = set_timestamp(timeout)
    timeexp = True
    while not monitor.abortRequested() and get_property(property_name) and timeexp:
        monitor.waitForAbort(polling)
        timeexp = get_timestamp(timeend)
    if not timeexp:
        kodi_log(f'{property_name} Timeout!', 1)
    del monitor
    return True


def use_thread_lock(property_name, timeout=10, polling=0.05, combine_name=False):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            name = encode_url(f"{property_name}.{'.'.join(args)}", **kwargs) if combine_name else property_name
            if not has_property_lock(name, timeout, polling):  # Check if locked and wait if it is
                get_property(name, 1)  # Lock thread for others
            response = func(self, *args, **kwargs)  # Get our response
            get_property(name, clear_property=True)  # Unlock for other threads
            return response
        return wrapper
    return decorator


class ParallelThread(jurialmunkey_thread.ParallelThread):
    thread_max = get_setting('max_threads', mode='int')

    @staticmethod
    def kodi_log(msg, level=0):
        kodi_log(msg, level)
