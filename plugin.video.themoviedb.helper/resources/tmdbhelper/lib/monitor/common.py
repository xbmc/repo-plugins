from tmdbhelper.lib.addon.plugin import get_infolabel, get_condvisibility
from tmdbhelper.lib.addon.tmdate import convert_timestamp, get_region_date
from tmdbhelper.lib.addon.logger import kodi_try_except, kodi_log
from tmdbhelper.lib.files.futils import validate_join
from tmdbhelper.lib.api.kodi.rpc import get_person_stats
from tmdbhelper.lib.api.contains import CommonContainerAPIs
from tmdbhelper.lib.monitor.propertysetter import PropertySetter
from jurialmunkey.parser import try_int
import xbmcvfs
import json


SETMAIN = {
    'label', 'tmdb_id', 'imdb_id', 'folderpath', 'filenameandpath'}
SETMAIN_ARTWORK = {
    'cropimage', 'cropimage.original', 'blurimage', 'blurimage.original', 'desaturateimage', 'desaturateimage.original', 'colorsimage', 'colorsimage.original',
    'icon', 'poster', 'thumb', 'fanart', 'discart', 'clearart', 'clearlogo', 'landscape', 'banner', 'keyart',
    'season.poster', 'season.thumb', 'season.fanart', 'season.discart', 'season.clearart', 'season.clearlogo', 'season.landscape', 'season.banner', 'season.keyart',
    'tvshow.poster', 'tvshow.thumb', 'tvshow.fanart', 'tvshow.discart', 'tvshow.clearart', 'tvshow.clearlogo', 'tvshow.landscape', 'tvshow.banner', 'tvshow.keyart'}
SETINFO = {
    'title', 'originaltitle', 'tvshowtitle', 'plot', 'rating', 'votes', 'premiered', 'year',
    'imdbnumber', 'tagline', 'episode', 'season', 'genre', 'set', 'studio', 'country',
    'mpaa', 'director', 'writer', 'trailer'}
SETPROP = {
    'tmdb_id', 'imdb_id', 'tvdb_id', 'tvshow.tvdb_id', 'tvshow.tmdb_id', 'tvshow.imdb_id',
    'biography', 'birthday', 'age', 'deathday', 'character', 'department', 'job', 'known_for', 'role', 'born',
    'creator', 'aliases', 'budget', 'revenue', 'set.tmdb_id', 'set.name', 'set.poster', 'set.fanart'}
SETPROP_RATINGS = {
    'awards', 'metacritic_rating', 'imdb_rating', 'imdb_votes', 'rottentomatoes_rating',
    'rottentomatoes_image', 'rottentomatoes_reviewtotal', 'rottentomatoes_reviewsfresh',
    'rottentomatoes_reviewsrotten', 'rottentomatoes_consensus', 'rottentomatoes_usermeter',
    'rottentomatoes_userreviews', 'trakt_rating', 'trakt_votes', 'letterboxd_rating',
    'letterboxd_votes', 'mdblist_rating', 'mdblist_votes', 'goldenglobe_wins',
    'goldenglobe_nominations', 'oscar_wins', 'oscar_nominations', 'award_wins', 'award_nominations',
    'emmy_wins', 'emmy_nominations', 'tmdb_rating', 'tmdb_votes', 'top250',
    'total_awards_won', 'awards_won', 'awards_won_cr', 'academy_awards_won', 'goldenglobe_awards_won',
    'mtv_awards_won', 'criticschoice_awards_won', 'emmy_awards_won', 'sag_awards_won', 'bafta_awards_won',
    'total_awards_nominated', 'awards_nominated', 'awards_nominated_cr', 'academy_awards_nominated',
    'goldenglobe_awards_nominated', 'mtv_awards_nominated', 'criticschoice_awards_nominated',
    'emmy_awards_nominated', 'sag_awards_nominated', 'bafta_awards_nominated', 'status', 'episode_type',
    'next_aired', 'next_aired.long', 'next_aired.short', 'next_aired.day', 'next_aired.day_short', 'next_aired.year', 'next_aired.episode',
    'next_aired.name', 'next_aired.tmdb_id', 'next_aired.plot', 'next_aired.season', 'next_aired.rating', 'next_aired.votes', 'next_aired.thumb',
    'next_aired.original', 'next_aired.days_from_aired', 'next_aired.days_until_aired', 'next_aired.original', 'next_aired.custom',
    'last_aired', 'last_aired.long', 'last_aired.short', 'last_aired.day', 'last_aired.day_short', 'last_aired.year', 'last_aired.episode',
    'last_aired.name', 'last_aired.tmdb_id', 'last_aired.plot', 'last_aired.season', 'last_aired.rating', 'last_aired.votes', 'last_aired.thumb',
    'last_aired.original', 'last_aired.days_from_aired', 'last_aired.days_until_aired', 'last_aired.original', 'last_aired.custom', }

