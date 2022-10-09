from resources.lib.addon.modimp import importmodule
from resources.lib.addon.consts import (
    ROUTE_NOID,
    TMDB_BASIC_LISTS,
    TRAKT_SYNC_LISTS,
    TRAKT_BASIC_LISTS,
    ROUTE_TMDBID,
    TRAKT_LIST_OF_LISTS,
    MDBLIST_LIST_OF_LISTS,
    RANDOMISED_LISTS,
    RANDOMISED_TRAKT
)


def get_container(info):
    route = None
    routes = ROUTE_NOID
    routes.update(TRAKT_LIST_OF_LISTS)
    routes.update(MDBLIST_LIST_OF_LISTS)
    routes.update(RANDOMISED_LISTS)
    routes.update(RANDOMISED_TRAKT)
    try:
        route = routes[info]['route']
    except KeyError:
        routes = ROUTE_TMDBID
        routes.update(TMDB_BASIC_LISTS)
        routes.update(TRAKT_BASIC_LISTS)
        routes.update(TRAKT_SYNC_LISTS)
    try:
        route = route or routes[info]['route']
        return importmodule(**route)
    except KeyError:
        if info and info[:4] != 'dir_':
            raise
        return importmodule(module_name='resources.lib.items.basedir', import_attr='ListBaseDir')
