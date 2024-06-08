from xbmc import Player
from jurialmunkey.parser import boolean
from jurialmunkey.window import get_property
from tmdbhelper.lib.monitor.common import CommonMonitorFunctions, SETPROP_RATINGS, SETMAIN_ARTWORK
from tmdbhelper.lib.addon.plugin import get_condvisibility, get_infolabel


class PlayerMonitor(Player, CommonMonitorFunctions):
    def __init__(self):
        Player.__init__(self)
        CommonMonitorFunctions.__init__(self)
        self.playerstring = None
        self.property_prefix = 'Player'
        self.reset_properties()

    def onAVStarted(self):
        self.get_playingitem()

    def onAVChange(self):
        self.get_playingitem()

    def onPlayBackEnded(self):
        self.set_watched()
        self.reset_properties()
        self.set_trakt_properties()

    def onPlayBackStopped(self):
        self.set_watched()
        self.reset_properties()
        self.set_trakt_properties()

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
        self.previous_item = None
        self.current_item = None

    def set_trakt_properties(self):
        if not boolean(get_property('TraktIsAuth')):
            return
        from tmdbhelper.lib.script.method.trakt import get_stats
        from tmdbhelper.lib.api.trakt.methods.activities import del_lastactivities_expiry
        del_lastactivities_expiry()
        get_stats()

    def get_playingitem(self):
        if not self.isPlayingVideo():
            return self.reset_properties()  # Not a video so don't get info
        info_tag = self.getVideoInfoTag()
        if info_tag.getMediaType() not in ['movie', 'episode']:
            return self.reset_properties()  # Not a movie or episode so don't get info TODO Maybe get PVR details also?
        self.playingfile = self.getPlayingFile()
        if self.playingfile and self.playingfile.endswith('dummy.mp4'):
            return self.reset_properties()  # Resolved to dummy so wait
        self.playerstring = get_property('PlayerInfoString')

        from json import loads
        self.playerstring = loads(self.playerstring) if self.playerstring else None

        self.total_time = self.getTotalTime()
        self.dbtype = info_tag.getMediaType()
        self.dbid = info_tag.getDbId()
        self.imdb_id = info_tag.getIMDBNumber() if self.dbtype == 'movie' else None
        self.query = info_tag.getTVShowTitle() if self.dbtype == 'episode' else info_tag.getTitle()
        self.year = info_tag.getYear() if self.dbtype == 'movie' else None
        self.epyear = info_tag.getYear() if self.dbtype == 'episode' else None
        self.season = info_tag.getSeason() if self.dbtype == 'episode' else None
        self.episode = info_tag.getEpisode() if self.dbtype == 'episode' else None

        if self.dbtype == 'episode':
            show_tmdb_id = info_tag.getUniqueID('tvshow.tmdb')
            if show_tmdb_id:
                self.tmdb_id = show_tmdb_id
            else:
                self.tmdb_id = self.get_tmdb_id_parent(
                    info_tag.getUniqueID('tmdb'), 'episode', season_episode_check=(self.season, self.episode,))
        else:
            self.tmdb_id = info_tag.getUniqueID('tmdb')

        self.current_item = (self.total_time, self.dbtype, self.dbid, self.imdb_id, self.query, self.year, self.epyear, self.season, self.episode, )
        if self.previous_item and self.current_item == self.previous_item:
            return  # Dont reset the same item again
        self.previous_item = self.current_item  # Store for next time

        self.tmdb_type = 'movie' if self.dbtype == 'movie' else 'tv'
        self.tmdb_id = self.tmdb_id or self.get_tmdb_id(self.tmdb_type, self.imdb_id, self.query, self.year, self.epyear)
        self.details = self.ib.get_item(self.tmdb_type, self.tmdb_id, self.season, self.episode)
        self.artwork = self.details['artwork'] if self.details else {}
        self.details = self.details['listitem'] if self.details else {}

        self.clear_properties()

        # Get ratings (no need for threading since we're only getting one item in player ever)
        if self.details and get_condvisibility("!Skin.HasSetting(TMDbHelper.DisableRatings)"):
            try:
                trakt_type = {'movie': 'movie', 'tv': 'show'}[self.tmdb_type]
            except KeyError:
                trakt_type = None
            if trakt_type:
                self.details = self.get_omdb_ratings(self.details)
                self.details = self.get_imdb_top250_rank(self.details, trakt_type=trakt_type)
                self.details = self.get_tvdb_awards(self.details, self.tmdb_type, self.tmdb_id)
                self.details = self.get_trakt_ratings(self.details, trakt_type, season=self.season, episode=self.episode)
                self.details = self.get_mdblist_ratings(self.details, trakt_type, tmdb_id=self.tmdb_id)
            self.set_iter_properties(self.details.get('infoproperties', {}), SETPROP_RATINGS)

        # Get artwork (no need for threading since we're only getting one item in player ever)
        # No need for merging Kodi DB artwork as we should have access to that via normal player properties
        if get_condvisibility("!Skin.HasSetting(TMDbHelper.DisableArtwork)"):
            if self.artwork:
                self.details['art'] = self.ib.get_item_artwork(self.artwork, is_season=True if self.season else False)
            if get_condvisibility("Skin.HasSetting(TMDbHelper.EnableCrop)"):
                art = self.details.get('art', {})
                org_logos = (
                    get_infolabel('Window(Home).Property(TMDbHelper.ListItem.CropImage.Original)'),
                    get_infolabel('Window(Home).Property(TMDbHelper.Player.CropImage.Original)'),)
                tmdb_logo = art.get('artist.clearlogo') or art.get('tvshow.clearlogo') or art.get('clearlogo')
                clearlogo = tmdb_logo if tmdb_logo and tmdb_logo in org_logos else (
                    get_infolabel('Player.Art(artist.clearlogo)')
                    or get_infolabel('Player.Art(tvshow.clearlogo)')
                    or get_infolabel('Player.Art(clearlogo)')
                    or tmdb_logo)
                from tmdbhelper.lib.monitor.images import ImageFunctions
                ImageFunctions(method='crop', is_thread=False, prefix='Player', artwork=clearlogo).run()
                self.properties.add('CropImage')
                self.properties.add('CropImage.Original')
            self.set_iter_properties(self.details.get('art', {}), SETMAIN_ARTWORK)

        self.set_properties(self.details)

    def set_watched(self):
        if not self.playerstring or not self.playerstring.get('tmdb_id'):
            return
        if not self.current_time or not self.total_time:
            return
        if f'{self.playerstring.get("tmdb_id")}' != f'{self.details.get("unique_ids", {}).get("tmdb")}':
            return  # Item in the player doesn't match so don't mark as watched

        # Only update if progress is 75% or more
        progress = ((self.current_time / self.total_time) * 100)
        if progress < 75:
            return

        import tmdbhelper.lib.api.kodi.rpc as rpc

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