TVDB_AWARDS_KEYS = {
    'Academy Awards': 'academy',
    'Golden Globe Awards': 'goldenglobe',
    'MTV Movie & TV Awards': 'mtv',
    'Critics\' Choice Awards': 'criticschoice',
    'Primetime Emmy Awards': 'emmy',
    'Screen Actors Guild Awards': 'sag',
    'BAFTA Awards': 'bafta'}


class CommonMonitorDetails(CommonContainerAPIs):
    def __init__(self):
        self.imdb_top250 = {}
        self._item_memory_cache = {}

    @property
    def ib(self):
        try:
            return self._ib
        except AttributeError:
            from tmdbhelper.lib.addon.plugin import get_setting
            from tmdbhelper.lib.items.builder import ItemBuilderService
            self._ib = ItemBuilderService(tmdb_api=self.tmdb_api, ftv_api=self.ftv_api, trakt_api=self.trakt_api)
            self._ib.ftv_api = self.ftv_api if get_setting('service_fanarttv_lookup') else None
            return self._ib

    def use_item_memory_cache(self, cache_name, func, *args, **kwargs):
        cache_data = self._item_memory_cache.get(cache_name) or func(*args, **kwargs)
        if not cache_data:
            return
        self._item_memory_cache[cache_name] = cache_data
        return cache_data

    def get_awards_data(self):
        try:
            filepath = validate_join('special://home/addons/plugin.video.themoviedb.helper/resources/jsondata/', 'awards.json')
            with xbmcvfs.File(filepath, 'r') as file:
                return json.load(file)
        except (IOError, json.JSONDecodeError):
            kodi_log('ERROR: Failed to load awards data!')
            return {'movie': {}, 'tv': {}}

    @kodi_try_except('lib.monitor.common get_tmdb_id')
    def get_tmdb_id(self, tmdb_type, imdb_id=None, query=None, year=None, episode_year=None):
        if imdb_id and imdb_id.startswith('tt'):
            return self.tmdb_api.get_tmdb_id(tmdb_type=tmdb_type, imdb_id=imdb_id)
        return self.tmdb_api.get_tmdb_id(tmdb_type=tmdb_type, query=query, year=year, episode_year=episode_year)

    @kodi_try_except('lib.monitor.common get_tmdb_id_multi')
    def get_tmdb_id_multi(self, media_type=None, imdb_id=None, query=None, year=None, episode_year=None):
        multi_i = self.tmdb_api.get_tmdb_multisearch(query=query, media_type=media_type) or {}
        return (multi_i.get('id'), multi_i.get('media_type'),)

    @kodi_try_except('lib.monitor.common get_tmdb_id_parent')
    def get_tmdb_id_parent(self, tmdb_id, trakt_type, season_episode_check=None):
        return self.trakt_api.get_id(tmdb_id, 'tmdb', trakt_type, output_type='tmdb', output_trakt_type='show', season_episode_check=season_episode_check)

    def get_trakt_episode_type(self, item, season=None, episode=None):
        from contextlib import suppress
        with suppress(KeyError, TypeError):
            trakt_id = None
            trakt_id = item['unique_ids'].get('tvshow.trakt') \
                or item['unique_ids'].get('tvshow.slug') \
                or item['unique_ids'].get('tvshow.imdb')
        episode_type = self.trakt_api.get_episode_type(trakt_id, season, episode)
        if episode_type:
            item['infoproperties']['episode_type'] = episode_type
        return item

    def get_trakt_ratings(self, item, trakt_type, season=None, episode=None):
        from contextlib import suppress
        with suppress(KeyError, TypeError):
            trakt_id = None
            trakt_id = item['unique_ids'].get('tvshow.trakt') \
                or item['unique_ids'].get('tvshow.slug') \
                or item['unique_ids'].get('tvshow.imdb') \
                or item['unique_ids'].get('trakt') \
                or item['unique_ids'].get('slug') \
                or item['unique_ids'].get('imdb')
        trakt_rating, trakt_votes = self.trakt_api.get_ratings(trakt_type, trakt_id, season, episode)
        if trakt_rating:
            item['infoproperties']['trakt_rating'] = trakt_rating
        if trakt_votes:
            item['infoproperties']['trakt_votes'] = trakt_votes
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

    def get_mdblist_ratings(self, item, trakt_type, tmdb_id):
        if not self.mdblist_api:
            return item
        ratings = self.mdblist_api.get_ratings(trakt_type, tmdb_id=tmdb_id) or {}

        # Pop some ratings we already retrieve from other services
        for i in ('trakt_rating', 'trakt_votes', 'tmdb_rating', 'tmdb_votes'):
            ratings.pop(i, None)

        item['infoproperties'].update(ratings)
        return item

    def get_tvdb_awards(self, item, tmdb_type, tmdb_id):
        try:
            awards = self.all_awards[tmdb_type][str(tmdb_id)]
        except(KeyError, TypeError, AttributeError):
            return item
        for t in ['awards_won', 'awards_nominated']:
            item_awards = awards.get(t)
            if not item_awards:
                continue
            all_awards, all_awards_cr = [], []
            for cat, lst in item_awards.items():
                all_awards_cr.append(f'[CR]{cat}' if all_awards else cat)
                all_awards_cr += lst
                all_awards += [(f'{cat} {i}') for i in lst]
                try:
                    item['infoproperties'][f'{TVDB_AWARDS_KEYS[cat]}_{t}'] = len(lst)
                except(KeyError, TypeError, AttributeError):
                    continue
            if all_awards:
                item['infoproperties'][f'total_{t}'] = len(all_awards)
                item['infoproperties'][t] = ' / '.join(all_awards)
                item['infoproperties'][f'{t}_cr'] = '[CR]'.join(all_awards_cr)
        return item

    def get_all_ratings(self, item, tmdb_type, tmdb_id, season=None, episode=None):
        try:
            trakt_type = {'movie': 'movie', 'tv': 'show'}[tmdb_type]
        except KeyError:
            return item  # Only lookup ratings for movie or tvshow
        item = self.get_omdb_ratings(item)
        item = self.get_imdb_top250_rank(item, trakt_type=trakt_type)
        item = self.get_trakt_ratings(item, trakt_type, season=season, episode=episode)
        item = self.get_trakt_episode_type(item, season=season, episode=episode)
        item = self.get_tvdb_awards(item, tmdb_type, tmdb_id)
        item = self.get_mdblist_ratings(item, trakt_type, tmdb_id)
        item = self.get_nextaired(item, tmdb_type, tmdb_id)
        return item

    def get_person_stats(self, item, tmdb_type, tmdb_id):
        if tmdb_type != 'person':
            return item

            return item
        try:
            name = item['infolabels']['title']
        except (KeyError, AttributeError, NameError):
            return item
        item.setdefault('infoproperties', {}).update(get_person_stats(name) or {})
        return item

    def get_nextaired(self, item, tmdb_type, tmdb_id):
        if 'status' in item['infolabels']:
            item['infoproperties']['status'] = item['infolabels']['status']
        if tmdb_type != 'tv':
            return item
        nextaired = self.tmdb_api.get_tvshow_nextaired(tmdb_id)
        item['infoproperties'].update(nextaired)
        return item


