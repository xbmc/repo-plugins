from resources.lib.addon.consts import TMDB_BASIC_LISTS
from resources.lib.addon.plugin import convert_type, get_plugin_category, get_setting, get_localized
from resources.lib.items.container import Container


class ListBasic(Container):
    def get_items(self, info, tmdb_type, tmdb_id=None, page=None, limit=None, **kwargs):
        info_model = TMDB_BASIC_LISTS.get(info)
        info_tmdb_type = info_model.get('tmdb_type') or tmdb_type
        self.tmdb_api.mapper.imagepath_quality = info_model.get('imagepath_quality', 'IMAGEPATH_ORIGINAL')
        items = self.tmdb_api.get_basic_list(
            path=info_model.get('path', '').format(
                tmdb_type=tmdb_type,
                tmdb_id=tmdb_id,
                iso_country=self.tmdb_api.iso_country,
                **kwargs),
            tmdb_type=info_tmdb_type,
            base_tmdb_type=tmdb_type,
            key=info_model.get('key', 'results'),
            params=info_model.get('params'),
            filters=self.filters,
            limit=limit or info_model.get('limit'),
            page=page)
        if 'tmdb_cache_only' in info_model:
            self.tmdb_cache_only = info_model['tmdb_cache_only']
        self.kodi_db = self.get_kodi_database(info_tmdb_type)
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
        items = self.tmdb_api.get_cast_list(tmdb_id, tmdb_type, season=season, episode=episode, aggregate=aggregate)
        self.tmdb_cache_only = True
        self.container_content = convert_type('person', 'container')
        return items


class ListCrew(Container):
    def get_items(self, tmdb_id, tmdb_type, season=None, episode=None, aggregate=False, **kwargs):
        items = self.tmdb_api.get_cast_list(tmdb_id, tmdb_type, season=season, episode=episode, keys=['crew'], aggregate=aggregate)
        self.tmdb_cache_only = True
        self.container_content = convert_type('person', 'container')
        return items


class ListFlatSeasons(Container):
    def get_items(self, tmdb_id, **kwargs):
        items = self.tmdb_api.get_flatseasons_list(tmdb_id)
        self.tmdb_cache_only = False
        self.kodi_db = self.get_kodi_database('tv')
        self.container_content = convert_type('episode', 'container')
        return items


class ListVideos(Container):
    def get_items(self, tmdb_id, tmdb_type, season=None, episode=None, **kwargs):
        items = self.tmdb_api.get_videos(tmdb_id, tmdb_type, season, episode)
        self.tmdb_cache_only = True
        self.container_content = convert_type('video', 'container')
        return items
