class TraktMethods():

    """
    TRAKT LIST METHODS
    """

    def get_sorted_list(self, *args, **kwargs):
        try:
            return self._get_sorted_list(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.lists import get_sorted_list
            self._get_sorted_list = get_sorted_list
            return self._get_sorted_list(self, *args, **kwargs)

    def get_simple_list(self, *args, **kwargs):
        try:
            return self._get_simple_list(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.lists import get_simple_list
            self._get_simple_list = get_simple_list
            return self._get_simple_list(self, *args, **kwargs)

    def get_mixed_list(self, *args, **kwargs):
        try:
            return self._get_mixed_list(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.lists import get_mixed_list
            self._get_mixed_list = get_mixed_list
            return self._get_mixed_list(self, *args, **kwargs)

    def get_basic_list(self, *args, **kwargs):
        try:
            return self._get_basic_list(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.lists import get_basic_list
            self._get_basic_list = get_basic_list
            return self._get_basic_list(self, *args, **kwargs)

    def get_stacked_list(self, *args, **kwargs):
        try:
            return self._get_stacked_list(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.lists import get_stacked_list
            self._get_stacked_list = get_stacked_list
            return self._get_stacked_list(self, *args, **kwargs)

    def get_custom_list(self, *args, **kwargs):
        try:
            return self._get_custom_list(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.lists import get_custom_list
            self._get_custom_list = get_custom_list
            return self._get_custom_list(self, *args, **kwargs)

    def get_list_of_genres(self, *args, **kwargs):
        try:
            return self._get_list_of_genres(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.lists import get_list_of_genres
            self._get_list_of_genres = get_list_of_genres
            return self._get_list_of_genres(self, *args, **kwargs)

    def get_list_of_lists(self, *args, **kwargs):
        try:
            return self._get_list_of_lists(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.lists import get_list_of_lists
            self._get_list_of_lists = get_list_of_lists
            return self._get_list_of_lists(self, *args, **kwargs)

    def get_sync_list(self, *args, **kwargs):
        try:
            return self._get_sync_list(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.lists import get_sync_list
            self._get_sync_list = get_sync_list
            return self._get_sync_list(self, *args, **kwargs)

    def merge_sync_sort(self, *args, **kwargs):
        try:
            return self._merge_sync_sort(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.lists import merge_sync_sort
            self._merge_sync_sort = merge_sync_sort
            return self._merge_sync_sort(self, *args, **kwargs)

    def filter_inprogress(self, *args, **kwargs):
        try:
            return self._filter_inprogress(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.lists import filter_inprogress
            self._filter_inprogress = filter_inprogress
            return self._filter_inprogress(self, *args, **kwargs)

    def get_imdb_top250(self, *args, **kwargs):
        try:
            return self._get_imdb_top250(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.lists import get_imdb_top250
            self._get_imdb_top250 = get_imdb_top250
            return self._get_imdb_top250(self, *args, **kwargs)

    """
    TRAKT DETAILS METHODS
    """

    def get_details(self, *args, **kwargs):
        try:
            return self._get_details(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.details import get_details
            self._get_details = get_details
            return self._get_details(self, *args, **kwargs)

    def get_id(self, *args, **kwargs):
        try:
            return self._get_id(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.details import get_id
            self._get_id = get_id
            return self._get_id(self, *args, **kwargs)

    def get_id_search(self, *args, **kwargs):
        try:
            return self._get_id_search(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.details import get_id_search
            self._get_id_search = get_id_search
            return self._get_id_search(self, *args, **kwargs)

    def get_showitem_details(self, *args, **kwargs):
        try:
            return self._get_showitem_details(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.details import get_showitem_details
            self._get_showitem_details = get_showitem_details
            return self._get_showitem_details(self, *args, **kwargs)

    def get_episode_type(self, *args, **kwargs):
        try:
            return self._get_episode_type(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.details import get_episode_type
            self._get_episode_type = get_episode_type
            return self._get_episode_type(self, *args, **kwargs)

    def get_ratings(self, *args, **kwargs):
        try:
            return self._get_ratings(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.details import get_ratings
            self._get_ratings = get_ratings
            return self._get_ratings(self, *args, **kwargs)

    """
    TRAKT SYNC METHODS
    """

    def get_sync_item(self, *args, **kwargs):
        try:
            return self._get_sync_item(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.sync import get_sync_item
            self._get_sync_item = get_sync_item
            return self._get_sync_item(self, *args, **kwargs)

    def add_list_item(self, *args, **kwargs):
        try:
            return self._add_list_item(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.sync import add_list_item
            self._add_list_item = add_list_item
            return self._add_list_item(self, *args, **kwargs)

    def like_userlist(self, *args, **kwargs):
        try:
            return self._like_userlist(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.sync import like_userlist
            self._like_userlist = like_userlist
            return self._like_userlist(self, *args, **kwargs)

    def sync_item(self, *args, **kwargs):
        try:
            return self._sync_item(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.sync import sync_item
            self._sync_item = sync_item
            return self._sync_item(self, *args, **kwargs)

    def get_sync_response(self, *args, **kwargs):
        try:
            return self._get_sync_response(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.sync import get_sync_response
            self._get_sync_response = get_sync_response
            return self._get_sync_response(self, *args, **kwargs)

    def get_sync_configured(self, *args, **kwargs):
        try:
            return self._get_sync_configured(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.sync import get_sync_configured
            self._get_sync_configured = get_sync_configured
            return self._get_sync_configured(self, *args, **kwargs)

    def is_sync(self, *args, **kwargs):
        try:
            return self._is_sync(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.sync import is_sync
            self._is_sync = is_sync
            return self._is_sync(self, *args, **kwargs)

    def get_sync_watched_movies(self, *args, **kwargs):
        try:
            return self._get_sync_watched_movies(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.sync import get_sync_watched_movies
            self._get_sync_watched_movies = get_sync_watched_movies
            return self._get_sync_watched_movies(self, *args, **kwargs)

    def get_sync_watched_shows(self, *args, **kwargs):
        try:
            return self._get_sync_watched_shows(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.sync import get_sync_watched_shows
            self._get_sync_watched_shows = get_sync_watched_shows
            return self._get_sync_watched_shows(self, *args, **kwargs)

    def get_sync_collection_movies(self, *args, **kwargs):
        try:
            return self._get_sync_collection_movies(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.sync import get_sync_collection_movies
            self._get_sync_collection_movies = get_sync_collection_movies
            return self._get_sync_collection_movies(self, *args, **kwargs)

    def get_sync_collection_shows(self, *args, **kwargs):
        try:
            return self._get_sync_collection_shows(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.sync import get_sync_collection_shows
            self._get_sync_collection_shows = get_sync_collection_shows
            return self._get_sync_collection_shows(self, *args, **kwargs)

    def get_sync_playback_movies(self, *args, **kwargs):
        try:
            return self._get_sync_playback_movies(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.sync import get_sync_playback_movies
            self._get_sync_playback_movies = get_sync_playback_movies
            return self._get_sync_playback_movies(self, *args, **kwargs)

    def get_sync_playback_shows(self, *args, **kwargs):
        try:
            return self._get_sync_playback_shows(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.sync import get_sync_playback_shows
            self._get_sync_playback_shows = get_sync_playback_shows
            return self._get_sync_playback_shows(self, *args, **kwargs)

    def get_sync_watchlist_movies(self, *args, **kwargs):
        try:
            return self._get_sync_watchlist_movies(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.sync import get_sync_watchlist_movies
            self._get_sync_watchlist_movies = get_sync_watchlist_movies
            return self._get_sync_watchlist_movies(self, *args, **kwargs)

    def get_sync_watchlist_shows(self, *args, **kwargs):
        try:
            return self._get_sync_watchlist_shows(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.sync import get_sync_watchlist_shows
            self._get_sync_watchlist_shows = get_sync_watchlist_shows
            return self._get_sync_watchlist_shows(self, *args, **kwargs)

    def get_sync_watchlist_seasons(self, *args, **kwargs):
        try:
            return self._get_sync_watchlist_seasons(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.sync import get_sync_watchlist_seasons
            self._get_sync_watchlist_seasons = get_sync_watchlist_seasons
            return self._get_sync_watchlist_seasons(self, *args, **kwargs)

    def get_sync_watchlist_episodes(self, *args, **kwargs):
        try:
            return self._get_sync_watchlist_episodes(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.sync import get_sync_watchlist_episodes
            self._get_sync_watchlist_episodes = get_sync_watchlist_episodes
            return self._get_sync_watchlist_episodes(self, *args, **kwargs)

    def get_sync_favorites_movies(self, *args, **kwargs):
        try:
            return self._get_sync_favorites_movies(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.sync import get_sync_favorites_movies
            self._get_sync_favorites_movies = get_sync_favorites_movies
            return self._get_sync_favorites_movies(self, *args, **kwargs)

    def get_sync_favorites_shows(self, *args, **kwargs):
        try:
            return self._get_sync_favorites_shows(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.sync import get_sync_favorites_shows
            self._get_sync_favorites_shows = get_sync_favorites_shows
            return self._get_sync_favorites_shows(self, *args, **kwargs)

    def get_sync_ratings_movies(self, *args, **kwargs):
        try:
            return self._get_sync_ratings_movies(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.sync import get_sync_ratings_movies
            self._get_sync_ratings_movies = get_sync_ratings_movies
            return self._get_sync_ratings_movies(self, *args, **kwargs)

    def get_sync_ratings_shows(self, *args, **kwargs):
        try:
            return self._get_sync_ratings_shows(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.sync import get_sync_ratings_shows
            self._get_sync_ratings_shows = get_sync_ratings_shows
            return self._get_sync_ratings_shows(self, *args, **kwargs)

    def get_sync_ratings_seasons(self, *args, **kwargs):
        try:
            return self._get_sync_ratings_seasons(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.sync import get_sync_ratings_seasons
            self._get_sync_ratings_seasons = get_sync_ratings_seasons
            return self._get_sync_ratings_seasons(self, *args, **kwargs)

    def get_sync_ratings_episodes(self, *args, **kwargs):
        try:
            return self._get_sync_ratings_episodes(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.sync import get_sync_ratings_episodes
            self._get_sync_ratings_episodes = get_sync_ratings_episodes
            return self._get_sync_ratings_episodes(self, *args, **kwargs)

    def get_sync(self, *args, **kwargs):
        try:
            return self._get_sync(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.sync import get_sync
            self._get_sync = get_sync
            return self._get_sync(self, *args, **kwargs)

    """
    TRAKT ACTIVITIES METHODS
    """

    def get_last_activity(self, *args, **kwargs):
        try:
            return self._get_last_activity(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.activities import get_last_activity
            self._get_last_activity = get_last_activity
            return self._get_last_activity(self, *args, **kwargs)

    """
    TRAKT PROGRESS METHODS
    """

    def get_ondeck_list(self, *args, **kwargs):
        try:
            return self._get_ondeck_list(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.progress import get_ondeck_list
            self._get_ondeck_list = get_ondeck_list
            return self._get_ondeck_list(self, *args, **kwargs)

    def get_towatch_list(self, *args, **kwargs):
        try:
            return self._get_towatch_list(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.progress import get_towatch_list
            self._get_towatch_list = get_towatch_list
            return self._get_towatch_list(self, *args, **kwargs)

    def get_inprogress_items(self, *args, **kwargs):
        try:
            return self._get_inprogress_items(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.progress import get_inprogress_items
            self._get_inprogress_items = get_inprogress_items
            return self._get_inprogress_items(self, *args, **kwargs)

    def get_inprogress_shows_list(self, *args, **kwargs):
        try:
            return self._get_inprogress_shows_list(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.progress import get_inprogress_shows_list
            self._get_inprogress_shows_list = get_inprogress_shows_list
            return self._get_inprogress_shows_list(self, *args, **kwargs)

    def get_inprogress_shows(self, *args, **kwargs):
        try:
            return self._get_inprogress_shows(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.progress import get_inprogress_shows
            self._get_inprogress_shows = get_inprogress_shows
            return self._get_inprogress_shows(self, *args, **kwargs)

    def is_inprogress_show(self, *args, **kwargs):
        try:
            return self._is_inprogress_show(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.progress import is_inprogress_show
            self._is_inprogress_show = is_inprogress_show
            return self._is_inprogress_show(self, *args, **kwargs)

    def get_episodes_watchcount(self, *args, **kwargs):
        try:
            return self._get_episodes_watchcount(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.progress import get_episodes_watchcount
            self._get_episodes_watchcount = get_episodes_watchcount
            return self._get_episodes_watchcount(self, *args, **kwargs)

    def get_hiddenitems(self, *args, **kwargs):
        try:
            return self._get_hiddenitems(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.progress import get_hiddenitems
            self._get_hiddenitems = get_hiddenitems
            return self._get_hiddenitems(self, *args, **kwargs)

    def get_upnext_list(self, *args, **kwargs):
        try:
            return self._get_upnext_list(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.progress import get_upnext_list
            self._get_upnext_list = get_upnext_list
            return self._get_upnext_list(self, *args, **kwargs)

    def get_upnext_episodes_list(self, *args, **kwargs):
        try:
            return self._get_upnext_episodes_list(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.progress import get_upnext_episodes_list
            self._get_upnext_episodes_list = get_upnext_episodes_list
            return self._get_upnext_episodes_list(self, *args, **kwargs)

    def get_upnext_episodes_listitems(self, *args, **kwargs):
        try:
            return self._get_upnext_episodes_listitems(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.progress import get_upnext_episodes_listitems
            self._get_upnext_episodes_listitems = get_upnext_episodes_listitems
            return self._get_upnext_episodes_listitems(self, *args, **kwargs)

    def get_show_progress(self, *args, **kwargs):
        try:
            return self._get_show_progress(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.progress import get_show_progress
            self._get_show_progress = get_show_progress
            return self._get_show_progress(self, *args, **kwargs)

    def get_upnext_episodes(self, *args, **kwargs):
        try:
            return self._get_upnext_episodes(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.progress import get_upnext_episodes
            self._get_upnext_episodes = get_upnext_episodes
            return self._get_upnext_episodes(self, *args, **kwargs)

    def get_movie_playcount(self, *args, **kwargs):
        try:
            return self._get_movie_playcount(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.progress import get_movie_playcount
            self._get_movie_playcount = get_movie_playcount
            return self._get_movie_playcount(self, *args, **kwargs)

    def get_movie_playprogress(self, *args, **kwargs):
        try:
            return self._get_movie_playprogress(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.progress import get_movie_playprogress
            self._get_movie_playprogress = get_movie_playprogress
            return self._get_movie_playprogress(self, *args, **kwargs)

    def get_episode_playprogress_list(self, *args, **kwargs):
        try:
            return self._get_episode_playprogress_list(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.progress import get_episode_playprogress_list
            self._get_episode_playprogress_list = get_episode_playprogress_list
            return self._get_episode_playprogress_list(self, *args, **kwargs)

    def get_episode_playprogress(self, *args, **kwargs):
        try:
            return self._get_episode_playprogress(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.progress import get_episode_playprogress
            self._get_episode_playprogress = get_episode_playprogress
            return self._get_episode_playprogress(self, *args, **kwargs)

    def get_episode_playcount(self, *args, **kwargs):
        try:
            return self._get_episode_playcount(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.progress import get_episode_playcount
            self._get_episode_playcount = get_episode_playcount
            return self._get_episode_playcount(self, *args, **kwargs)

    def get_episodes_airedcount(self, *args, **kwargs):
        try:
            return self._get_episodes_airedcount(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.progress import get_episodes_airedcount
            self._get_episodes_airedcount = get_episodes_airedcount
            return self._get_episodes_airedcount(self, *args, **kwargs)

    def get_season_episodes_airedcount(self, *args, **kwargs):
        try:
            return self._get_season_episodes_airedcount(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.progress import get_season_episodes_airedcount
            self._get_season_episodes_airedcount = get_season_episodes_airedcount
            return self._get_season_episodes_airedcount(self, *args, **kwargs)

    """
    TRAKT CALENDAR METHODS
    """

    def get_calendar(self, *args, **kwargs):
        try:
            return self._get_calendar(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.calendar import get_calendar
            self._get_calendar = get_calendar
            return self._get_calendar(self, *args, **kwargs)

    def get_calendar_episodes(self, *args, **kwargs):
        try:
            return self._get_calendar_episodes(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.calendar import get_calendar_episodes
            self._get_calendar_episodes = get_calendar_episodes
            return self._get_calendar_episodes(self, *args, **kwargs)

    def get_calendar_episode_item(self, *args, **kwargs):
        try:
            return self._get_calendar_episode_item(*args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.calendar import get_calendar_episode_item
            self._get_calendar_episode_item = get_calendar_episode_item
            return self._get_calendar_episode_item(*args, **kwargs)

    def get_calendar_episode_item_bool(self, *args, **kwargs):
        try:
            return self._get_calendar_episode_item_bool(*args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.calendar import get_calendar_episode_item_bool
            self._get_calendar_episode_item_bool = get_calendar_episode_item_bool
            return self._get_calendar_episode_item_bool(*args, **kwargs)

    def get_stacked_item(self, *args, **kwargs):
        try:
            return self._get_stacked_item(*args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.calendar import get_stacked_item
            self._get_stacked_item = get_stacked_item
            return self._get_stacked_item(*args, **kwargs)

    def stack_calendar_episodes(self, *args, **kwargs):
        try:
            return self._stack_calendar_episodes(*args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.calendar import stack_calendar_episodes
            self._stack_calendar_episodes = stack_calendar_episodes
            return self._stack_calendar_episodes(*args, **kwargs)

    def stack_calendar_tvshows(self, *args, **kwargs):
        try:
            return self._stack_calendar_tvshows(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.calendar import stack_calendar_tvshows
            self._stack_calendar_tvshows = stack_calendar_tvshows
            return self._stack_calendar_tvshows(self, *args, **kwargs)

    def get_calendar_episodes_listitems(self, *args, **kwargs):
        try:
            return self._get_calendar_episodes_listitems(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.calendar import get_calendar_episodes_listitems
            self._get_calendar_episodes_listitems = get_calendar_episodes_listitems
            return self._get_calendar_episodes_listitems(self, *args, **kwargs)

    def get_calendar_episodes_list(self, *args, **kwargs):
        try:
            return self._get_calendar_episodes_list(self, *args, **kwargs)
        except AttributeError:
            from tmdbhelper.lib.api.trakt.methods.calendar import get_calendar_episodes_list
            self._get_calendar_episodes_list = get_calendar_episodes_list
            return self._get_calendar_episodes_list(self, *args, **kwargs)
