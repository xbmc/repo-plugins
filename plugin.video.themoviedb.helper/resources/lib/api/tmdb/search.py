from xbmcgui import Dialog, INPUT_ALPHANUM
from resources.lib.addon.plugin import ADDONPATH, PLUGINPATH, convert_type, get_localized
from resources.lib.addon.parser import merge_two_dicts
from resources.lib.files.bcache import set_search_history, get_search_history
from resources.lib.items.container import Container
from urllib.parse import urlencode


MULTISEARCH_TYPES = ['movie', 'tv', 'person', 'collection', 'company', 'keyword']


def get_zippered_list(lists):
    max_len = 0
    for i in lists:
        max_len = max(max_len, len(i))
    return [i[x] for x in range(max_len) for i in lists if x < len(i)]


def get_searchdir(tmdb_type, clear_cache_item=True, append_type=False, **kwargs):  # list_searchdir
    base_item = {
        'label': f'{get_localized(137)} {convert_type(tmdb_type, "plural")}',
        'art': {'thumb': f'{ADDONPATH}/resources/icons/themoviedb/search.png'},
        'infoproperties': {'specialsort': 'top'},
        'params': merge_two_dicts(kwargs, {'info': 'search', 'tmdb_type': tmdb_type})}
    items = []
    items.append(base_item)

    history = get_search_history(tmdb_type)
    history.reverse()
    for i in history:
        item = {
            'label': f'{i} ({tmdb_type})' if append_type else i,
            'art': base_item.get('art'),
            'params': merge_two_dicts(base_item.get('params', {}), {'query': i})}
        items.append(item)
    if history and clear_cache_item:
        item = {
            'label': get_localized(32121),
            'art': base_item.get('art'),
            'infoproperties': {'specialsort': 'bottom'},
            'params': merge_two_dicts(base_item.get('params', {}), {'info': 'dir_search', 'clear_cache': 'True'})}
        items.append(item)
    return items


class ListSearchDir(Container):
    def get_items(self, tmdb_type, **kwargs):  # list_searchdir_router
        self.plugin_category = get_localized(137)
        if kwargs.get('clear_cache') != 'True':
            return get_searchdir(tmdb_type, **kwargs)
        set_search_history(tmdb_type, clear_cache=True)
        self.container_refresh = True


class ListMultiSearchDir(Container):
    def get_items(self, **kwargs):  # list_multisearchdir_router
        def _get_multisearchdir():
            lists = [get_searchdir(i, clear_cache_item=False, append_type=True) for i in MULTISEARCH_TYPES]
            items = get_zippered_list(lists)
            if len(items) > len(MULTISEARCH_TYPES):  # We have search results so need clear cache item
                items.append({
                    'label': get_localized(32121),
                    'art': {'thumb': f'{ADDONPATH}/resources/icons/themoviedb/search.png'},
                    'infoproperties': {'specialsort': 'bottom'},
                    'params': {'info': 'dir_multisearch', 'clear_cache': 'True'}})
            return items
        self.plugin_category = get_localized(137)
        if kwargs.get('clear_cache') != 'True':
            return _get_multisearchdir()
        for tmdb_type in MULTISEARCH_TYPES:
            set_search_history(tmdb_type, clear_cache=True)
        self.container_refresh = True


class ListSearch(Container):
    def get_items(self, tmdb_type, query=None, update_listing=False, page=None, **kwargs):
        original_query = query

        if not query:
            query = set_search_history(
                query=Dialog().input(get_localized(32044), type=INPUT_ALPHANUM),
                tmdb_type=tmdb_type)
            if not query:
                return
        elif kwargs.get('history', '').lower() == 'true':  # Force saving history
            set_search_history(query=query, tmdb_type=tmdb_type)

        items = self.tmdb_api.get_search_list(
            tmdb_type=tmdb_type, query=query, page=page,
            year=kwargs.get('year'),
            first_air_date_year=kwargs.get('first_air_date_year'),
            primary_release_year=kwargs.get('primary_release_year'))

        if not original_query:
            params = merge_two_dicts(kwargs, {
                'info': 'search', 'tmdb_type': tmdb_type, 'page': page, 'query': query,
                'update_listing': 'True'})
            self.container_update = f'{PLUGINPATH}?{urlencode(params)}'
            # Trigger container update using new path with query after adding items
            # Prevents onback from re-prompting for user input by re-writing path

        self.update_listing = True if update_listing else False
        self.container_content = convert_type(tmdb_type, 'container')
        self.kodi_db = self.get_kodi_database(tmdb_type)
        self.plugin_category = f'{get_localized(137)} - {query} ({tmdb_type})'

        return items
