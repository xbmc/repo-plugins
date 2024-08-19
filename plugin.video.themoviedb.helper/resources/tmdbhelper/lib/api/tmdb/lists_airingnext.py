from tmdbhelper.lib.items.container import Container
from tmdbhelper.lib.addon.plugin import convert_type, get_localized


class ListAiringNext(Container):
    def _get_items(self, seed_items: list, prefix: str, reverse: bool = False, **kwargs):
        from tmdbhelper.lib.addon.thread import ParallelThread
        from tmdbhelper.lib.addon.tmdate import date_in_range, is_future_timestamp
        from tmdbhelper.lib.api.mapping import get_empty_item
        from tmdbhelper.lib.items.pages import PaginatedItems

        def _get_nextaired_item(tmdb_id):
            cache_name = f'TMDb.get_nextaired_item.{prefix}.{tmdb_id}'
            cache_item = self.tmdb_api._cache.get_cache(cache_name)
            if cache_item:
                return cache_item

            ip = self.tmdb_api.get_tvshow_nextaired(tmdb_id)
            if not ip:
                return

            item_airdate = ip.get(f'{prefix}.original')
            if not item_airdate:
                return

            status = ip.get('status')
            if status in ['Canceled', 'Ended']:
                cache_days = 30  # Check in a month just in case gets renewed on another network
            elif date_in_range(item_airdate, 10, -2, date_fmt="%Y-%m-%d", date_lim=10):
                cache_days = 1  # Item airing this week so check again tomorrow in case schedule changes
            else:
                cache_days = 7  # Item airing in more than a week so let's check next week just in case of changes

            item = get_empty_item()
            item['infoproperties'] = ip
            item['infolabels']['mediatype'] = 'episode'
            item['infolabels']['title'] = ip.get(f'{prefix}.name')
            item['infolabels']['episode'] = ip.get(f'{prefix}.episode')
            item['infolabels']['season'] = ip.get(f'{prefix}.season')
            item['infolabels']['plot'] = ip.get(f'{prefix}.plot')
            item['infolabels']['year'] = ip.get(f'{prefix}.year')
            item['infolabels']['premiered'] = item_airdate
            item['art']['thumb'] = ip.get(f'{prefix}.thumb')
            item['label'] = f"{item['infolabels']['title']} ({item_airdate})"
            item['infoproperties']['tmdb_type'] = 'episode'
            item['infoproperties']['tmdb_id'] = item['unique_ids']['tvshow.tmdb'] = tmdb_id
            item['params'] = {
                'info': 'details',
                'tmdb_type': 'tv',
                'tmdb_id': tmdb_id,
                'episode': item['infolabels']['episode'],
                'season': item['infolabels']['season']}
            return self.tmdb_api._cache.set_cache(item, cache_name=cache_name, cache_days=cache_days)

        def _get_nextaired_item_thread(i):
            tmdb_id = i.get('tmdb_id') or self.tmdb_api.get_tmdb_id(
                tmdb_type='tv', imdb_id=i.get('imdb_id'), tvdb_id=i.get('tvdb_id'),
                query=i.get('showtitle') or i.get('title'), year=i.get('year'))
            if not tmdb_id:
                return

            item = _get_nextaired_item(tmdb_id)
            if not item:
                return

            item['infolabels']['tvshowtitle'] = i.get('showtitle') or i.get('title')
            return item

        with ParallelThread(seed_items, _get_nextaired_item_thread) as pt:
            item_queue = pt.queue

        items = [
            i for i in item_queue if i
            and is_future_timestamp(
                i['infoproperties'].get(f'{prefix}.original'),
                time_fmt="%Y-%m-%d", time_lim=10, days=-1)]

        items = sorted(items, key=lambda i: i['infoproperties'][f'{prefix}.original'], reverse=reverse)

        self.ib.cache_only = self.tmdb_cache_only = False
        self.container_content = convert_type('episode', 'container')

        paginated_items = PaginatedItems(items, page=kwargs.get('page', 1), limit=20)
        return paginated_items.items + paginated_items.next_page


class ListLibraryAiringNext(ListAiringNext):
    def get_items(self, **kwargs):
        from tmdbhelper.lib.api.kodi.rpc import get_kodi_library
        kodi_db = get_kodi_library('tv')
        if not kodi_db or not kodi_db.database:
            return
        self.plugin_category = f'{get_localized(32458)}'
        return self._get_items(kodi_db.database, 'next_aired', **kwargs)


class ListTraktAiringNext(ListAiringNext):
    def get_items(self, **kwargs):
        _dummydict = {}
        items = self.trakt_api.get_sync('watched', 'show', 'tmdb', extended='full')
        items = [{
            'tmdb_id': k,
            'imdb_id': v.get('show', _dummydict).get('ids', _dummydict).get('imdb', ''),
            'tvdb_id': v.get('show', _dummydict).get('ids', _dummydict).get('tvdb', ''),
            'title': v.get('show', _dummydict).get('title', ''),
            'year': v.get('show', _dummydict).get('year', '')}
            for k, v in items.items() if k and v]
        self.plugin_category = f'{get_localized(32459)}'
        return self._get_items(items, 'next_aired', **kwargs)
