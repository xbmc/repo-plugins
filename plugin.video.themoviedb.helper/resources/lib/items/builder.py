import re
import xbmcaddon
from resources.lib.items.artselect import _ArtworkSelector
from resources.lib.items.listitem import ListItem
from resources.lib.files.cache import BasicCache
from resources.lib.api.tmdb.api import TMDb
from resources.lib.api.fanarttv.api import FanartTV
from resources.lib.addon.timedate import set_timestamp, get_timestamp
from resources.lib.addon.constants import IMAGEPATH_QUALITY_POSTER, IMAGEPATH_QUALITY_FANART, IMAGEPATH_QUALITY_THUMBS, IMAGEPATH_QUALITY_CLOGOS, IMAGEPATH_ALL, ARTWORK_BLACKLIST
from resources.lib.addon.decorators import TimerList, ParallelThread
from resources.lib.addon.plugin import kodi_log

ADDON = xbmcaddon.Addon('plugin.video.themoviedb.helper')
ARTWORK_QUALITY = ADDON.getSettingInt('artwork_quality')
ARTWORK_QUALITY_FANART = IMAGEPATH_QUALITY_FANART[ARTWORK_QUALITY]
ARTWORK_QUALITY_THUMBS = IMAGEPATH_QUALITY_THUMBS[ARTWORK_QUALITY]
ARTWORK_QUALITY_CLOGOS = IMAGEPATH_QUALITY_CLOGOS[ARTWORK_QUALITY]
ARTWORK_QUALITY_POSTER = IMAGEPATH_QUALITY_POSTER[ARTWORK_QUALITY]
IMAGEPATH_MAP = {
    "fanart": ARTWORK_QUALITY_FANART,
    "tvshow.fanart": ARTWORK_QUALITY_FANART,
    "season.fanart": ARTWORK_QUALITY_FANART,
    "landscape": ARTWORK_QUALITY_THUMBS,
    "tvshow.landscape": ARTWORK_QUALITY_THUMBS,
    "season.landscape": ARTWORK_QUALITY_THUMBS,
    "clearlogo": ARTWORK_QUALITY_CLOGOS,
    "tvshow.clearlogo": ARTWORK_QUALITY_CLOGOS,
    "season.clearlogo": ARTWORK_QUALITY_CLOGOS,
    "thumb": ARTWORK_QUALITY_THUMBS,
    "tvshow.thumb": ARTWORK_QUALITY_THUMBS,
    "season.thumb": ARTWORK_QUALITY_THUMBS,
    "poster": ARTWORK_QUALITY_POSTER,
    "tvshow.poster": ARTWORK_QUALITY_POSTER,
    "season.poster": ARTWORK_QUALITY_POSTER
}
CACHE_DAYS = 10000
BACKFILL_BLACKLIST = ['poster']


