from tmdbhelper.lib.items.container import Container


class ListListItems(Container):
    def _get_item_tmdb_id(self, item, tmdb_type):
        if tmdb_type == 'tv':
            tv_tmdb_id = self.tmdb_api.get_tmdb_id(
                tmdb_type=tmdb_type,
                tvdb_id=item['unique_ids'].get('tvdb'))
            if not tv_tmdb_id:
                tv_tmdb_id = self.tmdb_api.get_tmdb_id(
                    tmdb_type=tmdb_type,
                    query=item['infolabels'].get('originaltitle'),
                    year=item['infolabels'].get('year'))
            item['unique_ids']['tvshow.tmdb'] = item['unique_ids']['tmdb'] = tv_tmdb_id
        elif tmdb_type == 'movie':
            item['unique_ids']['tmdb'] = self.tmdb_api.get_tmdb_id(
                tmdb_type=tmdb_type,
                query=item['infolabels'].get('originaltitle'),
                year=item['infolabels'].get('year'))
        if not item['unique_ids'].get('tmdb'):
            return
        item['params'] = {'info': 'details', 'tmdb_type': tmdb_type, 'tmdb_id': item['unique_ids']['tmdb']}
        return item

    def _get_threaded_items(self, data, page, *args, **kwargs):
        from tmdbhelper.lib.items.pages import PaginatedItems
        response = PaginatedItems(data, page=page)
        if not response or not response.items:
            return
        from tmdbhelper.lib.addon.thread import ParallelThread
        with ParallelThread(response.items, self._get_item, *args, **kwargs) as pt:
            item_queue = pt.queue
        items = [i for i in item_queue if i]
        return items + response.next_page


class ListLists(Container):
    def _get_items(self, endpoint, param_info, key=None, params=None):
        data = self.tvdb_api.get_request_lc(endpoint)
        if key and data:
            self.plugin_category = data.get('name')
            data = data.get(key)
        if not data:
            return

        from tmdbhelper.lib.api.mapping import get_empty_item
        from tmdbhelper.lib.addon.consts import TVDB_DISCLAIMER
        from tmdbhelper.lib.addon.plugin import ADDONPATH
        tvdb_icon = f'{ADDONPATH}/resources/icons/tvdb/tvdb.png'

        def _get_item(i):
            item = get_empty_item()
            item['label'] = i.get('name')
            item['art']['icon'] = tvdb_icon
            item['params'] = {'info': param_info, 'tvdb_id': i.get('id')}
            item['infolabels']['plot'] = TVDB_DISCLAIMER
            if params:
                item['params'].update(params)
            return item

        items = [_get_item(i) for i in data if i.get('id')]

        return items
