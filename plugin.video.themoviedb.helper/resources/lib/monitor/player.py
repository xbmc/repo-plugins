import xbmc
import resources.lib.kodi.rpc as rpc
from resources.lib.addon.window import get_property
from resources.lib.monitor.common import CommonMonitorFunctions, SETPROP_RATINGS, SETMAIN_ARTWORK
from resources.lib.addon.plugin import ADDON
from json import loads


class PlayerMonitor(xbmc.Player, CommonMonitorFunctions):
    def __init__(self):
        xbmc.Player.__init__(self)
        CommonMonitorFunctions.__init__(self)
        self.playerstring = None
        self.property_prefix = 'Player'
        self.reset_properties()

    def onAVStarted(self):
        self.reset_properties()
        self.get_playingitem()

    def onPlayBackEnded(self):
        self.set_watched()
        self.reset_properties()

    def onPlayBackStopped(self):
        self.set_watched()
        self.reset_properties()

    def reset_properties(self):
        self.clear_properties()
        self.properties = set()
        self.index_properties = set()
        self.total_time = 0
        self.current_time = 0
        self.dbtype = None
        self.imdb_id = None
        self.query = None
        self.year = None
        self.season = None
        self.episode = None
        self.dbid = None
        self.tmdb_id = None
        self.details = {}
        self.tmdb_type = None

    def get_playingitem(self):
        if not self.isPlayingVideo():
            return  # Not a video so don't get info
        if self.getVideoInfoTag().getMediaType() not in ['movie', 'episode']:
            return  # Not a movie or episode so don't get info TODO Maybe get PVR details also?
        self.playerstring = get_property('PlayerInfoString')
        self.playerstring = loads(self.playerstring) if self.playerstring else None

        self.total_time = self.getTotalTime()
        self.dbtype = self.getVideoInfoTag().getMediaType()
        self.dbid = self.getVideoInfoTag().getDbId()
        self.imdb_id = self.getVideoInfoTag().getIMDBNumber()
        self.query = self.getVideoInfoTag().getTVShowTitle() if self.dbtype == 'episode' else self.getVideoInfoTag().getTitle()
        self.year = self.getVideoInfoTag().getYear() if self.dbtype == 'movie' else None
        self.epyear = self.getVideoInfoTag().getYear() if self.dbtype == 'episodes' else None
        self.season = self.getVideoInfoTag().getSeason() if self.dbtype == 'episodes' else None
        self.episode = self.getVideoInfoTag().getEpisode() if self.dbtype == 'episodes' else None

        self.tmdb_type = 'movie' if self.dbtype == 'movie' else 'tv'
        self.tmdb_id = self.get_tmdb_id(self.tmdb_type, self.imdb_id, self.query, self.year, self.epyear)
        self.details = self.tmdb_api.get_details(self.tmdb_type, self.tmdb_id, self.season, self.episode)

        # Clear everything if we didn't get details because nothing to compare
        if not self.details:
            return self.reset_properties()

        # Get ratings (no need for threading since we're only getting one item in player ever)
        if xbmc.getCondVisibility("!Skin.HasSetting(TMDbHelper.DisableRatings)"):
            self.details = self.get_omdb_ratings(self.details)
            if self.tmdb_type == 'movie':
                self.details = self.get_imdb_top250_rank(self.details)
            if self.tmdb_type in ['movie', 'tv']:
                self.details = self.get_trakt_ratings(
                    self.details, 'movie' if self.tmdb_type == 'movie' else 'show',
                    season=self.season, episode=self.episode)
            self.set_iter_properties(self.details.get('infoproperties', {}), SETPROP_RATINGS)

        # Get artwork (no need for threading since we're only getting one item in player ever)
        # No need for merging Kodi DB artwork as we should have access to that via normal player properties
        if xbmc.getCondVisibility("!Skin.HasSetting(TMDbHelper.DisableArtwork)"):
            if ADDON.getSettingBool('service_fanarttv_lookup'):
                self.details = self.get_fanarttv_artwork(self.details, self.tmdb_type)
            self.set_iter_properties(self.details, SETMAIN_ARTWORK)

        self.set_properties(self.details)

    def set_watched(self):
        if not self.playerstring or not self.playerstring.get('tmdb_id'):
            return
        if not self.current_time or not self.total_time:
            return
        if u'{}'.format(self.playerstring.get('tmdb_id')) != u'{}'.format(self.details.get('unique_ids', {}).get('tmdb')):
            return  # Item in the player doesn't match so don't mark as watched

        # Only update if progress is 75% or more
        progress = ((self.current_time / self.total_time) * 100)
        if progress < 75:
            return

        if self.playerstring.get('tmdb_type') == 'episode':
            tvshowid = rpc.KodiLibrary('tvshow').get_info(
                info='dbid',
                imdb_id=self.playerstring.get('imdb_id'),
                tmdb_id=self.playerstring.get('tmdb_id'),
                tvdb_id=self.playerstring.get('tvdb_id'))
            if not tvshowid:
                return
            dbid = rpc.KodiLibrary('episode', tvshowid).get_info(
                info='dbid',
                season=self.playerstring.get('season'),
                episode=self.playerstring.get('episode'))
            if not dbid:
                return
            rpc.set_watched(dbid=dbid, dbtype='episode')
        elif self.playerstring.get('tmdb_type') == 'movie':
            dbid = rpc.KodiLibrary('movie').get_info(
                info='dbid',
                imdb_id=self.playerstring.get('imdb_id'),
                tmdb_id=self.playerstring.get('tmdb_id'),
                tvdb_id=self.playerstring.get('tvdb_id'))
            if not dbid:
                return
            rpc.set_watched(dbid=dbid, dbtype='movie')