class ItemBuilder(_ArtworkSelector):
    def __init__(self, tmdb_api=None, ftv_api=None, trakt_api=None, cache_only=False, delay_write=False):
        self.parent_tv = {}
        self.parent_season = {}
        self.tmdb_api = tmdb_api or TMDb()
        self.ftv_api = ftv_api or FanartTV()
        self.trakt_api = trakt_api
        self._cache = BasicCache(filename='ItemBuilder.db', delay_write=delay_write)
        self._regex = re.compile(r'({})'.format('|'.join(IMAGEPATH_ALL)))
        self.parent_params = None
        self.cache_only = cache_only
        self.timer_lists = {}
        self.log_timers = False
        self._yy = 0
        # self.__dict__.update(kwargs)

    def _timestamp(self, days=14):
        return set_timestamp(days * 24 * 3600)

    def _timeint(self, x, div=5):
        return int(x) // div

    def get_parents(self, tmdb_type, tmdb_id, season=None):
        with TimerList(self.timer_lists, '{}.{}.{}'.format(tmdb_type, tmdb_id, season), log_threshold=0.05, logging=self.log_timers):
            if tmdb_type != 'tv' or not tmdb_id:
                return
            self.parent_tv = self.get_item(tmdb_type=tmdb_type, tmdb_id=tmdb_id)
            if season is None:
                return
            self.parent_season = self.get_item(tmdb_type=tmdb_type, tmdb_id=tmdb_id, season=season)

    def map_item(self, item, tmdb_type, base_item=None):
        return self.tmdb_api.mapper.get_info(item, tmdb_type, base_item=base_item)

    def map_artwork(self, artwork):
        """ Remaps artwork from TMDb to expected quality """
        return {k: self._regex.sub(IMAGEPATH_MAP[k], v) for k, v in artwork.items() if v and k in IMAGEPATH_MAP}

    def join_base_artwork(self, base_artwork, base_items, prefix='', backfill=False):
        for k, v in base_artwork.items():
            if not v:
                continue
            if k[:7] == 'tvshow.':
                if not prefix:
                    base_items[k] = v
                continue
            k = '{}{}'.format(prefix, k)
            base_items[k] = v
        backfill_items = base_items.copy() if backfill else {}
        for k, v in backfill_items.items():
            if k[:7] != 'tvshow.':
                continue
            k = k.replace('tvshow.', '')
            if k in base_items:
                continue
            if k not in BACKFILL_BLACKLIST:
                base_items[k] = v
        return base_items

    def get_ftv_typeid(self, tmdb_type, item, season=None, tmdb_id=None):
        unique_ids = item['listitem'].get('unique_ids', {}) if item else {}
        if tmdb_type == 'movie':
            return (tmdb_id or unique_ids.get('tmdb'), 'movies')
        if tmdb_type == 'tv':
            if season is None:
                return (unique_ids.get('tvdb'), 'tv')
            return (unique_ids.get('tvshow.tvdb') or unique_ids.get('tvdb'), 'tv')
        return None, None

    def _get_ftv_artwork(self, tmdb_type, item, season=None, tmdb_id=None):
        with TimerList(self.timer_lists, 'item_ftv', log_threshold=0.05, logging=self.log_timers):
            artwork = None
            if not self.ftv_api:
                return
            ftv_id, ftv_type = self.get_ftv_typeid(tmdb_type, item, season, tmdb_id)
            if not ftv_type:
                return
            if not ftv_id:
                return -1 if ftv_type == 'movies' else None
            artwork = self.ftv_api.get_all_artwork(ftv_id, ftv_type, season)
        return artwork

    def _get_tmdb_artwork(self, item):
        if not item or 'artwork' not in item:
            return {}
        return item['artwork'].setdefault(ARTWORK_QUALITY, self.map_artwork(item['artwork'].get('tmdb')) or {})

    def get_artwork(self, item, tmdb_type, season=None, episode=None, base_item=None, prefix='', ftv_art=None):
        if not item:
            return

        # TMDb Artwork reconfigure quality and merge base_item
        item_artwork = self._get_tmdb_artwork(item)
        item_artwork = self.join_base_artwork(self._get_tmdb_artwork(base_item), item_artwork, prefix=prefix, backfill=True)
        item['artwork'][ARTWORK_QUALITY] = item_artwork

        # FanartTV retrieve artwork and merge base_item
        ftv_art = ftv_art or item['artwork'].setdefault('fanarttv', {})
        if not ftv_art and episode is None:  # No episode art on ftv so don't look it up
            ftv_art = self._get_ftv_artwork(tmdb_type, base_item or item, season=season) or {}
        if ftv_art == -1:
            ftv_art = {}
        item['artwork']['fanarttv'] = ftv_art
        if base_item and 'artwork' in base_item:
            self.join_base_artwork(base_item['artwork'].get('fanarttv', {}), ftv_art, prefix=prefix, backfill=True)
        return item

    def get_tmdb_item(self, tmdb_type, tmdb_id, season=None, episode=None, base_item=None, manual_art=None):
        with TimerList(self.timer_lists, 'item_tmdb', log_threshold=0.05, logging=self.log_timers):
            details = self.tmdb_api.get_details_request(tmdb_type, tmdb_id, season, episode)
            if not details:
                return
            if season is not None:
                tmdb_type = 'season' if episode is None else 'episode'
            item = {
                'listitem': self.map_item(details, tmdb_type, base_item=base_item['listitem'] if base_item else None),
                'expires': self._timestamp(),
                'artwork': {}}
            item['artwork']['tmdb'] = item['artwork'][ARTWORK_QUALITY] = item['listitem'].pop('art')
            if manual_art:
                item['artwork']['manual'] = manual_art
            item['listitem']['art'] = {}
        return item

    def get_cache_name(self, tmdb_type, tmdb_id, season=None, episode=None):
        language = self.tmdb_api.language
        return '{}.{}.{}.{}.{}'.format(language, tmdb_type, tmdb_id, season, episode)

    def get_item(self, tmdb_type, tmdb_id, season=None, episode=None, cache_refresh=False):
        if not tmdb_type or not tmdb_id:
            return

        # Get cached item
        name = self.get_cache_name(tmdb_type, tmdb_id, season, episode)
        item = None if cache_refresh else self._cache.get_cache(name)
        if self.cache_only:
            return item

        # Check our cached item hasn't expired
        # Compare against parent expiry in case newer details available to merge
        base_item = None
        if season is not None:
            base_name_season = None if episode is None else season
            parent = self.parent_tv if base_name_season is None else self.parent_season
            base_name = self.get_cache_name(tmdb_type, tmdb_id, base_name_season)
            base_item = parent or self._cache.get_cache(base_name)
        if item and get_timestamp(item['expires']):
            if not base_item or self._timeint(base_item['expires']) <= self._timeint(item['expires']):
                if not self.ftv_api or item['artwork'].get('fanarttv'):
                    if item['artwork'].get(ARTWORK_QUALITY):
                        return item
                # We're only missing artwork from a specific API or only need to remap quality
                # kodi_log('REMAP {}.{}.format\n{}'.format(tmdb_type, tmdb_id, item['artwork'].keys()), 1)
                prefix = 'tvshow.' if season is not None and episode is None else ''
                item = self.get_artwork(item, tmdb_type, season, episode, base_item, prefix=prefix)
                return self._cache.set_cache(item, name, cache_days=CACHE_DAYS)

        # Keep previous manually selected artwork
        prefix = ''
        manual_art = item['artwork'].get('manual', {}) if item and episode is None else {}
        manual_art = {k: v for k, v in manual_art.items() if v and '.' not in k}
        if season is not None:
            if episode is None:
                prefix = 'tvshow.'
            base_item = base_item or self.get_item(tmdb_type, tmdb_id, base_name_season)
            base_artwork = base_item['artwork'].get('manual', {}) if base_item else {}
            base_artwork = {k: v for k, v in base_artwork.items() if v}
            manual_art = self.join_base_artwork(base_artwork, manual_art, prefix=prefix)

        # Try to get FTV artwork in parallel thread if IDs are available
        with ParallelThread(
                [tmdb_type] if episode is None else [],
                self._get_ftv_artwork, base_item or item,
                season=season, tmdb_id=tmdb_id) as pt:
            item = self.get_tmdb_item(
                tmdb_type, tmdb_id, season=season, episode=episode,
                base_item=base_item, manual_art=manual_art)
            item_queue = pt.queue
        ftv_art = item_queue[0] if item_queue else None
        item = self.get_artwork(item, tmdb_type, season, episode, base_item, prefix=prefix, ftv_art=ftv_art)
        return self._cache.set_cache(item, name, cache_days=CACHE_DAYS)
        # TODO: Remember to include OMDb too!

    def get_item_artwork(self, artwork):
        art_dict = artwork.get('tmdb') or {}
        art_dict.update(artwork.get('fanarttv') or {})
        art_dict.update(artwork.get('manual') or {})
        return art_dict

    def get_listitem(self, i):
        li = ListItem(parent_params=self.parent_params, **i)
        mediatype = li.infolabels.get('mediatype')
        item = self.get_item(
            li.get_tmdb_type(),
            li.unique_ids.get('tvshow.tmdb') if mediatype in ['season', 'episode'] else li.unique_ids.get('tmdb'),
            li.infolabels.get('season', 0) if mediatype in ['season', 'episode'] else None,
            li.infolabels.get('episode') if mediatype == 'episode' else None)
        if not item or 'listitem' not in item:
            return li
        li.set_details(item['listitem'])
        li.set_artwork(item['artwork'].get(ARTWORK_QUALITY))
        li.set_artwork(item['artwork'].get('fanarttv'), blacklist=ARTWORK_BLACKLIST[ARTWORK_QUALITY])
        li.set_artwork(item['artwork'].get('manual'))
        return li
