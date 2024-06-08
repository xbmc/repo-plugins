from tmdbhelper.lib.addon.consts import TMDB_BASIC_LISTS, TMDB_SORT_TYPES
from tmdbhelper.lib.addon.plugin import convert_type, get_plugin_category, get_setting, get_localized
from tmdbhelper.lib.items.container import Container


class ListBasic(Container):
    def get_items(self, info, tmdb_type, tmdb_id=None, page=None, limit=None, sort_key=None, sort_key_order=None, length=None, **kwargs):
        info_model = TMDB_BASIC_LISTS.get(info)
        info_tmdb_type = info_model.get('tmdb_type') or tmdb_type
        self.tmdb_api.mapper.imagepath_quality = info_model.get('imagepath_quality', 'IMAGEPATH_ORIGINAL')
        items = self.tmdb_api.get_basic_list(
            path=info_model.get('path', '').format(
                tmdb_type=tmdb_type,
                tmdb_id=tmdb_id,
                iso_country=self.tmdb_api.iso_country,
                **kwargs),
            sort_key=sort_key or info_model.get('sort_key'),
            sort_key_order=sort_key_order or info_model.get('sort_key_order'),
            stacked=info_model.get('stacked'),
            tmdb_type=info_tmdb_type,
            base_tmdb_type=tmdb_type,
            key=info_model.get('key', 'results'),
            params=info_model.get('params'),
            filters=self.filters,
            icon_path=get_setting(info_model['icon_path'], 'str') if 'icon_path' in info_model else None,
            limit=limit or info_model.get('limit'),
            length=length or info_model.get('length'),
            page=page)
        if 'tmdb_cache_only' in info_model:
            self.tmdb_cache_only = info_model['tmdb_cache_only']
        self.kodi_db = self.get_kodi_database(info_tmdb_type)
        self.sort_by_dbid = True if self.kodi_db and info_model.get('dbid_sorting') else False
        self.library = convert_type(info_tmdb_type, 'library')
        self.container_content = convert_type(info_tmdb_type, 'container', items=items)
        self.plugin_category = get_plugin_category(info_model, convert_type(info_tmdb_type, 'plural'))
        return items


class ListCombo(Container):
    def get_items(self, info, tmdb_id=None, limit=None, sort_key=None, sort_type=None, **kwargs):
        info_model = TMDB_BASIC_LISTS.get(info)
        info_tmdb_type = info_model.get('tmdb_type')
        sort_key = sort_key or info_model.get('sort_key')
        sort_type = sort_type or info_model.get('sort_type')
        sort_type = TMDB_SORT_TYPES.get(sort_type) or str

        info_path_models = info_model.get('info_path_models') or []
        self.tmdb_api.mapper.imagepath_quality = info_model.get('imagepath_quality', 'IMAGEPATH_ORIGINAL')
        items = []

        for info_path_model in info_path_models:
            tmdb_type = info_path_model.get('tmdb_type')
            items += self.tmdb_api.get_basic_list(
                path=info_path_model.get('path', '').format(
                    tmdb_type=tmdb_type, tmdb_id=tmdb_id,
                    iso_country=self.tmdb_api.iso_country),
                sort_key=info_path_model.get('sort_key'),
                stacked=info_path_model.get('stacked'),
                tmdb_type=tmdb_type,
                base_tmdb_type=tmdb_type,
                key=info_path_model.get('key', 'results'),
                params=info_path_model.get('params'),
                filters=self.filters,
                limit=limit or info_path_model.get('limit'),
                pagination=False)

        if 'tmdb_cache_only' in info_model:
            self.tmdb_cache_only = info_model['tmdb_cache_only']

        if sort_key:
            dummy_dict = {}
            items = sorted(items, key=lambda i: sort_type(i.get('infolabels', dummy_dict).get(sort_key, 0) or i.get('infoproperties', dummy_dict).get(sort_key, 0)), reverse=True)

        self.kodi_db = self.get_kodi_database(info_tmdb_type)
        self.sort_by_dbid = True if self.kodi_db and info_model.get('dbid_sorting') else False
        self.library = convert_type(info_tmdb_type, 'library')
        self.container_content = convert_type(info_tmdb_type, 'container')
        self.plugin_category = get_plugin_category(info_model, convert_type(info_tmdb_type, 'plural'))

        return items


class ListSeasons(Container):
    def get_items(self, tmdb_id, **kwargs):
        self.ib.cache_only = self.tmdb_cache_only = False
        self.precache_parent(tmdb_id)
        items = self.tmdb_api.get_season_list(tmdb_id, special_folders=get_setting('special_folders', 'int'), get_detailed=True)
        self.container_content = convert_type('season', 'container')
        return items


class ListEpisodes(Container):
    def get_items(self, tmdb_id, season, **kwargs):
        self.ib.cache_only = self.tmdb_cache_only = False
        self.precache_parent(tmdb_id, season)
        items = self.tmdb_api.get_episode_list(tmdb_id, season, get_detailed=True)
        items = list(items) if items else []
        self.kodi_db = self.get_kodi_database('tv')
        self.container_content = convert_type('episode', 'container')
        self.plugin_category = f'{get_localized(20373)} {season}'
        return items


