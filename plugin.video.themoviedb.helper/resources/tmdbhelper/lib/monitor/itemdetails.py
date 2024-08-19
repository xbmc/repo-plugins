from tmdbhelper.lib.addon.plugin import get_condvisibility, get_infolabel, convert_media_type, convert_type, get_setting
from tmdbhelper.lib.addon.tmdate import convert_timestamp, get_region_date
from jurialmunkey.window import get_property
from tmdbhelper.lib.monitor.images import ImageFunctions
from tmdbhelper.lib.items.listitem import ListItem
from tmdbhelper.lib.api.mapping import get_empty_item
from collections import namedtuple
from copy import deepcopy


BASEITEM_PROPERTIES = [
    ('base_label', ('label',), None),
    ('base_title', ('title',), None),
    ('base_icon', ('icon',), None),
    ('base_plot', ('plot', 'Property(artist_description)', 'Property(album_description)', 'addondescription'), None),
    ('base_tagline', ('tagline',), None),
    ('base_dbtype', ('dbtype',), None),
    ('base_rating', ('userrating', 'rating',), None),
    ('base_poster', ('Art(poster)', 'Art(season.poster)', 'Art(tvshow.poster)'), None),
    ('base_fanart', ('Art(fanart)', 'Art(season.fanart)', 'Art(tvshow.fanart)'), None),
    ('base_clearlogo', ('Art(clearlogo)', 'Art(tvshow.clearlogo)', 'Art(artist.clearlogo)'), None),
    ('base_tvshowtitle', ('tvshowtitle',), None),
    ('base_studio', ('studio',), lambda v: v.split(' / ')[0] if v else None),
    ('base_genre', ('genre',), lambda v: v.split(' / ')[0] if v else None),
    ('base_director', ('director',), lambda v: v.split(' / ')[0] if v else None),
    ('base_writer', ('writer',), lambda v: v.split(' / ')[0] if v else None),
]

CV_USE_MULTI_TYPE = ""\
    "Window.IsVisible(DialogPVRInfo.xml) | "\
    "Window.IsVisible(MyPVRChannels.xml) | " \
    "Window.IsVisible(MyPVRRecordings.xml) | "\
    "Window.IsVisible(MyPVRSearch.xml) | "\
    "Window.IsVisible(MyPVRGuide.xml)"

ARTWORK_LOOKUP_TABLE = {
    'poster': ['Art(tvshow.poster)', 'Art(poster)', 'Art(thumb)'],
    'fanart': ['Art(fanart)', 'Art(thumb)'],
    'landscape': ['Art(landscape)', 'Art(fanart)', 'Art(thumb)'],
    'thumb': ['Art(thumb)']}


CROPIMAGE_SOURCE = "Art(artist.clearlogo)|Art(tvshow.clearlogo)|Art(clearlogo)"


ItemDetails = namedtuple("ItemDetails", "tmdb_type tmdb_id listitem artwork")


