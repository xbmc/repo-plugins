import xbmc
from timeit import default_timer as timer
from resources.lib.addon.plugin import get_setting, format_name
""" Lazyimports
import traceback
"""


ADDON_LOGNAME = '[plugin.video.themoviedb.helper]\n'
DEBUG_LOGGING = get_setting('debug_logging')


def kodi_log(value, level=0):
    try:
        if isinstance(value, list):
            value = ''.join(map(str, value))
        if isinstance(value, bytes):
            value = value.decode('utf-8')
        logvalue = f'{ADDON_LOGNAME}{value}'
        if level == 2 and DEBUG_LOGGING:
            xbmc.log(logvalue, level=xbmc.LOGINFO)
        elif level == 1:
            xbmc.log(logvalue, level=xbmc.LOGINFO)
        else:
            xbmc.log(logvalue, level=xbmc.LOGDEBUG)
    except Exception as exc:
        xbmc.log(f'Logging Error: {exc}', level=xbmc.LOGINFO)


def kodi_traceback(exception, log_msg=None, log_level=1, notification=True):
    """ Method for logging caught exceptions and notifying user """
    if notification:
        from xbmcgui import Dialog
        from resources.lib.addon.plugin import get_localized
        head = f'TheMovieDb Helper {get_localized(257)}'
        Dialog().notification(head, get_localized(2104))
    msg = f'Error Type: {type(exception).__name__}\nError Contents: {exception.args!r}'
    msg = [log_msg, '\n', msg, '\n'] if log_msg else [msg, '\n']
    try:
        import traceback
        kodi_log(msg + traceback.format_tb(exception.__traceback__), log_level)
    except Exception as exc:
        kodi_log(f'ERROR WITH TRACEBACK!\n{exc}\n{msg}', log_level)


def kodi_try_except(log_msg, exception_type=Exception):
    """ Decorator to catch exceptions and notify error for uninterruptable services """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_type as exc:
                kodi_traceback(exc, log_msg)
        return wrapper
    return decorator


class TryExceptLog():
    def __init__(self, exc_types=[Exception], log_msg=None, log_level=1):
        """ ContextManager to allow exception passing and log """
        self.log_msg = log_msg
        self.exc_types = exc_types
        self.log_level = log_level

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type and exc_type not in self.exc_types:
            return
        if self.log_level:
            kodi_log(f'{self.log_msg or "ERROR PASSED"}: {exc_type}', self.log_level)
        return True


def timer_report(func_name):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            """ Syntactic sugar to time a class function """
            timer_a = timer()
            response = func(self, *args, **kwargs)
            timer_z = timer()
            total_time = timer_z - timer_a
            if total_time > 0.001:
                timer_name = f'{self.__class__.__name__}.{func_name}.'
                timer_name = format_name(timer_name, *args, **kwargs)
                kodi_log(f'{timer_name}\n{total_time:.3f} sec', 1)
            return response
        return wrapper
    return decorator


def log_output(func_name):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            """ Syntactic sugar to log output of function """
            response = func(self, *args, **kwargs)
            log_text = f'{self.__class__.__name__}.{func_name}.'
            log_text = format_name(log_text, *args, **kwargs)
            kodi_log(log_text, 1)
            kodi_log(response, 1)
            return response
        return wrapper
    return decorator


class TimerFunc():
    def __init__(self, timer_name, log_threshold=0.05, inline=False):
        """ ContextManager for timing code blocks and outputing to log """
        self.inline = ' ' if inline else '\n'
        self.timer_name = timer_name
        self.log_threshold = log_threshold
        self.timer_a = timer()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        timer_z = timer()
        total_time = timer_z - self.timer_a
        if total_time > self.log_threshold:
            kodi_log(f'{self.timer_name}{self.inline}{total_time:.3f} sec', 1)


class TimerList():
    def __init__(self, dict_obj, list_name, log_threshold=0.001, logging=True):
        """ ContextManager for timing code blocks and storing in a list """
        self.list_obj = dict_obj.setdefault(list_name, [])
        self.log_threshold = log_threshold
        self.timer_a = timer() if logging else None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if not self.timer_a:
            return
        timer_z = timer()
        total_time = timer_z - self.timer_a
        if total_time > self.log_threshold:
            self.list_obj.append(total_time)


def log_timer_report(timer_lists, paramstring):
    _threaded = [
        'item_api', 'item_tmdb', 'item_ftv', 'item_map', 'item_cache',
        'item_set', 'item_get', 'item_getx', 'item_non', 'item_nonx', 'item_art']
    total_log = timer_lists.pop('total', 0)
    timer_log = ['DIRECTORY TIMER REPORT\n', paramstring, '\n']
    timer_log.append('------------------------------\n')
    for k, v in timer_lists.items():
        if k in _threaded:
            avg_time = f'{sum(v) / len(v):7.3f} sec avg | {max(v):7.3f} sec max | {len(v):3}' if v else '  None'
            timer_log.append(f' - {k:12s}: {avg_time}\n')
        elif k[:4] == 'item':
            avg_time = f'{sum(v) / len(v):7.3f} sec avg | {sum(v):7.3f} sec all | {len(v):3}' if v else '  None'
            timer_log.append(f' - {k:12s}: {avg_time}\n')
        else:
            tot_time = f'{sum(v) / len(v):7.3f} sec' if v else '  None'
            timer_log.append(f'{k:15s}: {tot_time}\n')
    timer_log.append('------------------------------\n')
    tot_time = f'{sum(total_log) / len(total_log):7.3f} sec' if total_log else '  None'
    timer_log.append(f'{"Total":15s}: {tot_time}\n')
    max_thrd = get_setting("max_threads", mode="int")
    if max_thrd:
        timer_log.append(f'Threads x{max_thrd}\n')
    for k, v in timer_lists.items():
        if v and k in _threaded:
            timer_log.append(f'\n{k}:\n{" ".join([f"{i:.3f} " for i in v])}\n')
    kodi_log(timer_log, 1)
