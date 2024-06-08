from tmdbhelper.lib.addon.plugin import format_name


def is_authorized(func):

    def wrapper(self, *args, **kwargs):

        def _get_request_data():
            # Authorization not required for this method
            if not kwargs.get('authorize', True):
                return func(self, *args, **kwargs)
            # Authorization already granted in this instance
            if self.authorization:
                return func(self, *args, **kwargs)
            # Authorization required ask for login if no token
            if not self.attempted_login and self.authorize(login=True):
                return func(self, *args, **kwargs)

        def _get_cached_data():
            params = {}
            params.update(kwargs)
            params['cache_only'] = True
            try:
                return func(self, *args, **params)
            except TypeError:
                return

        return _get_request_data() or _get_cached_data()

    return wrapper


def use_lastupdated_cache(cache, func, *args, sync_info=None, cache_name='', **kwargs):
    """
    Not a decorator. Function to check sync_info last_updated_at to decide if cache or refresh
    sync_info=self.get_sync('watched', 'show', 'slug', extended='full').get(slug)
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
    Optionally send decorator_cache_refresh=True in func kwargs to force refresh as long as authorized
    If not authorized the decoractor will only return cached object
    """
    def decorator(func):

        def wrapper(self, *args, allow_fallback=False, decorator_cache_refresh=None, **kwargs):
            # Setup getter/setter cache funcs
            func_get = self._cache.get_cache
            func_set = self._cache.set_cache

            # Set cache_name
            cache_name = f'{func.__name__}.'
            cache_name = f'{self.__class__.__name__}.{cache_name}'
            cache_name = format_name(cache_name, *args, **kwargs)

            # Check last activity from Trakt
            last_activity = self.get_last_activity(activity_type, activity_key)

            # Get our cached object
            response = None
            cache_object = None
            if last_activity == -1:  # Cache only mode
                cache_object = func_get(cache_name)
                if cache_object:
                    response = cache_object.get('response')
                return response
            if last_activity and not decorator_cache_refresh:
                cache_object = func_get(cache_name)

            # Check that cached object matches last_activity
            if cache_object and cache_object.get('response'):
                if cache_object.get('last_activity') >= last_activity:
                    response = cache_object['response']
                    return response

            def _get_fallback():
                _cache_object = cache_object
                if allow_fallback and not _cache_object:
                    _cache_object = func_get(cache_name)
                if _cache_object:
                    return _cache_object.get('response')

            # Either not cached or last_activity doesn't match so get a new request and cache it
            response = func(self, *args, **kwargs)

            # If we dont have a response then get fallback from cache
            if not response:
                response = _get_fallback()
                return response

            func_set(
                {'response': response, 'last_activity': last_activity},
                cache_name=cache_name, cache_days=cache_days)

            return response

        return wrapper
    return decorator
