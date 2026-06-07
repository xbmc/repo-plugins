from xbmcgui import Dialog
from resources.lib.addon.plugin import get_setting, ADDONPATH, PLUGINPATH, convert_trakt_type, convert_type, get_localized
from resources.lib.addon.parser import get_params
from resources.lib.api.request import RequestAPI
from resources.lib.items.pages import PaginatedItems
from resources.lib.addon.logger import kodi_log


def _get_paginated(items, limit=None, page=1):
    items = items or []
    if limit is None:
        return (items, None)
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


def _get_item_infolabels(item, item_type=None, infolabels=None):
    infolabels = infolabels or {}
    infolabels['title'] = item.get('title')
    infolabels['year'] = item.get('release_year')
    infolabels['mediatype'] = convert_type(convert_trakt_type(item_type), 'dbtype')
    return infolabels


def _get_item_info(item, item_type=None, params_def=None):
    base_item = {}
    base_item['label'] = item.get('title') or ''
    base_item['unique_ids'] = {'tmdb': item.get('id'), 'imdb': item.get('imdb_id')}
    base_item['infolabels'] = _get_item_infolabels(item, item_type=item_type)
    base_item['params'] = get_params(item, convert_trakt_type(item_type), definition=params_def)
    base_item['path'] = PLUGINPATH
    return base_item


def _get_configured(items, permitted_types=None, params_def=None):
    configured = {'items': []}
    configured_items_append = configured['items'].append
    for i in items:
        i_type = i.get('mediatype', None)
        if permitted_types and i_type not in permitted_types:
            continue
        item = _get_item_info(i, item_type=i_type, params_def=params_def)
        if not item:
            continue
        # Also add item to a list only containing that item type
        # Useful if we need to only get one type of item from a mixed list (e.g. only "movies")
        configured.setdefault(f'{i_type}s', []).append(item)
        configured_items_append(item)
    return configured


class MDbList(RequestAPI):
    def __init__(self, api_key=None, delay_write=False):
        super(MDbList, self).__init__(
            req_api_key=f'apikey={api_key or get_setting("mdblist_apikey", "str")}',
            req_api_name='MDbList',
            req_api_url='https://mdblist.com/api',
            delay_write=delay_write)

    def _get_request(self, func, *args, **kwargs):
        response = func(*args, **kwargs)
        if isinstance(response, dict):  # API returns dict rather than list on failure
            if not kwargs.get('cache_refresh') and response.get('error') == 'Invalid API key!' and get_setting("mdblist_apikey", "str"):
                kwargs['cache_refresh'] = True  # Refresh in case cached because we've got an api key
                response = func(*args, **kwargs)
                if not isinstance(response, dict):  # Check again in case now working and return response
                    return response
            kodi_log(f'MDBList Error: {response.get("error")}', 1)
            Dialog().ok(get_localized(257), f'{response.get("error")}')
            return []
        return response

    def _get_request_sc(self, *args, **kwargs):
        return self._get_request(self.get_request_sc, *args, **kwargs)

    def get_list_of_lists(self, path, limit=None, page=1):
        response = self._get_request_sc(path, cache_refresh=True if page == 1 else False)
        response, next_page = _get_paginated(response, limit=limit, page=page)
        items = _map_list(response)
        return items if not next_page else items + next_page

    def get_custom_list(self, list_id, page=1, limit=20):
        path = f'lists/{list_id}/items'
        response = self._get_request_sc(path, cache_refresh=True if page == 1 else False)
        response, next_page = _get_paginated(response, limit=limit, page=page)
        items = _get_configured(response, permitted_types=['movie', 'show'])
        return {
            'items': items['items'],
            'movies': items.get('movies', []),
            'shows': items.get('shows', []),
            'next_page': next_page}
