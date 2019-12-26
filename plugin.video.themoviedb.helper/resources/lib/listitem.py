import xbmcgui
import xbmcaddon
import xbmcplugin
import resources.lib.utils as utils
from resources.lib.kodilibrary import KodiLibrary

try:
    from urllib.parse import urlencode  # Py3
except ImportError:
    from urllib import urlencode  # Py2


class ListItem(object):
    def __init__(self, label=None, label2=None, dbtype=None, library=None, tmdb_id=None, imdb_id=None, dbid=None, tvdb_id=None,
                 cast=None, infolabels=None, infoproperties=None, poster=None, thumb=None, icon=None, fanart=None, nextpage=None,
                 streamdetails=None, clearlogo=None, clearart=None, banner=None, landscape=None, mixed_type=None, url=None, is_folder=True):
        self.addon = xbmcaddon.Addon()
        self.addonpath = self.addon.getAddonInfo('path')
        self.select_action = self.addon.getSettingInt('select_action')
        self.label = label or 'N/A'
        self.label2 = label2 or ''
        self.library = library or ''  # <content target= video, music, pictures, none>
        self.tmdb_id = tmdb_id or ''  # ListItem.Property(tmdb_id)
        self.imdb_id = imdb_id or ''  # IMDb ID for item
        self.tvdb_id = tvdb_id or ''  # IMDb ID for item
        self.poster, self.thumb = poster, thumb
        self.clearlogo, self.clearart, self.banner, self.landscape = clearlogo, clearart, banner, landscape
        self.url = url or {}
        self.mixed_type = mixed_type or ''
        self.streamdetails = streamdetails or {}
        self.icon = icon or '{0}/resources/poster.png'.format(self.addonpath)
        self.fanart = fanart or '{0}/fanart.jpg'.format(self.addonpath)
        self.cast = cast or []  # Cast list
        self.is_folder = is_folder
        self.infolabels = infolabels or {}  # ListItem.Foobar
        self.infoproperties = infoproperties or {}  # ListItem.Property(Foobar)
        self.dbid = dbid
        self.nextpage = nextpage

    def set_url(self, **kwargs):
        url = kwargs.pop('url', 'plugin://plugin.video.themoviedb.helper/?')
        return u'{0}{1}'.format(url, urlencode(kwargs))

    def get_url(self, url, url_tmdb_id=None, widget=None, fanarttv=None, nextpage=None, extended=None):
        self.url = self.url or url.copy()
        self.url['tmdb_id'] = self.tmdb_id = url_tmdb_id or self.tmdb_id
        if self.mixed_type:
            self.url['type'] = self.mixed_type
            self.infolabels['mediatype'] = utils.type_convert(self.mixed_type, 'dbtype')
        if self.label == 'Next Page':
            self.infolabels['mediatype'] = ''
        if self.infolabels.get('mediatype') in ['season', 'episode']:
            self.url['season'] = self.infolabels.get('season')
        if self.infolabels.get('mediatype') == 'episode':
            self.url['episode'] = self.infolabels.get('episode')
        if fanarttv:
            self.url['fanarttv'] = fanarttv
        if nextpage:
            self.url['nextpage'] = nextpage
        if widget:
            self.url['widget'] = widget
        if not extended and (self.url.get('widget', '').capitalize() == 'True' or self.select_action):
            if self.infolabels.get('mediatype') in ['movie', 'episode']:
                self.url['info'] = 'play'
            elif self.infolabels.get('mediatype') == 'tvshow':
                self.url['info'] = 'seasons'
        self.is_folder = False if self.url.get('info') in ['play', 'textviewer', 'imageviewer'] else True
        # self.infoproperties['isPlayable'] = 'True' if self.url.get('info') in ['play', 'textviewer', 'imageviewer'] else 'False'

    def get_extra_artwork(self, tmdb=None, fanarttv=None):
        if not fanarttv:
            return

        artwork = None

        if self.infolabels.get('mediatype') == 'tvshow' and (self.tvdb_id or tmdb):
            self.tvdb_id = self.tvdb_id or tmdb.get_item_externalid('tv', self.tmdb_id, 'tvdb_id')
            artwork = fanarttv.get_tvshow_allart_lc(self.tvdb_id)

        elif self.infolabels.get('mediatype') == 'movie':
            artwork = fanarttv.get_movie_allart_lc(self.tmdb_id)

        if artwork:
            self.clearart = self.clearart or artwork.get('clearart')
            self.clearlogo = self.clearlogo or artwork.get('clearlogo')
            self.landscape = self.landscape or artwork.get('landscape')
            self.banner = self.banner or artwork.get('banner')
            self.fanart = self.fanart or artwork.get('fanart')

    def get_trakt_unwatched(self, trakt=None, request=None, check_sync=True):
        if not trakt or request == -1:
            return

        season = self.infolabels.get('season') if self.infolabels.get('mediatype') == 'season' else None
        count = trakt.get_unwatched_count(tmdb_id=utils.try_parse_int(self.tmdb_id), season=season, request=request, check_sync=check_sync)

        if count == -1:
            return

        self.infoproperties['UnWatchedEpisodes'] = count

        if count == 0:
            self.infolabels['playcount'] = 1
            self.infolabels['overlay'] = 5

    def get_trakt_watched(self, trakt_watched=None):
        if not trakt_watched:
            return

        key = 'movie' if self.infolabels.get('mediatype') == 'movie' else 'show'
        item = utils.get_dict_in_list(trakt_watched, 'tmdb', utils.try_parse_int(self.tmdb_id), [key, 'ids'])
        if not item:
            return

        if self.infolabels.get('mediatype') == 'episode':
            found_ep = None
            for s in item.get('seasons', []):
                if s.get('number', -2) == utils.try_parse_int(self.infolabels.get('season', -1)):
                    for ep in s.get('episodes', []):
                        if ep.get('number', -2) == utils.try_parse_int(self.infolabels.get('episode', -1)):
                            found_ep = item = ep
                            break
                    break
            if not found_ep:
                return

        lastplayed = utils.convert_timestamp(item.get('last_watched_at'))
        self.infolabels['lastplayed'] = lastplayed.strftime('%Y-%m-%d %H:%M:%S') if lastplayed else None
        self.infolabels['playcount'] = item.get('plays', 0)
        self.infolabels['overlay'] = 5 if item.get('plays') else 4

    def get_tmdb_details(self, tmdb=None):
        if not tmdb:
            return

        details = None
        if self.infolabels.get('mediatype') in ['movie', 'tvshow']:
            tmdbtype = 'tv' if self.infolabels.get('mediatype') == 'tvshow' else 'movie'
            details = tmdb.get_detailed_item(tmdbtype, self.tmdb_id, cache_only=True)
        if self.infolabels.get('mediatype') in ['season', 'episode']:
            episode = self.infolabels.get('episode') if self.infolabels.get('mediatype') == 'episode' else None
            details = tmdb.get_detailed_item('tv', self.tmdb_id, season=self.infolabels.get('season'), episode=episode, cache_only=True)
        # # TODO: Add details for actors

        if not details:
            return

        self.cast = details.get('cast', [])
        self.infolabels = utils.merge_two_dicts(details.get('infolabels', {}), utils.del_empty_keys(self.infolabels))
        self.infoproperties = utils.merge_two_dicts(details.get('infoproperties', {}), utils.del_empty_keys(self.infoproperties))

    def get_omdb_details(self, omdb=None):
        if omdb and self.imdb_id and self.infolabels.get('mediatype') == 'movie':
            self.infoproperties = utils.merge_two_dicts(self.infoproperties, omdb.get_ratings_awards(imdb_id=self.imdb_id, cache_only=True))

    def get_kodi_details(self):
        if not self.dbid:
            return

        details = {}
        if self.infolabels.get('mediatype') == 'movie':
            details = KodiLibrary().get_movie_details(self.dbid)
        if self.infolabels.get('mediatype') == 'tvshow':
            details = KodiLibrary().get_tvshow_details(self.dbid)
        if self.infolabels.get('mediatype') == 'episode':
            details = KodiLibrary().get_episode_details(self.dbid)

        if not details:
            return

        self.icon = self.icon or details.get('icon', '')
        self.thumb = self.thumb or details.get('thumb', '')
        self.poster = self.poster or details.get('poster', '')
        self.fanart = self.fanart or details.get('fanart', '')
        self.cast = self.cast or details.get('cast', [])
        self.infolabels = utils.merge_two_dicts(details.get('infolabels', {}), utils.del_empty_keys(self.infolabels))
        self.infoproperties = utils.merge_two_dicts(details.get('infoproperties', {}), utils.del_empty_keys(self.infoproperties))
        self.streamdetails = details.get('streamdetails', {})

    def get_details(self, dbtype=None, tmdb=None, omdb=None, kodi=None):
        self.infolabels['mediatype'] = dbtype

        if self.dbid:
            self.infolabels['dbid'] = self.dbid

        if not dbtype:
            return

        self.get_tmdb_details(tmdb=tmdb)
        self.get_omdb_details(omdb=omdb)
        self.get_kodi_details() if self.addon.getSettingBool('local_db') or kodi else None

        if self.infolabels.get('mediatype') == 'tvshow':
            self.infoproperties['unwatchedepisodes'] = utils.try_parse_int(self.infolabels.get('episode')) - utils.try_parse_int(self.infoproperties.get('watchedepisodes'))

    def set_listitem(self, path=None):
        listitem = xbmcgui.ListItem(label=self.label, label2=self.label2, path=path)
        listitem.setLabel2(self.label2)
        listitem.setUniqueIDs({'imdb': self.imdb_id, 'tmdb': self.tmdb_id})
        listitem.setInfo(self.library, self.infolabels)
        listitem.setProperties(self.infoproperties)
        listitem.setArt({
            'thumb': self.thumb, 'icon': self.icon, 'poster': self.poster, 'fanart': self.fanart,
            'clearlogo': self.clearlogo, 'clearart': self.clearart, 'landscape': self.landscape, 'banner': self.banner})
        listitem.setCast(self.cast)

        if self.streamdetails:
            for k, v in self.streamdetails.items():
                if not k or not v:
                    continue
                for i in v:
                    if not i:
                        continue
                    listitem.addStreamInfo(k, i)

        return listitem

    def create_listitem(self, handle=None, **kwargs):
        xbmcplugin.addDirectoryItem(handle, self.set_url(**kwargs), self.set_listitem(), self.is_folder)
