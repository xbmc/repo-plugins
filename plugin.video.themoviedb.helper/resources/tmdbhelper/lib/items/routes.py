from jurialmunkey.modimp import importmodule
from tmdbhelper.lib.addon.consts import (
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

ALL_ROUTES = [
    ROUTE_NOID, TRAKT_LIST_OF_LISTS, MDBLIST_LIST_OF_LISTS, RANDOMISED_LISTS, RANDOMISED_TRAKT,
    ROUTE_TMDBID, TMDB_BASIC_LISTS, TRAKT_BASIC_LISTS, TRAKT_SYNC_LISTS
]


def get_container(info):
    route = None

    for routes in ALL_ROUTES:
        try:
            route = routes[info]['route']
            return importmodule(**route)
        except KeyError:
            continue

    if info and info[:4] != 'dir_':
        raise Exception(f'info={info} is not valid route')
    return importmodule(module_name='tmdbhelper.lib.items.basedir', import_attr='ListBaseDir')
