from xbmcgui import DialogProgressBG
from tmdbhelper.lib.update.userlist import get_monitor_userlists
from tmdbhelper.lib.addon.logger import kodi_log
from tmdbhelper.lib.addon.plugin import get_localized
from tmdbhelper.lib.api.kodi.rpc import get_kodi_library, set_tags
from tmdbhelper.lib.update.common import LibraryCommonFunctions
from tmdbhelper.lib.update.logger import _LibraryLogger
from tmdbhelper.lib.update.update import create_playlist


class LibraryTagger(LibraryCommonFunctions):
    def __init__(self, busy_spinner=True):
        self.kodi_db_movies = get_kodi_library('movie', cache_refresh=True)
        self.kodi_db_tv = get_kodi_library('tv', cache_refresh=True)
        self.p_dialog = DialogProgressBG() if busy_spinner else None
        self._log = _LibraryLogger(log_folder='log_tagger')
        self.clean_library = False
        self.auto_update = False
        self.debug_logging = True
        self._msg_start = f'{get_localized(32167)}...'
        self._msg_title = 'TMDbHelper Tagger'

    def add_item(self, item_type, database, user_slug, list_slug, tmdb_id=None, imdb_id=None, **kwargs):
        if not tmdb_id:
            return

        # Check item in library
        dbid = database.get_info(info='dbid', imdb_id=imdb_id, tmdb_id=tmdb_id)
        if not dbid:
            self._log._add(item_type, tmdb_id, 'missing from library', user_slug=user_slug, list_slug=list_slug)
            return

        set_tags(dbid, item_type, [f'Trakt User {user_slug}', f'Trakt List {list_slug}'])

        self._log._add(item_type, tmdb_id, 'in library', user_slug=user_slug, list_slug=list_slug)

    def add_movie(self, tmdb_id=None, imdb_id=None, user_slug=None, list_slug=None, **kwargs):
        self.add_item('movie', self.kodi_db_movies, user_slug, list_slug, tmdb_id, imdb_id, **kwargs)

    def add_tvshow(self, tmdb_id=None, imdb_id=None, user_slug=None, list_slug=None, **kwargs):
        self.add_item('tvshow', self.kodi_db_tv, user_slug, list_slug, tmdb_id, imdb_id, **kwargs)

    def update_tags(self, list_slugs=None, user_slugs=None):
        user_lists = get_monitor_userlists(list_slugs, user_slugs)

        if not user_lists:
            return

        kodi_log(u'UPDATING LIBRARY TAGS', 1)

        # Update library tags according to Trakt list names
        for list_slug, user_slug in user_lists:
            self.add_userlist(user_slug=user_slug, list_slug=list_slug, confirm=False)
            create_playlist('movies', user_slug, list_slug)
            create_playlist('tvshows', user_slug, list_slug)

    def run(self):
        self._start()
        self.update_tags()
        self._finish()