class ListEpisodeGroups(Container):
    def get_items(self, tmdb_id, **kwargs):
        items = self.tmdb_api.get_episode_groups_list(tmdb_id)
        self.ib.cache_only = self.tmdb_cache_only = False
        self.precache_parent(tmdb_id) if items else None
        self.container_content = convert_type('tv', 'container')
        return items


class ListEpisodeGroupSeasons(Container):
    def get_items(self, tmdb_id, group_id, **kwargs):
        items = self.tmdb_api.get_episode_group_seasons_list(tmdb_id, group_id)
        self.ib.cache_only = self.tmdb_cache_only = False
        self.precache_parent(tmdb_id) if items else None
        self.container_content = convert_type('season', 'container')
        self.trakt_watchedindicators = False  # Force override of setting because not "true" seasons so data will be incorrect
        return items


class ListEpisodeGroupEpisodes(Container):
    def get_items(self, tmdb_id, group_id, position, **kwargs):
        items = self.tmdb_api.get_episode_group_episodes_list(tmdb_id, group_id, position)
        self.ib.cache_only = self.tmdb_cache_only = False
        self.precache_parent(tmdb_id) if items else None
        self.container_content = convert_type('episode', 'container')
        return items


class ListNextRecommendation(Container):
    def get_items(self, tmdb_id, tmdb_type, season=None, episode=None, **kwargs):
        if tmdb_type not in ['movie', 'tv']:
            return []

        def _get_next_recommendation():
            path = f'{tmdb_type}/{tmdb_id}/recommendations'
            response = self.tmdb_api.get_basic_list(path, tmdb_type=tmdb_type, paginated=False)
            try:
                return response[0]
            except IndexError:
                return

        def _get_next_collection():
            path = f'movie/{tmdb_id}'
            response = self.tmdb_api.get_request_sc(path)
            try:
                collection_id = response['belongs_to_collection']['id']
                path = f'collection/{collection_id}'
                response = self.tmdb_api.get_basic_list(path, tmdb_type='movie', key='parts', paginated=False)
                for x, item in enumerate(response):
                    if str(item['infoproperties']['tmdb_id']) == str(tmdb_id):
                        return response[x + 1]
            except (KeyError, IndexError, TypeError):
                return _get_next_recommendation()

        def _get_next_episode():
            item = None
            if season and episode:
                item = self.tmdb_api.get_next_episode(tmdb_id, season, episode)
            if not item:
                item = _get_next_recommendation()
                try:
                    item = self.tmdb_api.get_next_episode(item['infoproperties']['tmdb_id'], 1, 0)
                except (KeyError, TypeError):
                    return
            return item

        next_item = _get_next_episode() if tmdb_type == 'tv' else _get_next_collection()

        if not next_item:
            return []

        self.kodi_db = self.get_kodi_database(tmdb_type)
        self.library = convert_type(tmdb_type, 'library')
        self.container_content = 'episodes' if tmdb_type == 'tv' else 'movies'
        return [next_item]


class ListAll(Container):
    def get_items(self, tmdb_type, page=None, **kwargs):
        items = self.tmdb_api.get_all_items_list(tmdb_type, page=page)
        self.tmdb_cache_only = False
        self.kodi_db = self.get_kodi_database(tmdb_type)
        self.library = convert_type(tmdb_type, 'library')
        self.container_content = convert_type(tmdb_type, 'container')
        return items


class ListCast(Container):
    def get_items(self, tmdb_id, tmdb_type, season=None, episode=None, aggregate=False, **kwargs):
        items = self.tmdb_api.get_cast_list(tmdb_id, tmdb_type, season=season, episode=episode, aggregate=aggregate, **kwargs)
        self.tmdb_cache_only = True
        self.container_content = convert_type('person', 'container')
        return items


class ListCrew(Container):
    def get_items(self, tmdb_id, tmdb_type, season=None, episode=None, aggregate=False, **kwargs):
        items = self.tmdb_api.get_cast_list(tmdb_id, tmdb_type, season=season, episode=episode, keys=['crew'], aggregate=aggregate, **kwargs)
        self.tmdb_cache_only = True
        self.container_content = convert_type('person', 'container')
        return items


class ListFlatSeasons(Container):
    def get_items(self, tmdb_id, **kwargs):
        items = self.tmdb_api.get_flatseasons_list(tmdb_id)
        items = list(items) if items else []
        self.tmdb_cache_only = False
        self.kodi_db = self.get_kodi_database('tv')
        self.container_content = convert_type('episode', 'container')
        return items


class ListVideos(Container):
    def get_items(self, tmdb_id, tmdb_type, season=None, episode=None, **kwargs):
        items = self.tmdb_api.get_videos_list(tmdb_id, tmdb_type, season, episode)
        self.tmdb_cache_only = True
        self.container_content = convert_type('video', 'container')
        return items
