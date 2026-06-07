from resources.lib.addon.window import get_property
from resources.lib.api.tmdb.api import TMDb
from resources.lib.api.omdb.api import OMDb
from resources.lib.api.trakt.api import TraktAPI
from resources.lib.api.fanarttv.api import FanartTV
from resources.lib.addon.plugin import get_setting, get_infolabel, get_condvisibility
from resources.lib.addon.parser import try_int, merge_two_dicts
from resources.lib.addon.tmdate import convert_timestamp, get_region_date
from resources.lib.items.builder import ItemBuilder
from resources.lib.addon.logger import kodi_traceback, kodi_try_except


SETMAIN = {
    'label', 'tmdb_id', 'imdb_id'}
SETMAIN_ARTWORK = {
    'icon', 'poster', 'thumb', 'fanart', 'discart', 'clearart', 'clearlogo', 'landscape', 'banner', 'keyart'}
SETINFO = {
    'title', 'originaltitle', 'tvshowtitle', 'plot', 'rating', 'votes', 'premiered', 'year',
    'imdbnumber', 'tagline', 'status', 'episode', 'season', 'genre', 'set', 'studio', 'country',
    'mpaa', 'director', 'writer', 'trailer', 'top250'}
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
        self.ftv_api = FanartTV()
        self.omdb_api = OMDb() if get_setting('omdb_apikey', 'str') else None
        self.ib = ItemBuilder(tmdb_api=self.tmdb_api, ftv_api=self.ftv_api, trakt_api=self.trakt_api)
        self.imdb_top250 = {}
        self.property_prefix = 'ListItem'

    @kodi_try_except('lib.monitor.common clear_property')
    def clear_property(self, key):
        key = f'{self.property_prefix}.{key}'
        get_property(key, clear_property=True)

    @kodi_try_except('lib.monitor.common set_property')
    def set_property(self, key, value):
        key = f'{self.property_prefix}.{key}'
        if value is None:
            get_property(key, clear_property=True)
        else:
            get_property(key, set_property=f'{value}')

    def set_iter_properties(self, dictionary: dict, keys: set):
        """ Interates through a set of keys and adds corresponding value from the dictionary as a window property
        Lists of values from dictionary are joined with ' / '.join(dictionary[key])
        TMDbHelper.ListItem.{key} = dictionary[key]
        """
        if not isinstance(dictionary, dict):
            dictionary = {}
        for k in keys:
            try:
                v = dictionary.get(k, None)
                if isinstance(v, list):
                    try:
                        v = ' / '.join(v)
                    except Exception as exc:
                        kodi_traceback(exc, f'\nlib.monitor.common set_iter_properties\nk: {k} v: {v}')
                self.properties.add(k)
                self.set_property(k, v)
            except Exception as exc:
                kodi_traceback(exc, f'\nlib.monitor.common set_iter_properties\nk: {k}')

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
                kodi_traceback(exc, f'\nlib.monitor.common set_indexed_properties\nk: {k} v: {v}')

        for k in (self.index_properties - index_properties):
            self.clear_property(k)
        self.index_properties = index_properties.copy()

    @kodi_try_except('lib.monitor.common set_list_properties')
    def set_list_properties(self, items, key, prop):
        if not isinstance(items, list):
            return
        joinlist = [i[key] for i in items[:10] if i.get(key)]
        joinlist = ' / '.join(joinlist)
        self.properties.add(prop)
        self.set_property(prop, joinlist)

    @kodi_try_except('lib.monitor.common set_time_properties')
    def set_time_properties(self, duration):
        minutes = duration // 60 % 60
        hours = duration // 60 // 60
        totalmin = duration // 60
        self.set_property('Duration', totalmin)
        self.set_property('Duration_H', hours)
        self.set_property('Duration_M', minutes)
        self.set_property('Duration_HHMM', f'{hours:02d}:{minutes:02d}')
        self.properties.update(['Duration', 'Duration_H', 'Duration_M', 'Duration_HHMM'])

    @kodi_try_except('lib.monitor.common set_date_properties')
    def set_date_properties(self, premiered):
        date_obj = convert_timestamp(premiered, time_fmt="%Y-%m-%d", time_lim=10)
        if not date_obj:
            return
        self.set_property('Premiered', get_region_date(date_obj, 'dateshort'))
        self.set_property('Premiered_Long', get_region_date(date_obj, 'datelong'))
        self.set_property('Premiered_Custom', date_obj.strftime(get_infolabel('Skin.String(TMDbHelper.Date.Format)') or '%d %b %Y'))
        self.properties.update(['Premiered', 'Premiered_Long', 'Premiered_Custom'])

    def set_properties(self, item):
        self.set_iter_properties(item, SETMAIN)
        self.set_iter_properties(item.get('infolabels', {}), SETINFO)
        self.set_iter_properties(item.get('infoproperties', {}), SETPROP)
        self.set_time_properties(item.get('infolabels', {}).get('duration', 0))
        self.set_date_properties(item.get('infolabels', {}).get('premiered'))
        self.set_list_properties(item.get('cast', []), 'name', 'cast')
        if get_condvisibility("!Skin.HasSetting(TMDbHelper.DisableExtendedProperties)"):
            self.set_indexed_properties(item.get('infoproperties', {}))

    @kodi_try_except('lib.monitor.common get_tmdb_id')
    def get_tmdb_id(self, tmdb_type, imdb_id=None, query=None, year=None, episode_year=None, media_type=None):
        if imdb_id and imdb_id.startswith('tt'):
            return self.tmdb_api.get_tmdb_id(tmdb_type=tmdb_type, imdb_id=imdb_id)
        if tmdb_type == 'multi':
            multi_i = self.tmdb_api.get_tmdb_multisearch(query=query, media_type=media_type) or {}
            self.multisearch_tmdbtype = multi_i.get('media_type')
            return multi_i.get('id')
        return self.tmdb_api.get_tmdb_id(tmdb_type=tmdb_type, query=query, year=year, episode_year=episode_year)

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

    def get_imdb_top250_rank(self, item, trakt_type):
        try:
            tmdb_id = try_int(item['unique_ids'].get('tvshow.tmdb') or item['unique_ids'].get('tmdb'))
        except KeyError:
            tmdb_id = None
        if not tmdb_id:
            return item
        try:
            imdb_top250 = self.imdb_top250[trakt_type]
        except KeyError:
            imdb_top250 = self.trakt_api.get_imdb_top250(id_type='tmdb', trakt_type=trakt_type)
            if not imdb_top250:
                return item
            self.imdb_top250[trakt_type] = imdb_top250
        try:
            item['infoproperties']['top250'] = item['infolabels']['top250'] = imdb_top250.index(tmdb_id) + 1
        except Exception:
            return item
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
