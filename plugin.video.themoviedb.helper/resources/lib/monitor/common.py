import xbmc
from resources.lib.addon.window import get_property
from resources.lib.tmdb.api import TMDb
from resources.lib.omdb.api import OMDb
from resources.lib.trakt.api import TraktAPI
from resources.lib.fanarttv.api import FanartTV
from resources.lib.addon.plugin import ADDON, kodi_traceback
from resources.lib.addon.parser import try_int
from resources.lib.addon.setutils import merge_two_dicts
from resources.lib.addon.decorators import try_except_log


SETMAIN = {
    'label', 'tmdb_id', 'imdb_id'}
SETMAIN_ARTWORK = {
    'icon', 'poster', 'thumb', 'fanart', 'discart', 'clearart', 'clearlogo', 'landscape', 'banner'}
SETINFO = {
    'title', 'originaltitle', 'tvshowtitle', 'plot', 'rating', 'votes', 'premiered', 'year',
    'imdbnumber', 'tagline', 'status', 'episode', 'season', 'genre', 'set', 'studio', 'country',
    'MPAA', 'director', 'writer', 'trailer', 'top250'}
SETPROP = {
    'tmdb_id', 'imdb_id', 'tvdb_id', 'tvshow.tvdb_id', 'tvshow.tmdb_id', 'tvshow.imdb_id',
    'biography', 'birthday', 'age', 'deathday', 'character', 'department', 'job', 'known_for', 'role', 'born',
    'creator', 'aliases', 'budget', 'revenue', 'set.tmdb_id', 'set.name', 'set.poster', 'set.fanart'}
SETPROP_RATINGS = {
    'awards', 'metacritic_rating', 'imdb_rating', 'imdb_votes', 'rottentomatoes_rating',
    'rottentomatoes_image', 'rottentomatoes_reviewtotal', 'rottentomatoes_reviewsfresh',
    'rottentomatoes_reviewsrotten', 'rottentomatoes_consensus', 'rottentomatoes_usermeter',
    'rottentomatoes_userreviews', 'trakt_rating', 'trakt_votes', 'goldenglobe_wins',
    'goldenglobe_nominations', 'oscar_wins', 'oscar_nominations', 'award_wins', 'award_nominations',
    'emmy_wins', 'emmy_nominations', 'tmdb_rating', 'tmdb_votes', 'top250'}


