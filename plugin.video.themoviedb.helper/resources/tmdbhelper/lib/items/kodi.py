from tmdbhelper.lib.api.mapping import set_show, get_empty_item
from tmdbhelper.lib.api.kodi.rpc import get_kodi_library, get_movie_details, get_tvshow_details, get_episode_details, get_season_details


class KodiDb():
    def __init__(self, tmdb_type):
        self.kodi_db_tv = {}
        self.kodi_db = get_kodi_library(tmdb_type)

    def get_kodi_details(self, li):
        """ Pass through listitem to get Kodi details """

        def _get_dbid():
            """ Get dbid for movie / tvshow """
            return self.kodi_db.get_info(
                info='dbid',
                imdb_id=li.unique_ids.get('imdb'),
                tmdb_id=li.unique_ids.get('tmdb'),
                tvdb_id=li.unique_ids.get('tvdb'),
                originaltitle=li.infolabels.get('originaltitle'),
                title=li.infolabels.get('title'),
                year=li.infolabels.get('year'))

        def _get_tvshow_dbid():
            """ Get dbid for parent tvshow """
            return self.kodi_db.get_info(
                info='dbid',
                imdb_id=li.unique_ids.get('tvshow.imdb'),
                tmdb_id=li.unique_ids.get('tvshow.tmdb'),
                tvdb_id=li.unique_ids.get('tvshow.tvdb'),
                title=li.infolabels.get('tvshowtitle'))

        def _get_child_details():
            season, episode = li.infolabels.get('season'), li.infolabels.get('episode')

            library, func = 'season', get_season_details
            if episode is not None:
                library, func = 'episode', get_episode_details

            kodi_db_tv = self.kodi_db_tv.setdefault(dbid, get_kodi_library(library, dbid))
            child_dbid = kodi_db_tv.get_info('dbid', season=season, episode=episode)
            if not child_dbid:
                return

            details = func(child_dbid)
            details['infoproperties']['tvshow.dbid'] = dbid
            return details

        if not self.kodi_db:
            return

        routes = {
            'movie': {
                'get_dbid': _get_dbid,
                'get_details': get_movie_details},
            'tvshow': {
                'get_dbid': _get_dbid,
                'get_details': get_tvshow_details},
            'season': {
                'get_dbid': _get_tvshow_dbid,
                'get_details': lambda x: set_show(_get_child_details() or get_empty_item(), get_tvshow_details(x))},
            'episode': {
                'get_dbid': _get_tvshow_dbid,
                'get_details': lambda x: set_show(_get_child_details() or get_empty_item(), get_tvshow_details(x))}}
        try:
            route = routes[li.infolabels['mediatype']]
        except KeyError:
            return

        dbid = route['get_dbid']()
        if not dbid:
            return
        return route['get_details'](dbid)
