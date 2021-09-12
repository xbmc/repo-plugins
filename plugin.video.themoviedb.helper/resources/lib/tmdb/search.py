import xbmc
import xbmcgui
from resources.lib.addon.cache import set_search_history, get_search_history
from resources.lib.addon.plugin import ADDONPATH, ADDON, PLUGINPATH, convert_type
from resources.lib.addon.setutils import merge_two_dicts
from urllib.parse import urlencode


MULTISEARCH_TYPES = ['movie', 'tv', 'person', 'collection', 'company', 'keyword']


def get_zippered_list(lists):
    max_len = 0
    for i in lists:
        max_len = max(max_len, len(i))
    return [i[x] for x in range(max_len) for i in lists if x < len(i)]


class SearchLists():
    def list_multisearchdir_router(self, **kwargs):
        if kwargs.get('clear_cache') != 'True':
            return self._list_multisearchdir(**kwargs)
        for tmdb_type in MULTISEARCH_TYPES:
            set_search_history(tmdb_type, clear_cache=True)
        self.container_refresh = True

    def _list_multisearchdir(self, **kwargs):
        lists = [self.list_searchdir(i, clear_cache_item=False, append_type=True) for i in MULTISEARCH_TYPES]
        items = get_zippered_list(lists)
        if len(items) > len(MULTISEARCH_TYPES):  # We have search results so need clear cache item
            items.append({
                'label': ADDON.getLocalizedString(32121),
                'art': {'thumb': u'{}/resources/icons/tmdb/search.png'.format(ADDONPATH)},
                'infoproperties': {'specialsort': 'bottom'},
                'params': {'info': 'dir_multisearch', 'clear_cache': 'True'}})
        return items

    def list_searchdir_router(self, tmdb_type, **kwargs):
        if kwargs.get('clear_cache') != 'True':
            return self.list_searchdir(tmdb_type, **kwargs)
        set_search_history(tmdb_type, clear_cache=True)
        self.container_refresh = True

    def list_searchdir(self, tmdb_type, clear_cache_item=True, append_type=False, **kwargs):
        base_item = {
            'label': u'{} {}'.format(xbmc.getLocalizedString(137), convert_type(tmdb_type, 'plural')),
            'art': {'thumb': u'{}/resources/icons/tmdb/search.png'.format(ADDONPATH)},
            'infoproperties': {'specialsort': 'top'},
            'params': merge_two_dicts(kwargs, {'info': 'search', 'tmdb_type': tmdb_type})}
        items = []
        items.append(base_item)

        history = get_search_history(tmdb_type)
        history.reverse()
        for i in history:
            item = {
                'label': u'{} ({})'.format(i, tmdb_type) if append_type else i,
                'art': base_item.get('art'),
                'params': merge_two_dicts(base_item.get('params', {}), {'query': i})}
            items.append(item)
        if history and clear_cache_item:
            item = {
                'label': ADDON.getLocalizedString(32121),
                'art': base_item.get('art'),
                'infoproperties': {'specialsort': 'bottom'},
                'params': merge_two_dicts(base_item.get('params', {}), {'info': 'dir_search', 'clear_cache': 'True'})}
            items.append(item)
        return items

    def list_search(self, tmdb_type, query=None, update_listing=False, page=None, **kwargs):
        original_query = query

        if not query:
            query = set_search_history(
                query=xbmcgui.Dialog().input(ADDON.getLocalizedString(32044), type=xbmcgui.INPUT_ALPHANUM),
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
            self.container_update = u'{}?{}'.format(PLUGINPATH, urlencode(params))
            # Trigger container update using new path with query after adding items
            # Prevents onback from re-prompting for user input by re-writing path

        self.update_listing = True if update_listing else False
        self.container_content = convert_type(tmdb_type, 'container')
        self.kodi_db = self.get_kodi_database(tmdb_type)

        return items
