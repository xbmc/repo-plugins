from resources.lib.addon.constants import TMDB_BASIC_LISTS
from resources.lib.addon.plugin import ADDON, convert_type


class TMDbLists():
    def list_tmdb(self, info, tmdb_type, tmdb_id=None, page=None, **kwargs):
        info_model = TMDB_BASIC_LISTS.get(info)
        info_tmdb_type = info_model.get('tmdb_type') or tmdb_type
        items = self.tmdb_api.get_basic_list(
            path=info_model.get('path', '').format(tmdb_type=tmdb_type, tmdb_id=tmdb_id, **kwargs),
            tmdb_type=info_tmdb_type,
            base_tmdb_type=tmdb_type,
            key=info_model.get('key', 'results'),
            params=info_model.get('params'),
            page=page)
        self.kodi_db = self.get_kodi_database(info_tmdb_type)
        self.library = convert_type(info_tmdb_type, 'library')
        self.container_content = convert_type(info_tmdb_type, 'container')
        return items

    def list_episode_group_episodes(self, tmdb_id, group_id, position, **kwargs):
        items = self.tmdb_api.get_episode_group_episodes_list(tmdb_id, group_id, position)
        self.container_content = convert_type('episode', 'container')
        return items

    def list_episode_group_seasons(self, tmdb_id, group_id, **kwargs):
        items = self.tmdb_api.get_episode_group_seasons_list(tmdb_id, group_id)
        self.container_content = convert_type('season', 'container')
        return items

    def list_episode_groups(self, tmdb_id, **kwargs):
        items = self.tmdb_api.get_episode_groups_list(tmdb_id)
        self.container_content = convert_type('tv', 'container')
        return items

    def list_flatseasons(self, tmdb_id, **kwargs):
        items = self.tmdb_api.get_flatseasons_list(tmdb_id)
        self.kodi_db = self.get_kodi_database('tv')
        self.container_content = convert_type('episode', 'container')
        return items

    def list_seasons(self, tmdb_id, **kwargs):
        items = self.tmdb_api.get_season_list(tmdb_id, special_folders=ADDON.getSettingInt('special_folders'))
        self.container_content = convert_type('season', 'container')
        return items

    def list_episodes(self, tmdb_id, season, **kwargs):
        items = self.tmdb_api.get_episode_list(tmdb_id, season)
        self.kodi_db = self.get_kodi_database('tv')
        self.container_content = convert_type('episode', 'container')
        return items

    def list_cast(self, tmdb_id, tmdb_type, season=None, episode=None, **kwargs):
        items = self.tmdb_api.get_cast_list(tmdb_id, tmdb_type, season=season, episode=episode)
        self.container_content = convert_type('person', 'container')
        return items

    def list_crew(self, tmdb_id, tmdb_type, season=None, episode=None, **kwargs):
        items = self.tmdb_api.get_cast_list(tmdb_id, tmdb_type, season=season, episode=episode, keys=['crew'])
        self.container_content = convert_type('person', 'container')
        return items

    def list_videos(self, tmdb_id, tmdb_type, season=None, episode=None, **kwargs):
        items = self.tmdb_api.get_videos(tmdb_id, tmdb_type, season, episode)
        self.container_content = convert_type('video', 'container')
        return items

    def list_all_items(self, tmdb_type, page=None, **kwargs):
        items = self.tmdb_api.get_all_items_list(tmdb_type, page=page)
        self.kodi_db = self.get_kodi_database(tmdb_type)
        self.library = convert_type(tmdb_type, 'library')
        self.container_content = convert_type(tmdb_type, 'container')
        return items
