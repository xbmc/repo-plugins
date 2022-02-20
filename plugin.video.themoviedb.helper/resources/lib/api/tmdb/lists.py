import xbmc
import xbmcaddon
from resources.lib.addon.constants import TMDB_BASIC_LISTS
from resources.lib.addon.plugin import convert_type, get_plugin_category


ADDON = xbmcaddon.Addon('plugin.video.themoviedb.helper')


class TMDbLists():
    def list_tmdb(self, info, tmdb_type, tmdb_id=None, page=None, limit=None, **kwargs):
        info_model = TMDB_BASIC_LISTS.get(info)
        info_tmdb_type = info_model.get('tmdb_type') or tmdb_type
        items = self.tmdb_api.get_basic_list(
            path=info_model.get('path', '').format(tmdb_type=tmdb_type, tmdb_id=tmdb_id, **kwargs),
            tmdb_type=info_tmdb_type,
            base_tmdb_type=tmdb_type,
            key=info_model.get('key', 'results'),
            params=info_model.get('params'),
            filters=self.filters,
            limit=limit or info_model.get('limit'),
            page=page)
        self.kodi_db = self.get_kodi_database(info_tmdb_type)
        self.library = convert_type(info_tmdb_type, 'library')
        self.container_content = convert_type(info_tmdb_type, 'container')
        self.plugin_category = get_plugin_category(info_model, convert_type(info_tmdb_type, 'plural'))
        return items

    def list_episode_group_episodes(self, tmdb_id, group_id, position, **kwargs):
        items = self.tmdb_api.get_episode_group_episodes_list(tmdb_id, group_id, position)
        self.tmdb_cache_only = False
        self.container_content = convert_type('episode', 'container')
        return items

    def list_episode_group_seasons(self, tmdb_id, group_id, **kwargs):
        items = self.tmdb_api.get_episode_group_seasons_list(tmdb_id, group_id)
        self.tmdb_cache_only = False
        self.container_content = convert_type('season', 'container')
        self.trakt_watchedindicators = False  # Force override of setting because not "true" seasons so data will be incorrect
        return items

    def list_episode_groups(self, tmdb_id, **kwargs):
        items = self.tmdb_api.get_episode_groups_list(tmdb_id)
        self.tmdb_cache_only = False
        self.container_content = convert_type('tv', 'container')
        return items

    def list_flatseasons(self, tmdb_id, **kwargs):
        items = self.tmdb_api.get_flatseasons_list(tmdb_id)
        self.tmdb_cache_only = False
        self.kodi_db = self.get_kodi_database('tv')
        self.container_content = convert_type('episode', 'container')
        return items

    def list_seasons(self, tmdb_id, **kwargs):
        items = self.tmdb_api.get_season_list(tmdb_id, special_folders=ADDON.getSettingInt('special_folders'))
        self.tmdb_cache_only = False
        self.container_content = convert_type('season', 'container')
        return items

    def list_episodes(self, tmdb_id, season, **kwargs):
        items = self.tmdb_api.get_episode_list(tmdb_id, season)
        self.tmdb_cache_only = False
        self.kodi_db = self.get_kodi_database('tv')
        self.container_content = convert_type('episode', 'container')
        self.plugin_category = '{} {}'.format(xbmc.getLocalizedString(20373), season)
        return items

    def list_cast(self, tmdb_id, tmdb_type, season=None, episode=None, **kwargs):
        items = self.tmdb_api.get_cast_list(tmdb_id, tmdb_type, season=season, episode=episode)
        self.tmdb_cache_only = True
        self.container_content = convert_type('person', 'container')
        return items

    def list_crew(self, tmdb_id, tmdb_type, season=None, episode=None, **kwargs):
        items = self.tmdb_api.get_cast_list(tmdb_id, tmdb_type, season=season, episode=episode, keys=['crew'])
        self.tmdb_cache_only = True
        self.container_content = convert_type('person', 'container')
        return items

    def list_videos(self, tmdb_id, tmdb_type, season=None, episode=None, **kwargs):
        items = self.tmdb_api.get_videos(tmdb_id, tmdb_type, season, episode)
        self.tmdb_cache_only = True
        self.container_content = convert_type('video', 'container')
        return items

    def list_all_items(self, tmdb_type, page=None, **kwargs):
        items = self.tmdb_api.get_all_items_list(tmdb_type, page=page)
        self.kodi_db = self.get_kodi_database(tmdb_type)
        self.library = convert_type(tmdb_type, 'library')
        self.container_content = convert_type(tmdb_type, 'container')
        return items
