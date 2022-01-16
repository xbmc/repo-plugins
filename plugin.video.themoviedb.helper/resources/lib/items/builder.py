import re
from resources.lib.items.artselect import _ArtworkSelector
from resources.lib.addon.plugin import get_setting
from resources.lib.items.listitem import ListItem
from resources.lib.files.bcache import BasicCache
from resources.lib.api.tmdb.api import TMDb
from resources.lib.api.fanarttv.api import FanartTV
from resources.lib.addon.tmdate import set_timestamp, get_timestamp
from resources.lib.addon.consts import IMAGEPATH_QUALITY_POSTER, IMAGEPATH_QUALITY_FANART, IMAGEPATH_QUALITY_THUMBS, IMAGEPATH_QUALITY_CLOGOS, IMAGEPATH_ALL, ARTWORK_BLACKLIST
from resources.lib.addon.thread import ParallelThread
from resources.lib.addon.logger import TimerList

FTV_SECOND_PREF = get_setting('fanarttv_secondpref')
ARTWORK_QUALITY = get_setting('artwork_quality', 'int')
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
    def __init__(self, tmdb_api=None, ftv_api=None, trakt_api=None, cache_only=False, delay_write=False, log_timers=False, timer_lists: dict = None):
        self.parent_tv = {}
        self.parent_season = {}
        self.tmdb_api = tmdb_api or TMDb()
        self.ftv_api = ftv_api or FanartTV()
        self.trakt_api = trakt_api
        self._cache = BasicCache(filename='ItemBuilder.db', delay_write=delay_write)
        self._regex = re.compile(r'({})'.format('|'.join(IMAGEPATH_ALL)))
        self.parent_params = None
        self.cache_only = cache_only
        self.timer_lists = timer_lists if isinstance(timer_lists, dict) else {}
        self.log_timers = log_timers
        self._yy = 0
        self.override = False if self.tmdb_api.iso_language == 'en' else True  # Override titles with TMDb translated data
        # self.__dict__.update(kwargs)

    def _timestamp(self, days=14):
        return set_timestamp(days * 24 * 3600)

    def _timeint(self, x, div=5):
        return int(x) // div

    def get_parents(self, tmdb_type, tmdb_id, season=None):
        with TimerList(self.timer_lists, f'{tmdb_type}.{tmdb_id}.{season}', log_threshold=0.05, logging=self.log_timers):
            if tmdb_type != 'tv' or not tmdb_id:
                return
            self.parent_tv = self.get_item(tmdb_type=tmdb_type, tmdb_id=tmdb_id)
            if season is None:
                return
            self.parent_season = self.get_item(tmdb_type=tmdb_type, tmdb_id=tmdb_id, season=season)

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
            k = f'{prefix}{k}'
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

    def get_tmdb_item(
            self, tmdb_type, tmdb_id, season=None, episode=None, base_item=None, manual_art=None,
            base_is_season=False, cache_refresh=False):
        with TimerList(self.timer_lists, 'item_tmdb', log_threshold=0.05, logging=self.log_timers):
            details = self.tmdb_api.get_details_request(tmdb_type, tmdb_id, season, episode, cache_refresh=cache_refresh)
            if not details:
                return
            if season is not None:
                tmdb_type = 'season' if episode is None else 'episode'
            item = {
                'listitem': self.tmdb_api.mapper.get_info(
                    details, tmdb_type,
                    base_item=base_item['listitem'] if base_item else None,
                    base_is_season=base_is_season),
                'expires': self._timestamp(),
                'artwork': {}}
            item['artwork']['tmdb'] = item['artwork'][ARTWORK_QUALITY] = item['listitem'].pop('art')
            if manual_art:
                item['artwork']['manual'] = manual_art
            item['listitem']['art'] = {}
        return item

    def get_cache_name(self, tmdb_type, tmdb_id, season=None, episode=None):
        language = self.tmdb_api.language
        return f'{language}.{tmdb_type}.{tmdb_id}.{season}.{episode}'

    def get_item(self, tmdb_type, tmdb_id, season=None, episode=None, cache_refresh=False):
        if not tmdb_type or not tmdb_id:
            return

        # Get cached item
        name = self.get_cache_name(tmdb_type, tmdb_id, season, episode)
        item = None if cache_refresh else self._cache.get_cache(name)
        if self.cache_only:
            return item

        # Get the parent tvshow/season for season/episode
        base_item = None
        base_name_season = None
        if season is not None:
            if episode is not None:
                base_name_season = season
            parent = self.parent_tv if base_name_season is None else self.parent_season
            base_name = self.get_cache_name(tmdb_type, tmdb_id, base_name_season)
            base_item = parent or self._cache.get_cache(base_name)

        # Check that our current item hasn't expired and needs refreshing
        if item and get_timestamp(item['expires']):  # Our item hasn't expired
            # Check that our parent item doesn't have newer details that we need to merge
            if not base_item or self._timeint(base_item['expires']) <= self._timeint(item['expires']):  # No new details in parent item
                # Check that we aren't missing any artwork or need to remap artwork quality
                if not self.ftv_api or item['artwork'].get('fanarttv'):  # We have fanarttv artwork (or user disabled fanarttv)
                    if item['artwork'].get(ARTWORK_QUALITY):  # We also have artwork at the correct quality level
                        return item  # Our item is up-to-date so we return it
                # Else we've got current item details but we need to grab some artwork or remap quality
                prefix = 'tvshow.' if season is not None and episode is None else ''  # Seasons should map tvshow art with prefix
                item = self.get_artwork(item, tmdb_type, season, episode, base_item, prefix=prefix)  # Get art and map it
                return self._cache.set_cache(item, name, cache_days=CACHE_DAYS)  # Re-add our item to the cache with new details

        # Item isn't current so it needs a refresh but let's make sure we keep manually set artwork
        prefix = ''
        manual_art = item['artwork'].get('manual', {}) if item and episode is None else {}  # Episodes inherit season/tvshow art so don't have their own manual art
        manual_art = {k: v for k, v in manual_art.items() if v and '.' not in k}  # Only get main art and filter out parent prefixed items
        if season is not None:
            prefix = 'tvshow.' if episode is None else prefix  # Seasons should prefix tvshow parent art to avoid mixing
            base_artwork = base_item['artwork'].get('manual', {}) if base_item else {}  # Get parent manual art if available
            base_artwork = {k: v for k, v in base_artwork.items() if v}  # Filter out empties
            if cache_refresh or not base_item:  # No parent item or refreshing so let's try to get a new one
                base_item = self.get_item(tmdb_type, tmdb_id, base_name_season, cache_refresh=cache_refresh)
            manual_art = self.join_base_artwork(base_artwork, manual_art, prefix=prefix)  # Join our manual artwork with our base

        # Try to get FTV artwork (if IDs are available) in parallel thread at same time as item
        with ParallelThread(
                [tmdb_type] if episode is None else [],
                self._get_ftv_artwork, base_item or item,
                season=season, tmdb_id=tmdb_id) as pt:
            item = self.get_tmdb_item(
                tmdb_type, tmdb_id, season=season, episode=episode,
                base_item=base_item, manual_art=manual_art,
                base_is_season=base_name_season is not None,
                cache_refresh=cache_refresh)
            item_queue = pt.queue
        ftv_art = item_queue[0] if item_queue else None
        item = self.get_artwork(item, tmdb_type, season, episode, base_item, prefix=prefix, ftv_art=ftv_art)
        return self._cache.set_cache(item, name, cache_days=CACHE_DAYS)

    def get_item_artwork(self, artwork, art_dict=None, is_season=False):
        def set_artwork(details=None, blacklist=[]):
            if not details:
                return
            if not blacklist:
                art_dict.update(details)
                return
            for k, v in details.items():
                if not v:
                    continue
                if k in blacklist and art_dict.get(k):
                    continue
                art_dict[k] = v
        art_dict = {} if art_dict is None else art_dict
        tmdb_art = artwork.get(ARTWORK_QUALITY) or self.map_artwork(artwork.get('tmdb', {}))
        if FTV_SECOND_PREF:
            set_artwork(artwork.get('fanarttv'))
            set_artwork(tmdb_art, blacklist=['landscape'] if is_season else [])
        else:
            set_artwork(tmdb_art)
            set_artwork(artwork.get('fanarttv'), blacklist=ARTWORK_BLACKLIST[ARTWORK_QUALITY])
        set_artwork(artwork.get('manual'))
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
        li.set_details(item['listitem'], override=self.override)
        li.art = self.get_item_artwork(item['artwork'], is_season=mediatype in ['season', 'episode'])
        return li
