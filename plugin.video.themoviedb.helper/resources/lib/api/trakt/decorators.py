from resources.lib.addon.plugin import format_name
from resources.lib.addon.logger import kodi_log
from resources.lib.addon.tmdate import set_timestamp, get_timestamp
from resources.lib.addon.window import get_property
from resources.lib.addon.parser import encode_url
from xbmc import Monitor


def _is_property_lock(property_name, timeout=5, polling=0.2):
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


def use_thread_lock(property_name, timeout=10, polling=0.1, combine_name=False):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            name = encode_url(f"{property_name}.{'.'.join(args)}", **kwargs) if combine_name else property_name
            if not _is_property_lock(name, timeout, polling):  # Check if locked and wait if it is
                get_property(name, 1)  # Lock thread for others
            response = func(self, *args, **kwargs)  # Get our response
            get_property(name, clear_property=True)  # Unlock for other threads
            return response
        return wrapper
    return decorator


def is_authorized(func):
    def wrapper(self, *args, **kwargs):
        if kwargs.get('authorize', True) and not self.authorize():
            return
        return func(self, *args, **kwargs)
    return wrapper


def use_lastupdated_cache(cache, func, *args, sync_info=None, cache_name='', **kwargs):
    """
    Not a decorator. Function to check sync_info last_updated_at to decide if cache or refresh
    sync_info=self.get_sync('watched', 'show', 'slug').get(slug)
    cache_name='TraktAPI.get_show_progress.response.{slug}'
    """
    sync_info = sync_info or {}

    # Get last modified timestamp from Trakt sync
    last_updated_at = sync_info.get('last_updated_at')

    # Get cached object
    cached_obj = cache.get_cache(cache_name) if last_updated_at else None

    # Return the cached response if show hasn't been modified on Trakt or watched since caching
    if cached_obj and cached_obj.get('response') and cached_obj.get('last_updated_at'):
        if cached_obj['last_updated_at'] == last_updated_at:
            return cached_obj['response']

    # Otherwise get a new response from Trakt and cache it with the timestamp
    # Cache is long (14 days) because we refresh earlier if last_updated_at timestamps change
    response = func(*args, **kwargs)
    if response and last_updated_at:
        cache.set_cache({'response': response, 'last_updated_at': last_updated_at}, cache_name)
    return response


def use_activity_cache(activity_type=None, activity_key=None, cache_days=None):
    """
    Decorator to cache and refresh if last activity changes
    Optionally can pickle instead of cache if necessary (useful for large objects like sync lists)
    Optionally send decorator_cache_refresh=True in func kwargs to force refresh
    """
    def decorator(func):
        def wrapper(self, *args, allow_fallback=False, decorator_cache_refresh=None, **kwargs):
            if not self.authorize():
                return

            # Setup getter/setter cache funcs
            func_get = self._cache.get_cache
            func_set = self._cache.set_cache

            # Set cache_name
            cache_name = f'{func.__name__}.'
            cache_name = f'{self.__class__.__name__}.{cache_name}'
            cache_name = format_name(cache_name, *args, **kwargs)

            # Cached response last_activity timestamp matches last_activity from trakt so no need to refresh
            last_activity = self._get_last_activity(activity_type, activity_key)
            cache_object = func_get(cache_name) if last_activity and not decorator_cache_refresh else None
            if cache_object and cache_object.get('last_activity') == last_activity:
                if cache_object.get('response') and cache_object.get('last_activity'):
                    return cache_object['response']

            # Either not cached or last_activity doesn't match so get a new request and cache it
            response = func(self, *args, **kwargs)
            if not response:
                cache_object = cache_object or func_get(cache_name) if allow_fallback else None
                if allow_fallback:
                    kodi_log([
                        'No response for ', cache_name,
                        '\nAttempting fallback... ', 'Failed!' if not cache_object else 'Success!'], 1)
                return cache_object.get('response') if cache_object else None
            func_set(
                {'response': response, 'last_activity': last_activity},
                cache_name=cache_name, cache_days=cache_days)
            return response
        return wrapper
    return decorator