class CommonMonitorFunctions(object):
    def __init__(self):
        self.properties = set()
        self.index_properties = set()
        self.trakt_api = TraktAPI()
        self.tmdb_api = TMDb()
        self.fanarttv = FanartTV()
        self.omdb_api = OMDb() if ADDON.getSettingString('omdb_apikey') else None
        self.imdb_top250 = {}
        self.property_prefix = 'ListItem'

    @try_except_log('lib.monitor.common clear_property')
    def clear_property(self, key):
        key = u'{}.{}'.format(self.property_prefix, key)
        get_property(key, clear_property=True)

    @try_except_log('lib.monitor.common set_property')
    def set_property(self, key, value):
        key = u'{}.{}'.format(self.property_prefix, key)
        if value is None:
            get_property(key, clear_property=True)
        else:
            get_property(key, set_property=u'{0}'.format(value))

    def set_iter_properties(self, dictionary, keys):
        if not isinstance(dictionary, dict):
            dictionary = {}
        for k in keys:
            try:
                v = dictionary.get(k, None)
                if isinstance(v, list):
                    try:
                        v = ' / '.join(v)
                    except Exception as exc:
                        kodi_traceback(exc, u'\nlib.monitor.common set_iter_properties\nk: {} v: {}'.format(k, v))
                self.properties.add(k)
                self.set_property(k, v)
            except Exception as exc:
                kodi_traceback(exc, u'\nlib.monitor.common set_iter_properties\nk: {}'.format(k))

    def set_indexed_properties(self, dictionary):
        if not isinstance(dictionary, dict):
            return

        index_properties = set()
        for k, v in dictionary.items():
            if k in self.properties or k in SETPROP_RATINGS or k in SETMAIN_ARTWORK:
                continue
            try:
                v = v or ''
                self.set_property(k, v)
                index_properties.add(k)
            except Exception as exc:
                kodi_traceback(exc, u'\nlib.monitor.common set_indexed_properties\nk: {} v: {}'.format(k, v))

        for k in (self.index_properties - index_properties):
            self.clear_property(k)
        self.index_properties = index_properties.copy()

    @try_except_log('lib.monitor.common set_list_properties')
    def set_list_properties(self, items, key, prop):
        if not isinstance(items, list):
            return
        joinlist = [i[key] for i in items[:10] if i.get(key)]
        joinlist = ' / '.join(joinlist)
        self.properties.add(prop)
        self.set_property(prop, joinlist)

    @try_except_log('lib.monitor.common set_time_properties')
    def set_time_properties(self, duration):
        minutes = duration // 60 % 60
        hours = duration // 60 // 60
        totalmin = duration // 60
        self.set_property('Duration', totalmin)
        self.set_property('Duration_H', hours)
        self.set_property('Duration_M', minutes)
        self.set_property('Duration_HHMM', u'{0:02d}:{1:02d}'.format(hours, minutes))
        self.properties.update(['Duration', 'Duration_H', 'Duration_M', 'Duration_HHMM'])

    def set_properties(self, item):
        self.set_iter_properties(item, SETMAIN)
        self.set_iter_properties(item.get('infolabels', {}), SETINFO)
        self.set_iter_properties(item.get('infoproperties', {}), SETPROP)
        self.set_time_properties(item.get('infolabels', {}).get('duration', 0))
        self.set_list_properties(item.get('cast', []), 'name', 'cast')
        if xbmc.getCondVisibility("!Skin.HasSetting(TMDbHelper.DisableExtendedProperties)"):
            self.set_indexed_properties(item.get('infoproperties', {}))

    @try_except_log('lib.monitor.common get_tmdb_id')
    def get_tmdb_id(self, tmdb_type, imdb_id=None, query=None, year=None, episode_year=None):
        if imdb_id and imdb_id.startswith('tt'):
            return self.tmdb_api.get_tmdb_id(tmdb_type=tmdb_type, imdb_id=imdb_id)
        return self.tmdb_api.get_tmdb_id(tmdb_type=tmdb_type, query=query, year=year, episode_year=episode_year)

    def get_fanarttv_artwork(self, item, tmdb_type=None, tmdb_id=None, tvdb_id=None):
        if not self.fanarttv or tmdb_type not in ['movie', 'tv']:
            return item
        lookup_id = None
        if tmdb_type == 'tv':
            lookup_id = tvdb_id or item.get('unique_ids', {}).get('tvshow.tvdb') or item.get('unique_ids', {}).get('tvdb')
            func = self.fanarttv.get_tv_all_artwork
        elif tmdb_type == 'movie':
            lookup_id = tmdb_id or item.get('unique_ids', {}).get('tmdb')
            func = self.fanarttv.get_movies_all_artwork
        if lookup_id:
            item['art'] = merge_two_dicts(item.get('art', {}), func(lookup_id))
        return item

    def get_trakt_ratings(self, item, trakt_type, season=None, episode=None):
        ratings = self.trakt_api.get_ratings(
            trakt_type=trakt_type,
            imdb_id=item.get('unique_ids', {}).get('tvshow.imdb') or item.get('unique_ids', {}).get('imdb'),
            trakt_id=item.get('unique_ids', {}).get('tvshow.trakt') or item.get('unique_ids', {}).get('trakt'),
            slug_id=item.get('unique_ids', {}).get('tvshow.slug') or item.get('unique_ids', {}).get('slug'),
            season=season,
            episode=episode)
        if not ratings:
            return item
        item['infoproperties'] = merge_two_dicts(item.get('infoproperties', {}), ratings)
        return item

    def get_imdb_top250_rank(self, item):
        if not self.imdb_top250:
            self.imdb_top250 = self.trakt_api.get_imdb_top250(id_type='tmdb')
        try:
            item['infoproperties']['top250'] = item['infolabels']['top250'] = self.imdb_top250.index(
                try_int(item.get('unique_ids', {}).get('tmdb'))) + 1
        except Exception:
            pass
        return item

    def get_omdb_ratings(self, item, cache_only=False):
        if not self.omdb_api:
            return item
        return self.omdb_api.get_item_ratings(item, cache_only=cache_only)

    def clear_properties(self, ignore_keys=None):
        if not ignore_keys:
            self.cur_item = 0
            self.pre_item = 1
        ignore_keys = ignore_keys or set()
        for k in self.properties - ignore_keys:
            self.clear_property(k)
        self.properties = set()
        for k in self.index_properties:
            self.clear_property(k)
        self.index_properties = set()

    def clear_property_list(self, properties):
        for k in properties:
            self.clear_property(k)
