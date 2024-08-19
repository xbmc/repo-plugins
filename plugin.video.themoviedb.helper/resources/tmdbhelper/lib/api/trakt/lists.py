from jurialmunkey.parser import try_int
from tmdbhelper.lib.addon.plugin import convert_type, PLUGINPATH, get_plugin_category, get_localized, get_setting, encode_url
from tmdbhelper.lib.items.container import Container


class ListBasic(Container):
    def get_items(
            self, info, tmdb_type, page=None, randomise=False, limit=None,
            genres=None, years=None, query=None, languages=None, countries=None, runtimes=None, studio_ids=None,
            **kwargs
    ):

        from tmdbhelper.lib.addon.consts import TRAKT_BASIC_LISTS

        def _get_items_both():
            info_model = TRAKT_BASIC_LISTS.get(info)
            items = self.trakt_api.get_mixed_list(
                path=info_model.get('path', ''),
                trakt_types=['movie', 'show'],
                authorize=info_model.get('authorize', False),
                extended=info_model.get('extended', None),
                genres=genres, years=years, query=query, languages=languages, countries=countries, runtimes=runtimes, studio_ids=studio_ids
            )
            self.tmdb_cache_only = False
            self.library = 'video'
            self.container_content = 'movies'
            self.kodi_db = self.get_kodi_database('both')
            return items

        if tmdb_type == 'both':
            return _get_items_both()
        info_model = TRAKT_BASIC_LISTS.get(info)
        info_tmdb_type = info_model.get('tmdb_type') or tmdb_type
        trakt_type = convert_type(tmdb_type, 'trakt')
        func = self.trakt_api.get_stacked_list if info_model.get('stacked') else self.trakt_api.get_basic_list
        items = func(
            path=info_model.get('path', '').format(trakt_type=trakt_type, **kwargs),
            trakt_type=trakt_type,
            params=info_model.get('params'),
            page=page,
            limit=limit,
            authorize=info_model.get('authorize', False),
            sort_by=info_model.get('sort_by', None),
            sort_how=info_model.get('sort_how', None),
            extended=info_model.get('extended', None),
            randomise=randomise,
            genres=genres, years=years, query=query, languages=languages, countries=countries, runtimes=runtimes, studio_ids=studio_ids,
            always_refresh=False   # Basic lists don't need updating more than once per day
        )
        self.tmdb_cache_only = False
        self.kodi_db = self.get_kodi_database(info_tmdb_type)
        self.library = convert_type(info_tmdb_type, 'library')
        self.container_content = convert_type(info_tmdb_type, 'container')
        self.plugin_category = get_plugin_category(info_model, convert_type(info_tmdb_type, 'plural'))
        return items


class ListSync(Container):
    def get_items(self, info, tmdb_type, page=None, **kwargs):
        from tmdbhelper.lib.addon.consts import TRAKT_SYNC_LISTS
        info_model = TRAKT_SYNC_LISTS.get(info)
        info_tmdb_type = info_model.get('tmdb_type') or tmdb_type
        items = self.trakt_api.get_sync_list(
            sync_type=info_model.get('sync_type', ''),
            trakt_type=convert_type(tmdb_type, 'trakt'),
            page=page,
            params=info_model.get('params'),
            sort_by=kwargs.get('sort_by', None) or info_model.get('sort_by', None),
            sort_how=kwargs.get('sort_how', None) or info_model.get('sort_how', None),
            extended=kwargs.get('extended', None) or info_model.get('extended', None),
            filters=info_model.get('filters', None))
        self.tmdb_cache_only = False
        self.kodi_db = self.get_kodi_database(info_tmdb_type)
        self.library = convert_type(info_tmdb_type, 'library')
        self.container_content = convert_type(info_tmdb_type, 'container')
        self.plugin_category = get_plugin_category(info_model, convert_type(info_tmdb_type, 'plural'))
        return items


class ListToWatch(Container):
    def get_items(self, info, tmdb_type, page=None, **kwargs):
        """ Get a mix of watchlisted and inprogress """
        if tmdb_type not in ['movie', 'tv']:
            return
        trakt_type = convert_type(tmdb_type, 'trakt')
        items = self.trakt_api.get_towatch_list(trakt_type=trakt_type, page=page)
        self.tmdb_cache_only = False
        self.kodi_db = self.get_kodi_database(tmdb_type)
        self.library = convert_type(tmdb_type, 'library')
        self.container_content = convert_type(tmdb_type, 'container')
        self.plugin_category = f'{convert_type(tmdb_type, "plural")} {get_localized(32078)}'
        return items


