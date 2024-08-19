# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

def map_kwargs(mapping={}):
    """ Decorator to remap kwargs key names """
    def decorator(func):
        def wrapper(*args, **kwargs):
            for k, v in mapping.items():
                if k in kwargs:
                    kwargs[v] = kwargs.pop(k, None)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def is_in_kwargs(mapping={}):
    """ Decorator to check that kwargs values match allowlist before running
    Accepts a dictionary of {kwarg: [allowlist]} key value pairs
    Decorated method is not run if kwargs.get(kwarg) not in [allowlist]
    Optionally can use {kwarg: True} to check kwarg exists and has any value
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            for k, v in mapping.items():
                if v is True:
                    if kwargs.get(k) is None:
                        return
                else:
                    if kwargs.get(k) not in v:
                        return
            return func(*args, **kwargs)
        return wrapper
    return decorator


def get_tmdb_id(func):
    """ Decorator to get tmdb_id if not in kwargs """
    def wrapper(*args, **kwargs):
        from tmdbhelper.lib.addon.dialog import BusyDialog
        from tmdbhelper.lib.api.tmdb.api import TMDb
        with BusyDialog():
            if not kwargs.get('tmdb_id'):
                kwargs['tmdb_id'] = TMDb().get_tmdb_id(**kwargs)
                if not kwargs['tmdb_id']:
                    return
        return func(*args, **kwargs)
    return wrapper


def choose_tmdb_id(func):
    """ Decorator to get tmdb_id if not in kwargs """
    def wrapper(*args, **kwargs):
        if kwargs.get('tmdb_id'):
            return func(*args, **kwargs)

        from xbmcgui import Dialog, ListItem
        from tmdbhelper.lib.addon.dialog import BusyDialog
        from tmdbhelper.lib.api.tmdb.api import TMDb
        from tmdbhelper.lib.api.tmdb.mapping import get_imagepath_poster

        if kwargs.get('query'):
            with BusyDialog():
                response = TMDb().get_request_sc('search', kwargs['tmdb_type'], query=kwargs['query'])
            if not response or not response.get('results'):
                return

            items = []
            for i in response['results']:
                li = ListItem(
                    i.get('title') or i.get('name'),
                    i.get('release_date') or i.get('first_air_date'))
                li.setArt({'icon': get_imagepath_poster(i.get('poster_path'))})
                items.append(li)

            x = Dialog().select(kwargs['query'], items, useDetails=True)
            if x == -1:
                return
            kwargs['tmdb_id'] = response['results'][x].get('id')

        else:
            with BusyDialog():
                kwargs['tmdb_id'] = TMDb().get_tmdb_id(**kwargs)

        if not kwargs['tmdb_id']:
            return

        return func(*args, **kwargs)
    return wrapper
