from resources.lib.items.container import Container
from resources.lib.addon.plugin import get_plugin_category, get_localized, PLUGINPATH
from resources.lib.addon.consts import MDBLIST_LIST_OF_LISTS


class ListLists(Container):
    def get_items(self, info, page=None, **kwargs):
        from xbmcplugin import SORT_METHOD_UNSORTED

        info_model = MDBLIST_LIST_OF_LISTS.get(info)

        items = self.mdblist_api.get_list_of_lists(
            path=info_model.get('path', '').format(**kwargs),
            page=page or 1)

        self.library = 'video'
        self.plugin_category = get_plugin_category(info_model)
        self.sort_methods = [{'sortMethod': SORT_METHOD_UNSORTED, 'label2Mask': '%U'}]  # Label2 Mask by Studio (i.e. User Name)
        return items


class ListCustom(Container):
    def get_items(self, list_id, page=None, **kwargs):
        response = self.mdblist_api.get_custom_list(
            page=page or 1,
            list_id=list_id)

        self.tmdb_cache_only = False
        self.set_mixed_content(response)

        return response.get('items', []) + response.get('next_page', [])


class ListCustomSearch(Container):
    def get_items(self, query=None, **kwargs):
        if not query:
            from xbmcgui import Dialog
            kwargs['query'] = query = Dialog().input(get_localized(32044))
            if not kwargs['query']:
                return
            from resources.lib.addon.parser import encode_url
            self.container_update = f'{encode_url(PLUGINPATH, **kwargs)},replace'
        from xbmcplugin import SORT_METHOD_UNSORTED
        items = self.mdblist_api.get_list_of_lists(path=f'lists/search?s={query}')
        self.library = 'video'
        self.sort_methods = [{'sortMethod': SORT_METHOD_UNSORTED, 'label2Mask': '%U'}]  # Label2 Mask by Studio (i.e. User Name)
        return items