class ListComments(Container):
    def get_items(self, info, tmdb_type, tmdb_id, sort=None, **kwargs):
        """ Get a mix of watchlisted and inprogress """
        from tmdbhelper.lib.api.mapping import get_empty_item

        if tmdb_type not in ['movie', 'tv']:
            return
        trakt_type = convert_type(tmdb_type, 'trakt')
        slug = self.trakt_api.get_id(tmdb_id, 'tmdb', trakt_type, 'slug')
        items = self.trakt_api.get_request_sc(f'{trakt_type}s', slug, 'comments', sort, limit=50)

        def _map_item(i):
            item = get_empty_item()
            plot = i.get('comment') or ''
            rate = i.get('user_stats', {}).get('rating')
            date = i.get('created_at')[:10]
            plot = f'{plot}\n{get_localized(563)} {rate}/10' if rate else plot
            plot = f'{plot}\n{date}'
            item['infolabels']['plot'] = plot
            item['label'] = item['infolabels']['title'] = i.get('user', {}).get('name') or i.get('user', {}).get('username')
            item['infolabels']['premiered'] = date
            item['infolabels']['rating'] = rate
            item['params'] = {'comment_id': i.get('id'), 'parent_id': i.get('parent_id'), 'user_slug': i.get('user', {}).get('ids', {}).get('slug')}
            return item

        items = [_map_item(i) for i in items if i]

        return items


class ListBecauseYouWatched(Container):
    def get_items(self, info, tmdb_type, page=None, **kwargs):
        import random

        trakt_type = convert_type(tmdb_type, 'trakt')
        watched_items = self.trakt_api.get_sync_list(
            sync_type='watched',
            trakt_type=trakt_type,
            page=1,
            limit=get_setting('trakt_becausewatchedseed', 'int') or 5,
            next_page=False,
            params=None,
            sort_by='plays' if info == 'trakt_becausemostwatched' else 'watched',
            sort_how='desc')
        if not watched_items:
            return
        item = watched_items[random.randint(0, len(watched_items) - 1)]
        try:
            item_tmdb_type = item['params']['tmdb_type']
            item_tmdb_id = item['params']['tmdb_id']
        except (AttributeError, KeyError):
            return
        self.parent_params = {
            'info': 'recommendations',
            'tmdb_type': item_tmdb_type,
            'tmdb_id': item_tmdb_id}
        from tmdbhelper.lib.api.tmdb.lists import ListBasic as TMDbListBasic
        items = TMDbListBasic.get_items(
            self,
            info='recommendations',
            tmdb_type=item_tmdb_type,
            tmdb_id=item_tmdb_id,
            page=1)
        self.plugin_category = self.parent_params['plugin_category'] = f'{get_localized(32288)} {item.get("label")}'
        return items


class ListCalendar(Container):
    def _get_calendar_items(self, info, startdate, days, page=None, kodi_db=None, endpoint=None, user=True, **kwargs):
        from tmdbhelper.lib.addon.tmdate import get_calendar_name

        items = self.trakt_api.get_calendar_episodes_list(
            try_int(startdate),
            try_int(days),
            kodi_db=kodi_db,
            user=user,
            page=page,
            endpoint=endpoint)

        self.kodi_db = self.get_kodi_database('tv')
        self.tmdb_cache_only = False
        self.library = 'video'
        self.container_content = 'episodes'
        self.plugin_category = get_calendar_name(startdate=try_int(startdate), days=try_int(days))
        self.thumb_override = get_setting('calendar_art', 'int')
        return items

    def get_items(self, **kwargs):
        kwargs['user'] = kwargs.pop('user', '').lower() != 'false'
        return self._get_calendar_items(**kwargs)


class ListLibraryCalendar(ListCalendar):
    def get_items(self, **kwargs):
        from tmdbhelper.lib.api.kodi.rpc import get_kodi_library
        kodi_db = get_kodi_library('tv')
        if not kodi_db:
            return
        return self._get_calendar_items(kodi_db=kodi_db, user=False, **kwargs)


class ListInProgress(Container):
    def get_items(self, info, tmdb_type, page=None, **kwargs):
        if tmdb_type == 'tv':
            items = self.trakt_api.get_inprogress_shows_list(
                page=page,
                params={
                    'info': 'trakt_upnext',
                    'tmdb_type': 'tv',
                    'tmdb_id': '{tmdb_id}'},
                sort_by=kwargs.get('sort_by', None),
                sort_how=kwargs.get('sort_how', None))
        else:
            items = self.trakt_api.get_ondeck_list(
                page=page,
                trakt_type='movie',
                sort_by=kwargs.get('sort_by', None),
                sort_how=kwargs.get('sort_how', None))
        self.tmdb_cache_only = False
        self.kodi_db = self.get_kodi_database(tmdb_type)
        self.library = convert_type(tmdb_type, 'library')
        self.container_content = convert_type(tmdb_type, 'container')
        self.plugin_category = f'{get_localized(32196)} {convert_type(tmdb_type, "plural")}'
        return items


class ListOnDeck(Container):
    def get_items(self, page=None, **kwargs):
        items = self.trakt_api.get_ondeck_list(page=page, trakt_type='episode')
        self.tmdb_cache_only = False
        self.library = 'video'
        self.container_content = 'episodes'
        self.plugin_category = get_localized(32406)
        return items