class ListItemDetails():
    def __init__(self, parent, position=0):
        self._parent = parent
        self._position = position
        self._season = None
        self._episode = None
        self._itemdetails = None
        self._cache = parent._cache

    @property
    def dbtype(self):
        if self.get_infolabel('Property(tmdb_type)') == 'person':
            return 'actors'

        def _get_fallback():
            if get_condvisibility("!Skin.HasSetting(TMDbHelper.DisablePVR)"):
                if get_condvisibility(CV_USE_MULTI_TYPE):
                    return 'multi'
                if self.get_infolabel('ChannelNumberLabel'):
                    return 'multi'
                if self.get_infolabel('Path') == 'pvr://channels/tv/':
                    return 'multi'
            if self._parent._container == 'Container.' and get_setting('service_container_content_fallback'):
                return get_infolabel('Container.Content') or ''
            return ''

        dbtype = self.get_infolabel('dbtype')
        return f'{dbtype}s' if dbtype else _get_fallback()

    @property
    def query(self):
        query = self.get_infolabel('TvShowTitle')
        if not query and self._dbtype in ['movies', 'tvshows', 'actors', 'sets', 'multi']:
            query = self.get_infolabel('Title') or self.get_infolabel('Label')
        return query

    @property
    def year(self):
        return self.get_infolabel('year')

    @property
    def season(self):
        if self._dbtype not in ['seasons', 'episodes', 'multi']:
            return
        return self.get_infolabel('Season') or None

    @property
    def episode(self):
        if self._dbtype not in ['episodes', 'multi']:
            return
        return self.get_infolabel('Episode') or None

    @property
    def imdb_id(self):
        if self._season:
            return
        if self._dbtype not in ['movies', 'tvshows']:
            return
        imdb_id = self.get_infolabel('UniqueId(imdb)') or self.get_infolabel('IMDBNumber') or ''
        return imdb_id if imdb_id.startswith('tt') else ''

    @property
    def tmdb_id(self):
        if self._dbtype in ['movies', 'tvshows']:
            return self.get_infolabel('UniqueId(tmdb)')

        if self._dbtype == 'seasons':
            # TODO: Trakt lookup of TMDb ID for season similar to episodes
            return self.get_infolabel('UniqueId(tvshow.tmdb)')

        if self._dbtype == 'episodes':
            return self.get_infolabel('UniqueId(tvshow.tmdb)') or self._parent.get_tmdb_id_parent(
                tmdb_id=self.get_infolabel('UniqueId(tmdb)'),
                trakt_type='episode',
                season_episode_check=(self._season, self._episode,))

    @property
    def tmdb_type(self):
        if self._dbtype == 'multi':
            return 'multi'
        return convert_media_type(self._dbtype, 'tmdb', strip_plural=True, parent_type=True)

    @property
    def kodi_db(self):
        if not get_setting('local_db'):
            return

        if self._dbtype == 'movies':
            from tmdbhelper.lib.items.kodi import KodiDb
            return KodiDb('movie')

        if self._dbtype in ['tvshows', 'seasons', 'episodes']:
            from tmdbhelper.lib.items.kodi import KodiDb
            return KodiDb('tv')

    def setup_current_listitem(self):
        """ Cache property getter return values for performance """
        self._dbtype = self.dbtype
        self._query = self.query
        self._year = self.year
        self._season = self.season
        self._episode = self.episode
        self._imdb_id = self.imdb_id
        self._tmdb_id = self.tmdb_id

    def get_infolabel(self, info):
        return self._parent.get_infolabel(info, self._position)

    def get_artwork(self, source='', build_fallback=False, built_artwork=None):
        source = source or ''
        source = source.lower()

        def _get_artwork_infolabel(_infolabels):
            for i in _infolabels:
                artwork = self.get_infolabel(i)
                if not artwork:
                    continue
                return artwork

        def _get_artwork_fallback(_infolabels, _built_artwork):
            for i in _infolabels:
                if not i.startswith('art('):
                    continue
                artwork = _built_artwork.get(i[4:-1])
                if not artwork:
                    continue
                return artwork

        def _get_artwork(_source):
            if _source:
                _infolabels = ARTWORK_LOOKUP_TABLE.get(_source, _source.split("|"))
            else:
                _infolabels = ARTWORK_LOOKUP_TABLE.get('thumb')

            artwork = _get_artwork_infolabel(_infolabels)

            if artwork or not build_fallback:
                return artwork

            nonlocal built_artwork

            built_artwork = built_artwork or self.get_builtartwork()
            if not built_artwork:
                return

            return _get_artwork_fallback(_infolabels, built_artwork)

        for _source in source.split("||"):
            artwork = _get_artwork(_source)
            if not artwork:
                continue
            return artwork

    def get_image_manipulations(self, use_winprops=False, built_artwork=None):
        self._parent._last_blur_fallback = False

        images = {}

        _manipulations = (
            {'method': 'crop',
                'active': lambda: get_condvisibility("Skin.HasSetting(TMDbHelper.EnableCrop)"),
                'images': lambda: self.get_artwork(
                    source=CROPIMAGE_SOURCE,
                    build_fallback=True, built_artwork=built_artwork)},
            {'method': 'blur',
                'active': lambda: get_condvisibility("Skin.HasSetting(TMDbHelper.EnableBlur)"),
                'images': lambda: self.get_artwork(
                    source=get_property('Blur.SourceImage'),
                    build_fallback=True, built_artwork=built_artwork)
                or get_property('Blur.Fallback')},
            {'method': 'desaturate',
                'active': lambda: get_condvisibility("Skin.HasSetting(TMDbHelper.EnableDesaturate)"),
                'images': lambda: self.get_artwork(
                    source=get_property('Desaturate.SourceImage'),
                    build_fallback=True, built_artwork=built_artwork)
                or get_property('Desaturate.Fallback')},
            {'method': 'colors',
                'active': lambda: get_condvisibility("Skin.HasSetting(TMDbHelper.EnableColors)"),
                'images': lambda: self.get_artwork(
                    source=get_property('Colors.SourceImage'),
                    build_fallback=True, built_artwork=built_artwork)
                or get_property('Colors.Fallback')},)

        for i in _manipulations:
            if not i['active']():
                continue
            imgfunc = ImageFunctions(method=i['method'], is_thread=False, artwork=i['images']())

            output = imgfunc.func(imgfunc.image)
            images[f'{i["method"]}image'] = output
            images[f'{i["method"]}image.original'] = imgfunc.image

            if use_winprops:
                imgfunc.set_properties(output)

        return images

    def get_person_stats(self):
        if not self._itemdetails or not self._itemdetails.listitem:
            return
        return self._parent.get_person_stats(
            self._itemdetails.listitem, self._itemdetails.tmdb_type, self._itemdetails.tmdb_id)

    def get_all_ratings(self, use_deepcopy=False):
        if self._itemdetails.tmdb_type not in ['movie', 'tv']:
            return {}
        if not self._itemdetails or not self._itemdetails.listitem:
            return {}
        _listitem = deepcopy(self._itemdetails.listitem) if use_deepcopy else self._itemdetails.listitem
        return self._parent.get_all_ratings(_listitem, self._itemdetails.tmdb_type, self._itemdetails.tmdb_id, self._season, self._episode) or {}

    def get_nextaired(self):
        if not self._itemdetails or not self._itemdetails.listitem:
            return {}
        if self._itemdetails.tmdb_type != 'tv':
            return self._itemdetails.listitem
        return self._parent.get_nextaired(self._itemdetails.listitem, self._itemdetails.tmdb_type, self._itemdetails.tmdb_id)

    def get_additional_properties(self):
        if not self._itemdetails:
            return
        self._itemdetails.listitem['folderpath'] = self._itemdetails.listitem['infoproperties']['folderpath'] = self.get_infolabel('folderpath')
        self._itemdetails.listitem['filenameandpath'] = self._itemdetails.listitem['infoproperties']['filenameandpath'] = self.get_infolabel('filenameandpath')
        for k, v, f in BASEITEM_PROPERTIES:
            try:
                value = next(j for j in (self.get_infolabel(i) for i in v) if j)
                value = f(value) if f else value
                self._itemdetails.listitem['infoproperties'][k] = value
            except StopIteration:
                self._itemdetails.listitem['infoproperties'][k] = None

    def get_itemtypeid(self, tmdb_type):
        li_year = self._year if tmdb_type == 'movie' else None
        ep_year = self._year if tmdb_type == 'tv' else None
        multi_t = 'tv' if self._episode or self._season else None

        if tmdb_type == 'multi':
            tmdb_id, tmdb_type = self._parent.get_tmdb_id_multi(
                media_type=multi_t, query=self._query, imdb_id=self._imdb_id, year=li_year, episode_year=ep_year)
            self._dbtype = convert_type(tmdb_type, 'dbtype')
        elif self._tmdb_id:
            tmdb_id = self._tmdb_id
        else:
            tmdb_id = self._parent.get_tmdb_id(
                tmdb_type=tmdb_type, query=self._query, imdb_id=self._imdb_id, year=li_year, episode_year=ep_year)

        return {'tmdb_type': tmdb_type, 'tmdb_id': tmdb_id}

    def get_itemdetails(self, func, *args, **kwargs):
        """ Use itemdetails cache to return a named tuple of tmdb_type, tmdb_id, listitem, artwork
        Runs func(*args, **kwargs) after retrieving a new uncached item for early code execution
        """
        tmdb_type = self.tmdb_type

        def _get_quick(cache_name_id):
            cache_item = self._cache.get_cache(cache_name_id) if tmdb_type else None

            if not cache_item:
                func(*args, **kwargs) if func else None
                cache_item = self._cache.set_cache(self.get_itemtypeid(tmdb_type), cache_name_id)

            cache_data = self.get_itemdetails_online(**cache_item, season=self._season, episode=self._episode, use_cache=True)
            return cache_data

        cache_name_id = self._parent.get_item_identifier(self._position)
        cache_name_iq = f'_get_quick.{cache_name_id}'

        self._itemdetails = self._parent.use_item_memory_cache(cache_name_iq, _get_quick, cache_name_id) if tmdb_type else None
        self._itemdetails = self._itemdetails or self.get_itemdetails_blank()

        return self._itemdetails

    def get_itemdetails_online(self, tmdb_type=None, tmdb_id=None, season=None, episode=None, use_cache=False):

        def _get_itemdetails_online():
            details = self._parent.ib.get_item(tmdb_type, tmdb_id, season, episode)
            try:
                return ItemDetails(tmdb_type, tmdb_id, details['listitem'], details['artwork'])
            except (KeyError, AttributeError, TypeError):
                return

        if not use_cache:
            return _get_itemdetails_online()

        cache_name = f'{tmdb_type}.{tmdb_id}.{season}.{episode}'
        return self._parent.use_item_memory_cache(cache_name, _get_itemdetails_online)

    @staticmethod
    def get_itemdetails_blank():
        return ItemDetails(None, None, get_empty_item(), {})

    def get_builtartwork(self):
        if not self._itemdetails or not self._itemdetails.artwork:
            return {}
        return self._parent.ib.get_item_artwork(self._itemdetails.artwork, is_season=True if self._season else False) or {}

    def get_builtitem(self):
        if not self._itemdetails:
            return ListItem().get_listitem()

        def set_time_properties(li):
            duration = li.infolabels.get('duration') or 0
            hours = duration // 60 // 60
            minutes = duration // 60 % 60
            totalmin = duration // 60
            li.infoproperties['Duration'] = totalmin
            li.infoproperties['Duration_H'] = hours
            li.infoproperties['Duration_M'] = minutes
            li.infoproperties['Duration_HHMM'] = f'{hours:02d}:{minutes:02d}'

        def set_date_properties(li):
            premiered = li.infolabels.get('premiered')
            date_obj = convert_timestamp(premiered, time_fmt="%Y-%m-%d", time_lim=10)
            if not date_obj:
                return
            li.infoproperties['Premiered'] = get_region_date(date_obj, 'dateshort')
            li.infoproperties['Premiered_Long'] = get_region_date(date_obj, 'datelong')
            li.infoproperties['Premiered_Custom'] = date_obj.strftime(get_infolabel('Skin.String(TMDbHelper.Date.Format)') or '%d %b %Y')

        li = ListItem(**self._itemdetails.listitem)
        li.art = self.get_builtartwork()

        try:
            li.set_details(details=self.kodi_db.get_kodi_details(li), reverse=True)
        except AttributeError:
            pass

        set_time_properties(li)
        set_date_properties(li)

        return li.get_listitem()
