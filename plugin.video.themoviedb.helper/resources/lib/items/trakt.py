from resources.lib.addon.parser import try_int

""" Lazyimports """
from resources.lib.addon.modimp import lazyimport
set_playprogress = None


class TraktMethods():
    def __init__(self, trakt, pauseplayprogress=False, watchedindicators=False, unwatchedepisodes=False):
        self._trakt = trakt
        self._pauseplayprogress = pauseplayprogress  # Set play progress using paused at position
        self._watchedindicators = watchedindicators  # Set watched status and playcount
        self._unwatchedepisodes = unwatchedepisodes  # Set unwatched episode count to total episode count for unwatched tvshows
        if pauseplayprogress:
            lazyimport(globals(), 'resources.lib.api.kodi.rpc', import_attr="set_playprogress")

    def set_playprogress(self, li):
        def _set_playprogress():
            if li.infolabels.get('mediatype') == 'movie':
                return self._trakt.get_movie_playprogress(
                    id_type='tmdb',
                    unique_id=try_int(li.unique_ids.get('tmdb')))
            return self._trakt.get_episode_playprogress(
                id_type='tmdb',
                unique_id=try_int(li.unique_ids.get('tvshow.tmdb')),
                season=li.infolabels.get('season'),
                episode=li.infolabels.get('episode'))
        if not self._pauseplayprogress:
            return
        if li.infolabels.get('mediatype') not in ['movie', 'episode']:
            return
        duration = li.infolabels.get('duration')
        if not duration:
            return
        progress = _set_playprogress()
        if not progress or progress < 4 or progress > 96:
            progress = 0
        li.infoproperties['ResumeTime'] = int(duration * progress // 100)
        li.infoproperties['TotalTime'] = int(duration)
        set_playprogress(li.get_url(), li.infoproperties['ResumeTime'], li.infoproperties['TotalTime'])

    def pre_sync(self, info=None, tmdb_id=None, tmdb_type=None, season=-2, **kwargs):
        info_movies = ['stars_in_movies', 'crew_in_movies', 'trakt_userlist']
        if tmdb_type in ['movie', 'both'] or info in info_movies:
            if self._watchedindicators:
                self._trakt.get_sync('watched', 'movie', 'tmdb')
            if self._pauseplayprogress:
                self._trakt.get_sync('playback', 'movie', 'tmdb')

        info_tvshow = ['stars_in_tvshows', 'crew_in_tvshows', 'trakt_userlist', 'trakt_calendar']
        if tmdb_type in ['tv', 'season', 'both'] or info in info_tvshow:
            tmdbid = try_int(tmdb_id, fallback=None)
            season = try_int(season, fallback=-2)  # Use -2 to force all seasons lookup data on Trakt at seasons level
            if self._watchedindicators:
                self._trakt.get_sync('watched', 'show', 'tmdb')
                if tmdbid:
                    self._trakt.get_episodes_airedcount(id_type='tmdb', unique_id=tmdbid, season=season)
                    self._trakt.get_episodes_watchcount(id_type='tmdb', unique_id=tmdbid, season=season)
            if self._pauseplayprogress and tmdbid and season != -2:
                self._trakt.get_sync('playback', 'show', 'tmdb')

    def get_playcount(self, li):
        if not self._watchedindicators:
            return
        if li.infolabels.get('mediatype') == 'movie':
            return self._trakt.get_movie_playcount(
                id_type='tmdb',
                unique_id=try_int(li.unique_ids.get('tmdb'))) or 0
        if li.infolabels.get('mediatype') == 'episode':
            return self._trakt.get_episode_playcount(
                id_type='tmdb',
                unique_id=try_int(li.unique_ids.get('tvshow.tmdb')),
                season=li.infolabels.get('season'),
                episode=li.infolabels.get('episode')) or 0
        if li.infolabels.get('mediatype') == 'tvshow':
            air_count = self._trakt.get_episodes_airedcount(
                id_type='tmdb',
                unique_id=try_int(li.unique_ids.get('tmdb')))
            if not air_count:
                return None if self._unwatchedepisodes else 0
            li.infolabels['episode'] = air_count
            return self._trakt.get_episodes_watchcount(
                id_type='tmdb',
                unique_id=try_int(li.unique_ids.get('tmdb'))) or 0
        if li.infolabels.get('mediatype') == 'season':
            air_count = self._trakt.get_episodes_airedcount(
                id_type='tmdb',
                unique_id=try_int(li.unique_ids.get('tvshow.tmdb') or li.unique_ids.get('tmdb')),
                season=li.infolabels.get('season'))
            if not air_count:
                return None if self._unwatchedepisodes else 0
            li.infolabels['episode'] = air_count
            return self._trakt.get_episodes_watchcount(
                id_type='tmdb',
                unique_id=try_int(li.unique_ids.get('tvshow.tmdb') or li.unique_ids.get('tmdb')),
                season=li.infolabels.get('season')) or 0
