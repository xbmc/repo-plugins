import os
import urllib

from ..storage import WatchLaterList, FunctionCache, SearchHistory, FavoriteList, AccessManager
from .abstract_settings import AbstractSettings
from .. import utils


class AbstractContext(object):
    CACHE_ONE_MINUTE = 60
    CACHE_ONE_HOUR = 60 * CACHE_ONE_MINUTE
    CACHE_ONE_DAY = 24 * CACHE_ONE_HOUR
    CACHE_ONE_WEEK = 7 * CACHE_ONE_DAY
    CACHE_ONE_MONTH = 4 * CACHE_ONE_WEEK

    SORT_METHOD_ALBUM = 'album'
    SORT_METHOD_ALBUM_IGNORE_THE = 'album_ignore_the'
    SORT_METHOD_ARTIST = 'artist'
    SORT_METHOD_ARTIST_IGNORE_THE = 'artist_ignore_the'
    SORT_METHOD_BIT_RATE = 'bit_rate'
    SORT_METHOD_CHANNEL = 'channel'
    SORT_METHOD_COUNTRY = 'country'
    SORT_METHOD_DATE = 'date'
    SORT_METHOD_DATE_ADDED = 'date_added'
    SORT_METHOD_DATE_TAKEN = 'date_taken'
    SORT_METHOD_DRIVE_TYPE = 'drive_type'
    SORT_METHOD_DURATION = 'duration'
    SORT_METHOD_EPISODE = 'episode'
    SORT_METHOD_FILE = 'file'
    SORT_METHOD_FULL_PATH = 'full_path'
    SORT_METHOD_GENRE = 'genre'
    SORT_METHOD_LABEL = 'label'
    SORT_METHOD_LABEL_IGNORE_FOLDERS = 'label_ignore_folders'
    SORT_METHOD_LABEL_IGNORE_THE = 'label_ignore_the'
    SORT_METHOD_LAST_PLAYED = 'last_played'
    SORT_METHOD_LISTENERS = 'listeners'
    SORT_METHOD_MPAA_RATING = 'mpaa_rating'
    SORT_METHOD_NONE = 'none'
    SORT_METHOD_PLAY_COUNT = 'play_count'
    SORT_METHOD_PLAYLIST_ORDER = 'playlist_order'
    SORT_METHOD_PRODUCTION_CODE = 'production_code'
    SORT_METHOD_PROGRAM_COUNT = 'program_count'
    SORT_METHOD_SIZE = 'size'
    SORT_METHOD_SONG_RATING = 'song_rating'
    SORT_METHOD_STUDIO = 'studio'
    SORT_METHOD_STUDIO_IGNORE_THE = 'studio_ignore_the'
    SORT_METHOD_TITLE = 'title'
    SORT_METHOD_TITLE_IGNORE_THE = 'title_ignore_the'
    SORT_METHOD_TRACK_NUMBER = 'track_number'
    SORT_METHOD_UNSORTED = 'unsorted'
    SORT_METHOD_VIDEO_RATING = 'video_rating'
    SORT_METHOD_VIDEO_RUNTIME = 'video_runtime'
    SORT_METHOD_VIDEO_SORT_TITLE = 'video_sort_title'
    SORT_METHOD_VIDEO_SORT_TITLE_IGNORE_THE = 'video_sort_title_ignore_the'
    SORT_METHOD_VIDEO_TITLE = 'video_title'
    SORT_METHOD_VIDEO_YEAR = 'video_year'

    CONTENT_TYPE_FILES = 'files'
    CONTENT_TYPE_SONGS = 'songs'
    CONTENT_TYPE_ARTISTS = 'artists'
    CONTENT_TYPE_ALBUMS = 'albums'
    CONTENT_TYPE_MOVIES = 'movies'
    CONTENT_TYPE_TV_SHOWS = 'tvshows'
    CONTENT_TYPE_EPISODES = 'episodes'
    CONTENT_TYPE_MUSIC_VIDEOS = 'musicvideos'

    LOG_DEBUG = 0
    LOG_INFO = 1
    LOG_WARNING = 2
    LOG_ERROR = 3

    def __init__(self, path=u'/', params=None, plugin_name=u'', plugin_id=u''):
        if not params:
            params = {}
            pass

        self._path_match = None
        self._python_version = None
        self._cache_path = None
        self._function_cache = None
        self._search_history = None
        self._favorite_list = None
        self._watch_later_list = None
        self._access_manager = None

        self._plugin_name = unicode(plugin_name)
        self._version = 'UNKNOWN'
        self._plugin_id = plugin_id
        self._path = path
        self._params = params
        self._utils = None
        self._view_mode = None

        # create valid uri
        self._uri = self.create_uri(self._path, self._params)
        pass

    def set_path_match(self, path_match):
        """
        Sets the current regular expression match for a navigated path
        :param path_match: regular expression match
        """
        self._path_match = path_match
        pass

    def get_path_match(self):
        """
        Returns the current path match of regular expression
        :return: match of regular expression
        """
        return self._path_match

    def format_date_short(self, date_obj):
        raise NotImplementedError()

    def format_time(self, time_obj):
        raise NotImplementedError()

    def get_language(self):
        raise NotImplementedError()

    def _get_cache_path(self):
        if not self._cache_path:
            self._cache_path = os.path.join(self.get_data_path(), 'kodion')
            pass
        return self._cache_path

    def get_function_cache(self):
        if not self._function_cache:
            settings = self.get_settings()
            max_cache_size_mb = settings.get_int(AbstractSettings.ADDON_CACHE_SIZE, 5)
            self._function_cache = FunctionCache(os.path.join(self._get_cache_path(), 'cache'),
                                                 max_file_size_kb=max_cache_size_mb * 1024)

            if settings.is_clear_cache_enabled():
                self.log_info('Clearing cache...')
                settings.disable_clear_cache()
                self._function_cache.remove_file()
                self.log_info('Clearing cache done')
                pass
            pass
        return self._function_cache

    def cache_function(self, seconds, func, *args, **keywords):
        return self.get_function_cache().get(seconds, func, *args, **keywords)

    def get_search_history(self):
        if not self._search_history:
            max_search_history_items = self.get_settings().get_int(AbstractSettings.ADDON_SEARCH_SIZE, 50,
                                                                   lambda x: x * 10)
            self._search_history = SearchHistory(os.path.join(self._get_cache_path(), 'search'),
                                                 max_search_history_items)
            pass
        return self._search_history

    def get_favorite_list(self):
        if not self._favorite_list:
            self._favorite_list = FavoriteList(os.path.join(self._get_cache_path(), 'favorites'))
            pass
        return self._favorite_list

    def get_watch_later_list(self):
        if not self._watch_later_list:
            self._watch_later_list = WatchLaterList(os.path.join(self._get_cache_path(), 'watch_later'))
            pass
        return self._watch_later_list

    def get_access_manager(self):
        if not self._access_manager:
            self._access_manager = AccessManager(self.get_settings())
            pass
        return self._access_manager

    def get_video_playlist(self):
        raise NotImplementedError()

    def get_audio_playlist(self):
        raise NotImplementedError()

    def get_video_player(self):
        raise NotImplementedError()

    def get_audio_player(self):
        raise NotImplementedError()

    def get_ui(self):
        raise NotImplementedError()

    def get_system_version(self):
        raise NotImplementedError()

    def get_system_name(self):
        raise NotImplementedError()

    def get_python_version(self):
        if not self._python_version:
            try:
                import platform
                python_version = str(platform.python_version())
                python_version = python_version.split('.')
                self._python_version = tuple(map(lambda x: int(x), python_version))
            except Exception, ex:
                self.log_error('Unable to get the version of python')
                self.log_error(ex.__str__())

                self._python_version = [0, 0]
                pass
            pass

        return self._python_version

    def create_uri(self, path=u'/', params=None):
        if not params:
            params = {}
            pass

        uri_path = utils.path.to_uri(path)
        if uri_path:
            uri = "%s://%s%s" % ('plugin', utils.strings.to_utf8(self._plugin_id), uri_path)
        else:
            uri = "%s://%s/" % ('plugin', utils.strings.to_utf8(self._plugin_id))
            pass

        if len(params) > 0:
            # make a copy of the map
            uri_params = {}
            uri_params.update(params)

            # encode in utf-8
            for param in uri_params:
                uri_params[param] = utils.strings.to_utf8(params[param])
                pass
            uri += '?' + urllib.urlencode(uri_params)
            pass

        return uri

    def get_path(self):
        return self._path

    def get_params(self):
        return self._params

    def get_param(self, name, default=None):
        return self.get_params().get(name, default)

    def get_data_path(self):
        """
        Returns the path for read/write nightcrawler of files
        :return:
        """
        raise NotImplementedError()

    def get_native_path(self):
        raise NotImplementedError()

    def get_icon(self):
        return os.path.join(self.get_native_path(), 'icon.png')

    def get_fanart(self):
        return os.path.join(self.get_native_path(), 'fanart.jpg')

    def create_resource_path(self, relative_path):
        relative_path = utils.path.normalize(relative_path)
        path_comps = relative_path.split('/')
        return os.path.join(self.get_native_path(), 'resources', *path_comps)

    def get_uri(self):
        return self._uri

    def get_name(self):
        return self._plugin_name

    def get_version(self):
        return self._version

    def get_id(self):
        return self._plugin_id

    def get_handle(self):
        raise NotImplementedError()

    def get_settings(self):
        raise NotImplementedError()

    def localize(self, text_id, default=u''):
        raise NotImplementedError()

    def set_content_type(self, content_type):
        raise NotImplementedError()

    def add_sort_method(self, *sort_methods):
        raise NotImplementedError()

    def log(self, text, log_level):
        raise NotImplementedError()

    def log_debug(self, text):
        self.log(text, self.LOG_DEBUG)
        pass

    def log_info(self, text):
        self.log(text, self.LOG_INFO)
        pass

    def log_warning(self, text):
        self.log(text, self.LOG_WARNING)
        pass

    def log_error(self, text):
        self.log(text, self.LOG_ERROR)
        pass

    def clone(self, new_path=None, new_params=None):
        raise NotImplementedError()

    def execute(self, command):
        raise NotImplementedError()

    def sleep(self, milli_seconds):
        raise NotImplementedError()

    def resolve_item(self, item):
        raise NotImplementedError()

    def add_item(self, item):
        raise NotImplementedError()

    def end_of_content(self, succeeded=True):
        raise NotImplementedError()