class CommonMonitorFunctions(PropertySetter, CommonMonitorDetails):
    def __init__(self):
        self.properties = set()
        self.index_properties = set()
        self.property_prefix = 'ListItem'
        super().__init__()

    def clear_property(self, key):
        key = f'{self.property_prefix}.{key}'
        self.get_property(key, clear_property=True)

    def set_property(self, key, value):
        key = f'{self.property_prefix}.{key}'
        if value is None:
            self.get_property(key, clear_property=True)
            return
        self.get_property(key, set_property=f'{value}')

    @kodi_try_except('lib.monitor.common set_iter_properties')
    def set_iter_properties(self, dictionary: dict, keys: set, property_object=None):
        """ Interates through a set of keys and adds corresponding value from the dictionary as a window property
        Lists of values from dictionary are joined with ' / '.join(dictionary[key])
        TMDbHelper.ListItem.{key} = dictionary[key]
        """
        if not isinstance(dictionary, dict):
            dictionary = {}

        if property_object is None:
            property_object = set()

        for k in keys:
            if k not in dictionary:
                continue
            v = dictionary[k]
            if v is None:
                continue
            if isinstance(v, list):
                v = ' / '.join(v)
            self.properties.add(k)
            property_object.add(k)
            self.set_property(k, v)

    @kodi_try_except('lib.monitor.common set_indexed_properties')
    def set_indexed_properties(self, dictionary):
        if not isinstance(dictionary, dict):
            return

        index_properties = set()

        if get_condvisibility("!Skin.HasSetting(TMDbHelper.DisableExtendedProperties) | !String.IsEmpty(Window.Property(TMDbHelper.EnableExtendedProperties))"):
            # Convert dictionary to list of keys to avoid iteration size change errors
            keys = (
                k for k in list(dictionary)
                if k not in self.properties
                and k not in SETPROP_RATINGS
                and k not in SETMAIN_ARTWORK)

            for k in keys:
                if k not in dictionary:
                    continue
                v = dictionary[k]
                if v is None:
                    continue
                self.set_property(k, v)
                index_properties.add(k)

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

    def set_properties(self, item, baseitem_properties=None):
        cast = item.get('cast', [])
        infolabels = item.get('infolabels', {})
        infoproperties = item.get('infoproperties', {})
        baseitem_properties = baseitem_properties or set()
        self.set_iter_properties(item, SETMAIN)
        self.set_iter_properties(infolabels, SETINFO)
        self.set_iter_properties(infoproperties, SETPROP.union(baseitem_properties))
        self.set_time_properties(infolabels.get('duration', 0))
        self.set_date_properties(infolabels.get('premiered'))
        self.set_list_properties(cast, 'name', 'cast')
        self.set_indexed_properties(infoproperties)

    def clear_properties(self, ignore_keys=None):
        if not ignore_keys:
            self._cur_item = 0
            self._pre_item = 1
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
