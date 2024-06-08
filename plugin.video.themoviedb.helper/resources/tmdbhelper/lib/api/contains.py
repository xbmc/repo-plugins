class CommonContainerAPIs():
    @property
    def page_length(self):
        return 1

    @property
    def ftv_is_cache_only(self):
        return False

    @property
    def all_awards(self):
        try:
            return self._all_awards
        except AttributeError:
            self._all_awards = self.get_awards_data()
            return self._all_awards

    @property
    def trakt_api(self):
        try:
            return self._trakt_api
        except AttributeError:
            from tmdbhelper.lib.api.trakt.api import TraktAPI
            self._trakt_api = TraktAPI(page_length=self.page_length)
            return self._trakt_api

    @property
    def tmdb_api(self):
        try:
            return self._tmdb_api
        except AttributeError:
            from tmdbhelper.lib.api.tmdb.api import TMDb
            self._tmdb_api = TMDb(page_length=self.page_length)
            return self._tmdb_api

    @property
    def ftv_api(self):
        try:
            return self._ftv_api
        except AttributeError:
            from tmdbhelper.lib.api.fanarttv.api import FanartTV
            self._ftv_api = FanartTV(cache_only=self.ftv_is_cache_only)
            return self._ftv_api

    @property
    def tvdb_api(self):
        try:
            return self._tvdb_api
        except AttributeError:
            from tmdbhelper.lib.api.tvdb.api import TVDb
            self._tvdb_api = TVDb()
            return self._tvdb_api

    @property
    def omdb_api(self):
        try:
            return self._omdb_api
        except AttributeError:
            from tmdbhelper.lib.api.omdb.api import OMDb
            from tmdbhelper.lib.addon.plugin import get_setting
            self._omdb_api = OMDb() if get_setting('omdb_apikey', 'str') else None
            return self._omdb_api

    @property
    def mdblist_api(self):
        try:
            return self._mdblist_api
        except AttributeError:
            from tmdbhelper.lib.api.mdblist.api import MDbList
            from tmdbhelper.lib.addon.plugin import get_setting
            self._mdblist_api = MDbList() if get_setting('mdblist_apikey', 'str') else None
            return self._mdblist_api
