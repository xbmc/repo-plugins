class TMDbMethods():

    """
    TMDb DETAILS METHODS
    """

    def get_genres(self, *args, **kwargs):
        try:
            return self._get_genres(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.tmdb.methods.details import get_genres
            self._get_genres = get_genres
            return self._get_genres(self, *args, **kwargs)

    def get_tmdb_multisearch_validfy(self, *args, **kwargs):
        try:
            return self._get_tmdb_multisearch_validfy(*args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.tmdb.methods.details import get_tmdb_multisearch_validfy
            self._get_tmdb_multisearch_validfy = get_tmdb_multisearch_validfy
            return self._get_tmdb_multisearch_validfy(*args, **kwargs)

    def get_tmdb_multisearch_request(self, *args, **kwargs):
        try:
            return self._get_tmdb_multisearch_request(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.tmdb.methods.details import get_tmdb_multisearch_request
            self._get_tmdb_multisearch_request = get_tmdb_multisearch_request
            return self._get_tmdb_multisearch_request(self, *args, **kwargs)

    def get_tmdb_multisearch(self, *args, **kwargs):
        try:
            return self._get_tmdb_multisearch(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.tmdb.methods.details import get_tmdb_multisearch
            self._get_tmdb_multisearch = get_tmdb_multisearch
            return self._get_tmdb_multisearch(self, *args, **kwargs)

    def get_tmdb_id(self, *args, **kwargs):
        try:
            return self._get_tmdb_id(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.tmdb.methods.details import get_tmdb_id
            self._get_tmdb_id = get_tmdb_id
            return self._get_tmdb_id(self, *args, **kwargs)

    def get_tmdb_id_request(self, *args, **kwargs):
        try:
            return self._get_tmdb_id_request(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.tmdb.methods.details import get_tmdb_id_request
            self._get_tmdb_id_request = get_tmdb_id_request
            return self._get_tmdb_id_request(self, *args, **kwargs)

    def get_tmdb_id_from_query(self, *args, **kwargs):
        try:
            return self._get_tmdb_id_from_query(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.tmdb.methods.details import get_tmdb_id_from_query
            self._get_tmdb_id_from_query = get_tmdb_id_from_query
            return self._get_tmdb_id_from_query(self, *args, **kwargs)

    def get_collection_tmdb_id(self, *args, **kwargs):
        try:
            return self._get_collection_tmdb_id(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.tmdb.methods.details import get_collection_tmdb_id
            self._get_collection_tmdb_id = get_collection_tmdb_id
            return self._get_collection_tmdb_id(self, *args, **kwargs)

    def get_tmdb_id_list(self, *args, **kwargs):
        try:
            return self._get_tmdb_id_list(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.tmdb.methods.details import get_tmdb_id_list
            self._get_tmdb_id_list = get_tmdb_id_list
            return self._get_tmdb_id_list(self, *args, **kwargs)

    def get_tvshow_nextaired(self, *args, **kwargs):
        try:
            return self._get_tvshow_nextaired(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.tmdb.methods.details import get_tvshow_nextaired
            self._get_tvshow_nextaired = get_tvshow_nextaired
            return self._get_tvshow_nextaired(self, *args, **kwargs)

    def get_details_request(self, *args, **kwargs):
        try:
            return self._get_details_request(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.tmdb.methods.details import get_details_request
            self._get_details_request = get_details_request
            return self._get_details_request(self, *args, **kwargs)

    def get_details(self, *args, **kwargs):
        try:
            return self._get_details(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.tmdb.methods.details import get_details
            self._get_details = get_details
            return self._get_details(self, *args, **kwargs)

    def get_next_episode(self, *args, **kwargs):
        try:
            return self._get_next_episode(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.tmdb.methods.details import get_next_episode
            self._get_next_episode = get_next_episode
            return self._get_next_episode(self, *args, **kwargs)

    """
    TMDb LIST METHODS
    """

    def get_flatseasons_list(self, *args, **kwargs):
        try:
            return self._get_flatseasons_list(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.tmdb.methods.lists import get_flatseasons_list
            self._get_flatseasons_list = get_flatseasons_list
            return self._get_flatseasons_list(self, *args, **kwargs)

    def get_episode_group_episodes_list(self, *args, **kwargs):
        try:
            return self._get_episode_group_episodes_list(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.tmdb.methods.lists import get_episode_group_episodes_list
            self._get_episode_group_episodes_list = get_episode_group_episodes_list
            return self._get_episode_group_episodes_list(self, *args, **kwargs)

    def get_episode_group_seasons_list(self, *args, **kwargs):
        try:
            return self._get_episode_group_seasons_list(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.tmdb.methods.lists import get_episode_group_seasons_list
            self._get_episode_group_seasons_list = get_episode_group_seasons_list
            return self._get_episode_group_seasons_list(self, *args, **kwargs)

    def get_episode_groups_list(self, *args, **kwargs):
        try:
            return self._get_episode_groups_list(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.tmdb.methods.lists import get_episode_groups_list
            self._get_episode_groups_list = get_episode_groups_list
            return self._get_episode_groups_list(self, *args, **kwargs)

    def get_videos_list(self, *args, **kwargs):
        try:
            return self._get_videos_list(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.tmdb.methods.lists import get_videos_list
            self._get_videos_list = get_videos_list
            return self._get_videos_list(self, *args, **kwargs)

    def get_season_list(self, *args, **kwargs):
        try:
            return self._get_season_list(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.tmdb.methods.lists import get_season_list
            self._get_season_list = get_season_list
            return self._get_season_list(self, *args, **kwargs)

    def get_episode_list(self, *args, **kwargs):
        try:
            return self._get_episode_list(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.tmdb.methods.lists import get_episode_list
            self._get_episode_list = get_episode_list
            return self._get_episode_list(self, *args, **kwargs)

    def get_cast_list(self, *args, **kwargs):
        try:
            return self._get_cast_list(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.tmdb.methods.lists import get_cast_list
            self._get_cast_list = get_cast_list
            return self._get_cast_list(self, *args, **kwargs)

    def get_downloaded_list(self, *args, **kwargs):
        try:
            return self._get_downloaded_list(*args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.tmdb.methods.lists import get_downloaded_list
            self._get_downloaded_list = get_downloaded_list
            return self._get_downloaded_list(*args, **kwargs)

    def get_daily_list(self, *args, **kwargs):
        try:
            return self._get_daily_list(*args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.tmdb.methods.lists import get_daily_list
            self._get_daily_list = get_daily_list
            return self._get_daily_list(*args, **kwargs)

    def get_all_items_list(self, *args, **kwargs):
        try:
            return self._get_all_items_list(*args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.tmdb.methods.lists import get_all_items_list
            self._get_all_items_list = get_all_items_list
            return self._get_all_items_list(*args, **kwargs)

    def get_search_list(self, *args, **kwargs):
        try:
            return self._get_search_list(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.tmdb.methods.lists import get_search_list
            self._get_search_list = get_search_list
            return self._get_search_list(self, *args, **kwargs)

    def get_basic_list(self, *args, **kwargs):
        try:
            return self._get_basic_list(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.tmdb.methods.lists import get_basic_list
            self._get_basic_list = get_basic_list
            return self._get_basic_list(self, *args, **kwargs)

    def get_discover_list(self, *args, **kwargs):
        try:
            return self._get_discover_list(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.tmdb.methods.lists import get_discover_list
            self._get_discover_list = get_discover_list
            return self._get_discover_list(self, *args, **kwargs)
