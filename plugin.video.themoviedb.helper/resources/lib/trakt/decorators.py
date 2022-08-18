from resources.lib.files.utils import set_pickle, get_pickle
from resources.lib.addon.plugin import format_name, kodi_log


def is_authorized(func):
    def wrapper(self, *args, **kwargs):
        if kwargs.get('authorize', True) and not self.authorize():
            return
        return func(self, *args, **kwargs)
    return wrapper


def use_lastupdated_cache(cache, func, *args, **kwargs):
    """
    Not a decorator. Function to check sync_info last_updated_at to decide if cache or refresh
    sync_info=self.get_sync('watched', 'show', 'slug').get(slug)
    cache_name='TraktAPI.get_show_progress.response.{}'.format(slug)
    """
    sync_info = kwargs.pop('sync_info', None) or {}
    cache_name = kwargs.pop('cache_name', None) or ''

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


def use_activity_cache(activity_type=None, activity_key=None, cache_days=None, pickle_object=False, allow_fallback=False):
    """
    Decorator to cache and refresh if last activity changes
    Optionally can pickle instead of cache if necessary (useful for large objects like sync lists)
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if not self.authorize():
                return

            # Setup getter/setter cache funcs
            func_get = get_pickle if pickle_object else self._cache.get_cache
            func_set = set_pickle if pickle_object else self._cache.set_cache

            # Set cache_name
            cache_name = u'{}.'.format(func.__name__)
            cache_name = u'{}.{}'.format(self.__class__.__name__, cache_name)
            cache_name = format_name(cache_name, *args, **kwargs)

            # Cached response last_activity timestamp matches last_activity from trakt so no need to refresh
            last_activity = self._get_last_activity(activity_type, activity_key)
            cache_object = func_get(cache_name) if last_activity else None
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
