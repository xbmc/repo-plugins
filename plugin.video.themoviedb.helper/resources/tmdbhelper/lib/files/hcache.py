from tmdbhelper.lib.files.bcache import BasicCache
from tmdbhelper.lib.addon.logger import kodi_log


SEARCH_HISTORY = 'search_history.db'


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
