from tmdbhelper.lib.files.bcache import use_simple_cache
from tmdbhelper.lib.addon.consts import CACHE_SHORT
from tmdbhelper.lib.api.trakt.decorators import is_authorized


@use_simple_cache(cache_days=CACHE_SHORT)
def get_simple_list(self, *args, trakt_type=None, **kwargs):
    response = self.get_response(*args, **kwargs)
    if not response:
        return
    from tmdbhelper.lib.api.trakt.items import TraktItems
    return TraktItems(response.json(), headers=response.headers, trakt_type=trakt_type).configure_items()


@use_simple_cache(cache_days=CACHE_SHORT)
def get_sorted_list(
        self, path, sort_by=None, sort_how=None, extended=None, trakt_type=None, permitted_types=None, cache_refresh=False, cache_only=False,
        genres=None, years=None, query=None, languages=None, countries=None, runtimes=None, studio_ids=None
):
    response = self.get_response(
        path, extended=extended, limit=4095, cache_only=cache_only,
        genres=genres, years=years, query=query, languages=languages, countries=countries, runtimes=runtimes, studio_ids=studio_ids
    )

    if not response:
        return

    def _get_sorted_list_items():
        if extended == 'sync':
            return self.merge_sync_sort(response.json())
        if extended == 'inprogress':
            return self.filter_inprogress(self.merge_sync_sort(response.json()))
        return response.json()

    items = _get_sorted_list_items()

    from tmdbhelper.lib.api.trakt.items import TraktItems
    return TraktItems(items, headers=response.headers).build_items(
        sort_by=sort_by or response.headers.get('x-sort-by'),
        sort_how=sort_how or response.headers.get('x-sort-how'),
        permitted_types=permitted_types)


@is_authorized
def get_mixed_list(
        self, path, trakt_types: list, limit: int = None, extended: str = None, authorize=False, cache_only=False,
        genres=None, years=None, query=None, languages=None, countries=None, runtimes=None, studio_ids=None
):
    """ Returns a randomised simple list which combines movies and shows
    path uses {trakt_type} as format substitution for trakt_type in trakt_types
    """
    items = []
    limit = limit or self.item_limit

    for trakt_type in trakt_types:
        response = self.get_simple_list(
            path.format(trakt_type=trakt_type),
            extended=extended, page=1, limit=limit * 2, trakt_type=trakt_type, cache_only=cache_only,
            genres=genres, years=years, query=query, languages=languages, countries=countries, runtimes=runtimes, studio_ids=studio_ids
        ) or {}
        items += response.get('items') or []

    if not items:
        return

    if len(items) <= limit:
        return items

    import random
    return random.sample(items, limit)


@is_authorized
def get_basic_list(
        self, path, trakt_type, page: int = 1, limit: int = None, params=None,
        sort_by=None, sort_how=None, extended=None, authorize=False, cache_only=False, randomise=False, always_refresh=True,
        genres=None, years=None, query=None, languages=None, countries=None, runtimes=None, studio_ids=None
):

    from jurialmunkey.parser import try_int
    cache_refresh = True if always_refresh and try_int(page, fallback=1) == 1 else False
    limit = limit or self.item_limit

    if randomise:
        response = self.get_simple_list(
            path, extended=extended, page=1, limit=limit * 2, trakt_type=trakt_type, cache_only=cache_only,
            genres=genres, years=years, query=query, languages=languages, countries=countries, runtimes=runtimes, studio_ids=studio_ids
        )

    elif sort_by is not None:  # Sorted list manually paginated because need to sort first
        from tmdbhelper.lib.items.pages import PaginatedItems
        response = self.get_sorted_list(
            path, sort_by, sort_how, extended, cache_refresh=cache_refresh, cache_only=cache_only,
            genres=genres, years=years, query=query, languages=languages, countries=countries, runtimes=runtimes, studio_ids=studio_ids
        )
        response = PaginatedItems(items=response['items'], page=page, limit=limit).get_dict()

    else:  # Unsorted lists can be paginated by the API
        response = self.get_simple_list(
            path, extended=extended, page=page, limit=limit, trakt_type=trakt_type, cache_only=cache_only,
            genres=genres, years=years, query=query, languages=languages, countries=countries, runtimes=runtimes, studio_ids=studio_ids
        )

    if not response:
        return

    if randomise and len(response['items']) > limit:
        import random
        return random.sample(response['items'], limit)

    from tmdbhelper.lib.items.pages import get_next_page
    return response['items'] + get_next_page(response['headers'])


