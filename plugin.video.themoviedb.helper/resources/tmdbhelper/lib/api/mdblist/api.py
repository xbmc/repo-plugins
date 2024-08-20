from jurialmunkey.parser import get_params
from tmdbhelper.lib.addon.plugin import ADDONPATH, PLUGINPATH, convert_trakt_type, convert_type, get_localized, get_setting
from tmdbhelper.lib.api.request import RequestAPI
from tmdbhelper.lib.api.api_keys.mdblist import API_KEY

PARAMS_DEF = {
    'episode': {
        'info': 'details', 'tmdb_type': 'tv', 'tmdb_id': '{tmdb_id}',
        'season': '{season}', 'episode': '{episode}'
    },
    'season': {
        'info': 'episodes', 'tmdb_type': 'tv', 'tmdb_id': '{tmdb_id}',
        'season': '{season}'
    }
}


def _get_paginated(items, limit=None, page=1):
    items = items or []
    if limit is None:
        return (items, None)
    from tmdbhelper.lib.items.pages import PaginatedItems
    paginated_items = PaginatedItems(items, page=page, limit=limit)
    return (paginated_items.items, paginated_items.next_page)


def _map_list(response):
    items = []
    items_append = items.append
    for i in response:
        item = {}
        item['label'] = i.get('name')
        item['infolabels'] = {'plot': i.get('description'), 'studio': [i.get('user_name')]}
        item['art'] = {'icon': f'{ADDONPATH}/resources/icons/mdblist/mdblist.png'}
        item['params'] = {
            'info': 'mdblist_userlist',
            'list_name': i.get('name'),
            'list_id': i.get('id'),
            'plugin_category': i.get('name')}
        item['unique_ids'] = {
            'mdblist': i.get('id'),
            'slug': i.get('slug'),
            'user': i.get('user_id')}
        # TODO: ContextMenu: Add to library
        items_append(item)
    return items


def _get_item_unique_ids(item, item_type=None, unique_ids=None):
    unique_ids = unique_ids or {}
    unique_ids['tmdb'] = item.get('id')
    unique_ids['imdb'] = item.get('imdb_id')
    if item_type in ('season', 'episode'):
        unique_ids['tvshow.tmdb'] = item.get('id')
    return unique_ids


def _get_item_infolabels(item, item_type=None, infolabels=None):
    infolabels = infolabels or {}
    infolabels['title'] = item.get('title')
    infolabels['year'] = item.get('release_year')
    infolabels['mediatype'] = convert_type(convert_trakt_type(item_type), 'dbtype')
    if item_type in ('season', 'episode'):
        infolabels['season'] = item.get('season')
    if item_type == 'episode':
        infolabels['episode'] = item.get('episode')
    return infolabels


def _get_item_info(item, item_type=None, params_def=None):
    base_item = {}
    base_item['label'] = item.get('title') or ''
    base_item['unique_ids'] = _get_item_unique_ids(item, item_type=item_type)
    base_item['infolabels'] = _get_item_infolabels(item, item_type=item_type)
    base_item['params'] = get_params(item, convert_trakt_type(item_type), definition=params_def)
    base_item['path'] = PLUGINPATH
    return base_item


def _get_configured(items, permitted_types=None):
    configured = {'items': []}
    configured_items_append = configured['items'].append

    for i in items:
        i_type = i.get('mediatype', None)

        if permitted_types and i_type not in permitted_types:
            continue

        item = _get_item_info(i, item_type=i_type, params_def=PARAMS_DEF.get(i_type))

        if not item:
            continue

        # Also add item to a list only containing that item type
        # Useful if we need to only get one type of item from a mixed list (e.g. only "movies")
        configured.setdefault(f'{i_type}s', []).append(item)
        configured_items_append(item)

    return configured


class MDbList(RequestAPI):

    api_key = API_KEY

    def __init__(self, api_key=None, page_length=1):
        api_key = api_key or self.api_key

        super(MDbList, self).__init__(
            req_api_key=f'apikey={api_key}',
            req_api_name='MDbList',
            req_api_url='https://mdblist.com/api')
        MDbList.api_key = api_key

        self.item_limit = 20 * max(get_setting('pagemulti_trakt', 'int'), page_length)

    def _get_request(self, func, *args, **kwargs):
        response = func(*args, **kwargs)
        if isinstance(response, dict):  # API returns dict rather than list on failure
            if not kwargs.get('cache_refresh') and response.get('error') == 'Invalid API key!' and self.api_key:
                kwargs['cache_refresh'] = True  # Refresh in case cached because we've got an api key
                response = func(*args, **kwargs)
                if not isinstance(response, dict):  # Check again in case now working and return response
                    return response
            from tmdbhelper.lib.addon.logger import kodi_log
            kodi_log(f'MDBList Error: {response.get("error")}', 1)
            from xbmcgui import Dialog
            Dialog().ok(get_localized(257), f'{response.get("error")}')
            return []
        return response

    def _get_request_sc(self, *args, **kwargs):
        return self._get_request(self.get_request_sc, *args, **kwargs)

    def get_details(self, media_type, imdb_id=None, trakt_id=None, tmdb_id=None, tvdb_id=None, title=None, year=None):
        params = {
            'i': imdb_id, 't': trakt_id, 'tm': tmdb_id, 'tv': tvdb_id,
            'm': media_type, 's': title, 'y': year
        }
        params = {k: v for k, v in params.items() if v}
        return self.get_request_sc(**params)

    def get_ratings(self, media_type, imdb_id=None, trakt_id=None, tmdb_id=None, tvdb_id=None, title=None, year=None):
        infoproperties = {}

        details = self.get_details(media_type, imdb_id, trakt_id, tmdb_id, tvdb_id, title, year)

        try:
            infoproperties['mdblist_rating'] = details['score']
            ratings = details['ratings']
        except (KeyError, TypeError):
            return infoproperties

        translation = {
            'tomatoes': 'rottentomatoes_rating',
            'tomatoesaudience': 'rottentomatoes_usermeter'}
        for i in ratings:
            try:
                name = i['source']
            except KeyError:
                continue
            if i.get('value'):
                infoproperties[translation.get(name) or f'{name}_rating'] = i['value']
            if i.get('votes'):
                infoproperties[f'{name}_votes'] = i['votes']

        return infoproperties

    def get_list_of_lists(self, path, page=1, limit: int = None):
        response = self._get_request_sc(path, cache_refresh=True if page == 1 else False)
        response, next_page = _get_paginated(response, limit=limit or 250, page=page)
        items = _map_list(response)
        return items if not next_page else items + next_page

    def get_custom_list(self, list_id, page=1, limit: int = None):
        path = f'lists/{list_id}/items'
        response = self._get_request_sc(path, cache_refresh=True if page == 1 else False)
        return self.get_custom_list_paginated(response, page, limit)

    def get_custom_list_paginated(self, response, page=1, limit: int = None):
        response, next_page = _get_paginated(response, limit=limit or self.item_limit, page=page)
        items = _get_configured(response, permitted_types=['movie', 'show', 'season', 'episode'])
        return {
            'items': items['items'],
            'movies': items.get('movies', []),
            'shows': items.get('shows', []),
            'seasons': items.get('seasons', []),
            'episodes': items.get('episodes', []),
            'next_page': next_page}