class ListNextEpisodes(Container):
    def get_items(self, info, tmdb_type, page=None, **kwargs):
        if tmdb_type != 'tv':
            return
        sort_settings = {
            'airdate': ('released', 'desc'),
            'todays': ('airing', -1),
            'lastweek': ('airing', -7),
            'recentlywatched': (None, None)}
        sort_by, sort_how = sort_settings[get_setting('trakt_nextepisodesort', 'str')]
        items = self.trakt_api.get_upnext_episodes_list(page=page, sort_by=sort_by, sort_how=sort_how)
        self.tmdb_cache_only = False
        # self.kodi_db = self.get_kodi_database(tmdb_type)
        self.library = 'video'
        self.container_content = 'episodes'
        self.thumb_override = get_setting('calendar_art', 'int')
        self.plugin_category = get_localized(32197)
        return items


class ListUpNext(Container):
    def get_items(self, info, tmdb_type, tmdb_id, page=None, **kwargs):
        if tmdb_type != 'tv':
            return
        self.ib.cache_only = self.tmdb_cache_only = False
        self.precache_parent(tmdb_id)
        items = self.trakt_api.get_upnext_list(unique_id=tmdb_id, id_type='tmdb', page=page)
        if not items:
            items = self.tmdb_api.get_episode_list(tmdb_id, 1, get_detailed=True)
            items = list(items) if items else []
        self.kodi_db = self.get_kodi_database(tmdb_type)
        self.library = 'video'
        self.container_content = 'episodes'
        self.plugin_category = get_localized(32043)
        return items


class ListGenres(Container):
    def get_items(self, info, tmdb_type, **kwargs):
        items = self.trakt_api.get_list_of_genres(convert_type(tmdb_type, 'trakt'))
        self.library = 'video'
        self.plugin_category = get_localized(135)
        return items


class ListLists(Container):
    def get_items(self, info, page=None, **kwargs):
        from xbmcplugin import SORT_METHOD_UNSORTED
        from tmdbhelper.lib.addon.consts import TRAKT_LIST_OF_LISTS

        info_model = TRAKT_LIST_OF_LISTS.get(info)

        if info_model.get('get_trakt_id'):
            kwargs['trakt_type'] = {'movie': 'movie', 'tv': 'show'}[kwargs['tmdb_type']]
            kwargs['trakt_id'] = self.trakt_api.get_id(kwargs['tmdb_id'], 'tmdb', trakt_type=kwargs['trakt_type'], output_type='trakt')

        items = self.trakt_api.get_list_of_lists(
            path=info_model.get('path', '').format(**kwargs),
            page=page,
            authorize=info_model.get('authorize', False))

        self.library = 'video'
        self.plugin_category = get_plugin_category(info_model)
        self.sort_methods = [{'sortMethod': SORT_METHOD_UNSORTED, 'label2Mask': '%U'}]  # Label2 Mask by Studio (i.e. User Name)
        return items


class ListCustom(Container):
    def get_items(
            self, list_slug, user_slug=None, page=None,
            **kwargs
    ):
        from jurialmunkey.parser import boolean
        response = self.trakt_api.get_custom_list(
            page=page or 1,
            list_slug=list_slug,
            user_slug=user_slug,
            sort_by=kwargs.get('sort_by', None),
            sort_how=kwargs.get('sort_how', None),
            extended=kwargs.get('extended', None),
            authorize=False if user_slug and not boolean(kwargs.get('owner', False)) else True,
            always_refresh=True if not get_setting('trakt_cacheownlists') and boolean(kwargs.get('owner', False)) else False)
        if not response:
            return []
        self.tmdb_cache_only = False
        self.set_mixed_content(response)
        return response.get('items', []) + response.get('next_page', [])


class ListCustomSearch(Container):
    def get_items(self, query=None, **kwargs):
        from xbmcgui import Dialog
        if not query:
            kwargs['query'] = query = Dialog().input(get_localized(32044))
            if not kwargs['query']:
                return
            self.container_update = f'{encode_url(PLUGINPATH, **kwargs)},replace'
        items = self.trakt_api.get_list_of_lists(path=f'search/list?query={query}&fields=name', sort_likes=True, authorize=False)
        self.library = 'video'
        return items


class ListSortBy(Container):
    def get_items(self, info, **kwargs):
        from tmdbhelper.lib.api.trakt.sorting import get_sort_methods
        from tmdbhelper.lib.api.mapping import get_empty_item

        def _listsortby_item(i, **params):
            item = get_empty_item()
            item['label'] = item['infolabels']['title'] = f'{params.get("list_name")} - {i["name"]}'
            item['params'] = params
            for k, v in i['params'].items():
                item['params'][k] = v
            return item

        kwargs['info'] = kwargs.pop('parent_info', None)
        items = get_sort_methods(kwargs['info'])
        items = [_listsortby_item(i, **kwargs) for i in items]
        self.library = 'video'
        return items