@is_authorized
def get_stacked_list(
        self, path, trakt_type, page: int = 1, limit: int = None, params=None, sort_by=None, sort_how=None,
        extended=None, authorize=False, always_refresh=True, cache_only=False,
        genres=None, years=None, query=None, languages=None, countries=None, runtimes=None, studio_ids=None,
        **kwargs
):
    """ Get Basic list but stack repeat TV Shows """
    from jurialmunkey.parser import try_int
    limit = limit or self.item_limit
    cache_refresh = True if always_refresh and try_int(page, fallback=1) == 1 else False

    response = self.get_simple_list(
        path, extended=extended, limit=4095, trakt_type=trakt_type, cache_refresh=cache_refresh, cache_only=cache_only,
        genres=genres, years=years, query=query, languages=languages, countries=countries, runtimes=runtimes, studio_ids=studio_ids
    )

    if not response:
        return

    from tmdbhelper.lib.items.pages import PaginatedItems
    response['items'] = self.stack_calendar_tvshows(response['items'])
    response = PaginatedItems(items=response['items'], page=page, limit=limit).get_dict()

    if not response:
        return

    from tmdbhelper.lib.items.pages import get_next_page
    return response['items'] + get_next_page(response['headers'])


@is_authorized
def get_custom_list(
        self, list_slug, user_slug=None, page: int = 1, limit: int = None, params=None, authorize=False,
        sort_by=None, sort_how=None, extended=None, owner=False, always_refresh=True, cache_only=False
):

    limit = limit or self.item_limit

    if user_slug == 'official':
        path = f'lists/{list_slug}/items'
    else:
        path = f'users/{user_slug or "me"}/lists/{list_slug}/items'

    # Refresh cache on first page for user list because it might've changed
    from jurialmunkey.parser import try_int
    cache_refresh = True if always_refresh and try_int(page, fallback=1) == 1 else False

    sorted_items = self.get_sorted_list(
        path, sort_by, sort_how, extended,
        permitted_types=['movie', 'show', 'person', 'episode'],
        cache_refresh=cache_refresh, cache_only=cache_only
    ) or {}

    from tmdbhelper.lib.items.pages import PaginatedItems
    paginated_items = PaginatedItems(
        items=sorted_items.get('items', []), page=page, limit=limit)

    return {
        'items': paginated_items.items,
        'movies': sorted_items.get('movies', []),
        'shows': sorted_items.get('shows', []),
        'persons': sorted_items.get('persons', []),
        'next_page': paginated_items.next_page}


def get_list_of_genres(self, trakt_type):
    if trakt_type not in ['movie', 'show']:
        return

    response = self.get_response(f'genres/{trakt_type}s')

    if not response:
        return

    from tmdbhelper.lib.addon.plugin import get_setting, ADDONPATH

    items = []

    for i in response.json():
        item = {}
        item['label'] = i.get('name')
        item['infolabels'] = {}
        item['infoproperties'] = {}
        item['art'] = {
            'icon': f'{ADDONPATH}/resources/icons/trakt/genres.png'
        }
        item['params'] = {
            'info': 'dir_trakt_genre',
            'genre': i.get('slug'),
            'tmdb_type': 'movie' if trakt_type == 'movie' else 'tv'
        }
        item['unique_ids'] = {'slug': i.get('slug')}
        items.append(item)

    def _add_icon(i):
        import xbmcvfs
        slug = i['unique_ids']['slug']
        if not slug:
            return i
        filepath = xbmcvfs.validatePath(xbmcvfs.translatePath(f'{icon_path}/{slug}.png'))
        if not xbmcvfs.exists(filepath):
            return i
        i['art']['icon'] = filepath
        return i

    icon_path = get_setting('trakt_genre_icon_location', 'str')

    if icon_path:
        items = [_add_icon(i) for i in items]

    return items


