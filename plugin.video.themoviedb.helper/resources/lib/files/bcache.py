from resources.lib.addon.plugin import format_name
from resources.lib.files.futils import get_filecache_name
from resources.lib.addon.logger import kodi_log, kodi_try_except

""" Lazyimports
from resources.lib.files.scache import SimpleCache
"""

SEARCH_HISTORY = 'search_history.db'


class BasicCache(object):
    def __init__(self, filename=None, mem_only=False, delay_write=False):
        self._filename = filename
        self._cache = None
        self._mem_only = mem_only
        self._delaywrite = delay_write
        self._id_list = []

    @kodi_try_except('lib.addon.cache ret_cache')
    def ret_cache(self):
        from resources.lib.files.scache import SimpleCache
        if not self._cache:
            self._cache = SimpleCache(filename=self._filename, mem_only=self._mem_only, delay_write=self._delaywrite)
        return self._cache

    @kodi_try_except('lib.addon.cache get_cache')
    def get_cache(self, cache_name):
        self.ret_cache()
        cache_name = get_filecache_name(cache_name or '')
        no_hdd = True if self._id_list and cache_name not in self._id_list else False
        return self._cache.get(cache_name, no_hdd=no_hdd)

    def get_id_list(self):
        self.ret_cache()
        self._id_list = self._cache.get_id_list() or []
        return self._id_list

    @kodi_try_except('lib.addon.cache set_cache')
    def set_cache(self, my_object, cache_name, cache_days=14, force=False, fallback=None):
        """ set object to cache via thread """
        self._set_cache(my_object, cache_name, cache_days, force, fallback)
        return my_object

    def _set_cache(self, my_object, cache_name, cache_days=14, force=False, fallback=None):
        """ set object to cache """
        self.ret_cache()
        cache_name = get_filecache_name(cache_name or '')
        if force and (not my_object or not cache_name or not cache_days):
            my_object = my_object or fallback
            cache_days = force if isinstance(force, int) else cache_days
        self._cache.set(cache_name, my_object, cache_days=cache_days)

    @kodi_try_except('lib.addon.cache del_cache')
    def del_cache(self, cache_name):
        self.ret_cache()
        cache_name = get_filecache_name(cache_name or '')
        self._cache.set(cache_name, None, cache_days=0)

    @kodi_try_except('lib.addon.cache use_cache')
    def use_cache(
            self, func, *args,
            cache_days=14, cache_name='', cache_only=False, cache_force=False, cache_strip=[], cache_fallback=False,
            cache_refresh=False, cache_combine_name=False, headers=None,
            **kwargs):
        """
        Simplecache takes func with args and kwargs
        Returns the cached item if it exists otherwise does the function
        """
        if not cache_name or cache_combine_name:
            cache_name = format_name(cache_name, *args, **kwargs)
            for k, v in cache_strip:
                cache_name = cache_name.replace(k, v)
        my_cache = self.get_cache(cache_name) if not cache_refresh else None
        if my_cache:
            return my_cache
        if not cache_only:
            if headers:
                kwargs['headers'] = headers
            my_object = func(*args, **kwargs)
            return self.set_cache(my_object, cache_name, cache_days, force=cache_force, fallback=cache_fallback)


def use_simple_cache(cache_days=None):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            kwargs['cache_days'] = cache_days or kwargs.get('cache_days', None)
            kwargs['cache_combine_name'] = True
            kwargs['cache_name'] = f'{func.__name__}.'
            kwargs['cache_name'] = f'{self.__class__.__name__}.{kwargs["cache_name"]}'
            return self._cache.use_cache(func, self, *args, **kwargs)
        return wrapper
    return decorator


def get_search_history(tmdb_type=None):
    if not tmdb_type:
        return []
    return BasicCache(SEARCH_HISTORY).get_cache(tmdb_type) or []


def _add_search_history(tmdb_type=None, query=None, max_entries=9, **kwargs):
    search_history = get_search_history(tmdb_type)
    if query in search_history:  # Remove query if in history because we want it to be first in list
        search_history.remove(query)
    if max_entries and len(search_history) > max_entries:
        search_history.pop(0)  # Remove the oldest query if we hit our max so we don't accumulate months worth of queries
    if query:
        search_history.append(query)
    return search_history


def _replace_search_history(tmdb_type=None, query=None, replace=None, **kwargs):
    search_history = get_search_history(tmdb_type)
    if not isinstance(replace, int) and replace in search_history:
        replace = search_history.index(replace)  # If not an int then we need to look-up index of the item to replace
    if not isinstance(replace, int):
        return  # If we can't find an index don't update the cache so we don't cause unintended modification
    try:  # Use a try block to catch index out of range errors or other issues with updating history
        if query:
            search_history[replace] = query
        else:
            search_history.pop(replace)
    except Exception as exc:
        kodi_log(exc, 1)
        return
    return search_history


def set_search_history(tmdb_type=None, query=None, cache_days=120, clear_cache=False, max_entries=9, replace=False):
    if not tmdb_type:
        return
    _cache = BasicCache(SEARCH_HISTORY)
    if not clear_cache:
        func = _add_search_history if replace is False else _replace_search_history
        search_history = func(tmdb_type=tmdb_type, query=query, max_entries=max_entries, replace=replace)
        _cache.set_cache(search_history, cache_name=tmdb_type, cache_days=cache_days, force=True)
    return _cache.set_cache(None, tmdb_type, 0, force=True) if clear_cache else query
