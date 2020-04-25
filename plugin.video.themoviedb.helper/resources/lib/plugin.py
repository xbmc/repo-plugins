import xbmc
import xbmcgui
import xbmcaddon
import resources.lib.utils as utils
from resources.lib.constants import LANGUAGES, APPEND_TO_RESPONSE, TMDB_LISTS
from resources.lib.kodilibrary import KodiLibrary
from resources.lib.tmdb import TMDb
from resources.lib.omdb import OMDb
from resources.lib.fanarttv import FanartTV
from resources.lib.traktapi import TraktAPI


class Plugin(object):
    def __init__(self):
        self.addon = xbmcaddon.Addon('plugin.video.themoviedb.helper')
        self.addonpath = self.addon.getAddonInfo('path')
        self.prefixname = 'TMDbHelper.'
        self.kodimoviedb = None
        self.koditvshowdb = None
        self.details_tv = None
        self.imdb_top250 = None

        cache_long = self.addon.getSettingInt('cache_details_days')
        cache_short = self.addon.getSettingInt('cache_list_days')
        # tmdb_apikey = self.addon.getSettingString('tmdb_apikey')
        tmdb_apikey = None
        omdb_apikey = self.addon.getSettingString('omdb_apikey')
        # fanarttv_apikey = self.addon.getSettingString('fanarttv_apikey')
        fanarttv_apikey = None
        fanarttv_clientkey = self.addon.getSettingString('fanarttv_clientkey')
        language = LANGUAGES[self.addon.getSettingInt('language')]
        mpaa_prefix = self.addon.getSettingString('mpaa_prefix')

        self.tmdb = TMDb(
            api_key=tmdb_apikey, language=language, cache_long=cache_long, cache_short=cache_short,
            append_to_response=APPEND_TO_RESPONSE, mpaa_prefix=mpaa_prefix)

        self.omdb = OMDb(api_key=omdb_apikey, cache_long=cache_long, cache_short=cache_short) if omdb_apikey else None

        self.fanarttv = (
            FanartTV(
                api_key=fanarttv_apikey, client_key=fanarttv_clientkey, language=language,
                cache_long=cache_long, cache_short=cache_short)
            if self.addon.getSettingBool('fanarttv_lookup') else None)

    def textviewer(self, header, text):
        xbmcgui.Dialog().textviewer(header, text)

    def imageviewer(self, image):
        xbmc.executebuiltin('ShowPicture({0})'.format(image))

    def get_trakt_usernameslug(self, login=False):
        return TraktAPI().get_usernameslug(login=login)

    def get_kodi_person_stats(self, item):
        if item.get('infolabels', {}).get('title'):
            statistics = KodiLibrary().get_person_stats(item.get('infolabels', {}).get('title'))
            if statistics:
                item['infoproperties'] = utils.merge_two_dicts(item.get('infoproperties', {}), statistics)
        return item

    def get_tmdb_id(self, query=None, itemtype=None, imdb_id=None, tvdb_id=None, year=None, **kwargs):
        if kwargs.get('tmdb_id'):
            return kwargs.get('tmdb_id')
        query = utils.split_items(query)[0] if query else None
        itemtype = itemtype or TMDB_LISTS.get(kwargs.get('info'), {}).get('tmdb_check_id') or kwargs.get('type')
        return self.tmdb.get_tmdb_id(itemtype=itemtype, imdb_id=imdb_id, tvdb_id=tvdb_id, query=query, year=year, longcache=True)

    def get_omdb_ratings(self, item, cache_only=False):
        if self.omdb and item.get('infolabels', {}).get('imdbnumber'):
            ratings_awards = self.omdb.get_ratings_awards(imdb_id=item.get('infolabels', {}).get('imdbnumber'), cache_only=cache_only)
            if ratings_awards:
                item['infoproperties'] = utils.merge_two_dicts(item.get('infoproperties', {}), ratings_awards)
        return item

    def get_trakt_ratings(self, item, tmdbtype=None, tmdb_id=None, season=None, episode=None):
        imdb_id = self.tmdb.get_item_externalid(itemtype=tmdbtype, tmdb_id=tmdb_id, external_id='imdb_id')
        if tmdbtype and imdb_id:
            ratings = TraktAPI().get_ratings(tmdbtype=tmdbtype, imdb_id=imdb_id, season=season, episode=episode)
            if ratings:
                item['infoproperties'] = utils.merge_two_dicts(item.get('infoproperties', {}), ratings)
        return item

    def get_top250_rank(self, item):
        if not self.imdb_top250:
            self.imdb_top250 = [i.get('movie', {}).get('ids', {}).get('tmdb') for i in TraktAPI().get_imdb_top250()]
        try:
            item['infolabels']['top250'] = self.imdb_top250.index(item.get('infoproperties', {}).get('tmdb_id')) + 1
        except Exception:
            pass
        return item

    def get_kodi_artwork(self, item, dbtype=None, dbid=None):
        if not dbid:
            return item

        details = {}
        if dbtype == 'movies':
            details = KodiLibrary().get_movie_details(dbid)
        elif dbtype == 'tvshows':
            details = KodiLibrary().get_tvshow_details(dbid)
        elif dbtype == 'episodes':
            details = KodiLibrary().get_episode_details(dbid)

        if not details:
            return item

        item['icon'] = details.get('icon') or item.get('icon') or ''
        item['thumb'] = details.get('thumb') or item.get('thumb') or ''
        item['poster'] = details.get('poster') or item.get('poster') or ''
        item['fanart'] = details.get('fanart') or item.get('fanart') or ''
        item['landscape'] = details.get('landscape') or item.get('landscape') or ''
        item['clearart'] = details.get('clearart') or item.get('clearart') or ''
        item['clearlogo'] = details.get('clearlogo') or item.get('clearlogo') or ''
        item['discart'] = details.get('discart') or item.get('discart') or ''

        return item

    def get_fanarttv_artwork(self, item, tmdbtype=None, tmdb_id=None, tvdb_id=None):
        if not self.fanarttv or tmdbtype not in ['movie', 'tv']:
            return item

        artwork, lookup_id, func = None, None, None

        if tmdbtype == 'tv':
            lookup_id = tvdb_id or item.get('infoproperties', {}).get('tvshow.tvdb_id') or item.get('tvdb_id')
            func = self.fanarttv.get_tvshow_allart_lc
        elif tmdbtype == 'movie':
            lookup_id = tmdb_id or item.get('tmdb_id')
            func = self.fanarttv.get_movie_allart_lc

        if not lookup_id or not func:
            return item

        artwork = func(lookup_id)

        if artwork:
            item['discart'] = item.get('discart') or artwork.get('discart') or ''
            item['clearart'] = item.get('clearart') or artwork.get('clearart') or ''
            item['clearlogo'] = item.get('clearlogo') or artwork.get('clearlogo') or ''
            item['landscape'] = item.get('landscape') or artwork.get('landscape') or ''
            item['banner'] = item.get('banner') or artwork.get('banner') or ''
            item['fanart'] = item.get('fanart') or artwork.get('fanart') or ''
            item['extrafanart'] = item.get('extrafanart') or utils.iterate_extraart(artwork.get('extrafanart', [])) or ''
        return item

    def get_db_info(self, info=None, tmdbtype=None, imdb_id=None, originaltitle=None, title=None, year=None, tvshowtitle=None, season=None, episode=None, tmdb_id=None, tvdb_id=None):
        dbid = None
        kodidatabase = None
        if tmdbtype == 'movie':
            kodidatabase = self.kodimoviedb = self.kodimoviedb or KodiLibrary(dbtype='movie')
        if tmdbtype == 'tv':
            kodidatabase = self.koditvshowdb = self.koditvshowdb or KodiLibrary(dbtype='tvshow')
        if kodidatabase and info:
            return kodidatabase.get_info(info=info, imdb_id=imdb_id, tmdb_id=tmdb_id, tvdb_id=tvdb_id, originaltitle=originaltitle, title=title, year=year)
        if tmdbtype == 'episode':
            kodidatabase = self.koditvshowdb = self.koditvshowdb or KodiLibrary(dbtype='tvshow')
            dbid = kodidatabase.get_info(info='dbid', imdb_id=imdb_id, tmdb_id=tmdb_id, tvdb_id=tvdb_id, title=tvshowtitle, year=year)
            kodidatabase = KodiLibrary(dbtype='episode', tvshowid=dbid)
        if dbid and kodidatabase and season and episode:
            return kodidatabase.get_info('dbid', season=season, episode=episode)