@is_authorized
def get_list_of_lists(self, path, page: int = 1, limit: int = 250, authorize=False, next_page=True, sort_likes=False, **kwargs):
    response = self.get_response(path, page=page, limit=limit)
    if not response:
        return
    items = []
    from tmdbhelper.lib.addon.plugin import get_localized
    sorted_list = sorted(response.json(), key=lambda i: i.get('likes', 0) or i.get('list', {}).get('likes', 0), reverse=True) if sort_likes else response.json()
    for i in sorted_list:
        if i.get('list') and i['list'].get('name'):
            i = i['list']
        elif not i.get('name'):
            continue

        i_name = i.get('name')
        i_usr = i.get('user') or {}
        i_ids = i.get('ids') or {}
        i_usr_ids = i_usr.get('ids') or {}
        i_usr_slug = 'official' if i.get('type') == 'official' else i_usr_ids.get('slug')
        i_lst_slug = i_ids.get('slug')
        i_lst_trakt = i_ids.get('trakt')

        item = {}
        item['label'] = f"{i.get('name')}"
        item['infolabels'] = {'plot': i.get('description'), 'studio': [i_usr.get('name') or i_usr_ids.get('slug')]}
        item['infoproperties'] = {k: v for k, v in i.items() if v and type(v) not in [list, dict]}
        item['art'] = {}
        item['params'] = {
            'info': 'trakt_userlist',
            'list_name': i_name,
            'list_slug': i_lst_slug,
            'user_slug': i_usr_slug,
            'plugin_category': i_name}
        item['unique_ids'] = {
            'trakt': i_lst_trakt,
            'slug': i_lst_slug,
            'user': i_usr_slug}
        item['infoproperties']['is_sortable'] = 'True'

        # Add sort methods
        item['context_menu'] = [(
            get_localized(32309),
            u'Runscript(plugin.video.themoviedb.helper,sort_list,{})'.format(
                u','.join(f'{k}={v}' for k, v in item['params'].items())))]

        # Add library context menu
        item['context_menu'] += [(
            get_localized(20444), u'Runscript(plugin.video.themoviedb.helper,{})'.format(
                u'user_list={list_slug},user_slug={user_slug}'.format(**item['params'])))]

        # Unlike list context menu
        if path.startswith('users/likes'):
            item['context_menu'] += [(
                get_localized(32319), u'Runscript(plugin.video.themoviedb.helper,{},delete)'.format(
                    u'like_list={list_slug},user_slug={user_slug}'.format(**item['params'])))]

        # Like list context menu
        elif path.startswith(('lists/', 'search/')):
            item['context_menu'] += [(
                get_localized(32315), u'Runscript(plugin.video.themoviedb.helper,{})'.format(
                    u'like_list={list_slug},user_slug={user_slug}'.format(**item['params'])))]

        # Owner of list so set param to allow deleting later
        else:
            item['params']['owner'] = 'true'
            item['context_menu'] += [(
                get_localized(118), u'Runscript(plugin.video.themoviedb.helper,{})'.format(
                    u'rename_list={list_slug}'.format(**item['params'])))]
            item['context_menu'] += [(
                get_localized(117), u'Runscript(plugin.video.themoviedb.helper,{})'.format(
                    u'delete_list={list_slug}'.format(**item['params'])))]

        items.append(item)
    if not next_page:
        return items
    from tmdbhelper.lib.items.pages import get_next_page
    return items + get_next_page(response.headers)


def get_sync_list(
    self, sync_type, trakt_type, page: int = 1, limit: int = None, params=None, sort_by=None, sort_how=None, next_page=True,
    always_refresh=True, extended=None, filters=None
):
    from tmdbhelper.lib.api.trakt.items import TraktItems
    limit = limit or self.sync_item_limit
    sync = self.get_sync(sync_type, trakt_type, extended=extended)
    func = TraktItems(items=sync, trakt_type=trakt_type).build_items
    response = func(sort_by, sort_how, filters=filters)
    if not response:
        return
    from tmdbhelper.lib.items.pages import PaginatedItems
    response = PaginatedItems(items=response['items'], page=page, limit=limit)
    return response.items if not next_page else response.items + response.next_page


def merge_sync_sort(self, items):
    """ Get sync dict sorted by slugs then merge slug into list """
    sync = {}
    sync.update(self.get_sync('watched', 'show', 'slug', extended='full'))
    sync.update(self.get_sync('watched', 'movie', 'slug'))
    return [dict(i, **sync.get(i.get(i.get('type'), {}).get('ids', {}).get('slug'), {})) for i in items]


def filter_inprogress(self, items):
    """ Filter list so that it only returns inprogress shows """
    inprogress = self.get_inprogress_shows() or []
    inprogress = [i['show']['ids']['slug'] for i in inprogress if i.get('show', {}).get('ids', {}).get('slug')]
    if not inprogress:
        return
    items = [i for i in items if i.get('show', {}).get('ids', {}).get('slug') in inprogress]
    return items


@use_simple_cache(cache_days=CACHE_SHORT)
def get_imdb_top250(self, id_type=None, trakt_type='movie'):
    paths = {
        'movie': 'users/justin/lists/imdb-top-rated-movies/items',
        'show': 'users/justin/lists/imdb-top-rated-tv-shows/items'}
    try:
        response = self.get_response(paths[trakt_type], limit=4095)
        from tmdbhelper.lib.api.trakt.items import TraktItems
        sorted_items = TraktItems(response.json() if response else []).sort_items('rank', 'asc') or []
        return [i[trakt_type]['ids'][id_type] for i in sorted_items]
    except KeyError:
        return []
