from resources.lib.api.kodi.rpc import get_person_stats
from resources.lib.addon.window import get_property
from resources.lib.monitor.common import CommonMonitorFunctions, SETMAIN_ARTWORK, SETPROP_RATINGS
from resources.lib.monitor.images import ImageFunctions
from resources.lib.addon.plugin import convert_media_type, convert_type, get_setting, get_infolabel, get_condvisibility
from resources.lib.addon.logger import kodi_try_except
from threading import Thread


def get_container():
    widget_id = get_property('WidgetContainer', is_type=int)
    if widget_id:
        return f'Container({widget_id}).'
    return 'Container.'


def get_container_item(container=None):
    if get_condvisibility(
            "[Window.IsVisible(DialogPVRInfo.xml) | Window.IsVisible(MyPVRGuide.xml) | "
            "Window.IsVisible(movieinformation)] + "
            "!Skin.HasSetting(TMDbHelper.ForceWidgetContainer)"):
        return 'ListItem.'
    return f'{container or get_container()}ListItem.'


class ListItemMonitor(CommonMonitorFunctions):
    def __init__(self):
        super(ListItemMonitor, self).__init__()
        self.cur_item = 0
        self.pre_item = 1
        self.cur_folder = None
        self.pre_folder = None
        self.property_prefix = 'ListItem'
        self._last_blur_fallback = False

    def get_container(self):
        self.container = get_container()
        self.container_item = get_container_item(self.container)

    def get_infolabel(self, infolabel):
        return get_infolabel(f'{self.container_item}{infolabel}')

    def get_position(self):
        return get_infolabel(f'{self.container}CurrentItem')

    def get_numitems(self):
        return get_infolabel(f'{self.container}NumItems')

    def get_imdb_id(self):
        imdb_id = self.get_infolabel('IMDBNumber') or ''
        if imdb_id.startswith('tt'):
            return imdb_id
        return ''

    def get_query(self):
        if self.get_infolabel('TvShowTitle'):
            return self.get_infolabel('TvShowTitle')
        if self.get_infolabel('Title'):
            return self.get_infolabel('Title')
        if self.get_infolabel('Label'):
            return self.get_infolabel('Label')

    def get_season(self):
        if self.dbtype == 'episodes':
            return self.get_infolabel('Season')

    def get_episode(self):
        if self.dbtype == 'episodes':
            return self.get_infolabel('Episode')

    def get_dbtype(self):
        if self.get_infolabel('Property(tmdb_type)') == 'person':
            return 'actors'
        dbtype = self.get_infolabel('dbtype')
        if dbtype:
            return f'{dbtype}s'
        if get_condvisibility(
                "Window.IsVisible(DialogPVRInfo.xml) | "
                "Window.IsVisible(MyPVRChannels.xml) | "
                "Window.IsVisible(MyPVRRecordings.xml) | "
                "Window.IsVisible(MyPVRSearch.xml) | "
                "Window.IsVisible(MyPVRGuide.xml)"):
            return 'multi' if get_condvisibility("!Skin.HasSetting(TMDbHelper.DisablePVR)") else ''
        if self.container == 'Container.':
            return get_infolabel('Container.Content()') or ''
        return ''

    def get_tmdb_type(self, dbtype=None):
        dbtype = dbtype or self.dbtype
        if dbtype == 'multi':
            return 'multi'
        return convert_media_type(dbtype, 'tmdb', strip_plural=True, parent_type=True)

    def set_cur_item(self):
        self.dbtype = self.get_dbtype()
        self.dbid = self.get_infolabel('dbid')
        self.imdb_id = self.get_imdb_id()
        self.query = self.get_query()
        self.year = self.get_infolabel('year')
        self.season = self.get_season()
        self.episode = self.get_episode()

    def get_cur_item(self):
        return (
            'current_item',
            self.get_infolabel('dbtype'),
            self.get_infolabel('dbid'),
            self.get_infolabel('IMDBNumber'),
            self.get_infolabel('label'),
            self.get_infolabel('year'),
            self.get_infolabel('season'),
            self.get_infolabel('episode'),)

    def is_same_item(self, update=False):
        self.cur_item = self.get_cur_item()
        if self.cur_item == self.pre_item:
            return self.cur_item
        if update:
            self.pre_item = self.cur_item

    def get_cur_folder(self):
        return ('current_folder', self.container, get_infolabel('Container.Content()'), self.get_numitems(),)

    def clear_properties(self, ignore_keys=None):
        if not self.get_artwork(source="Art(artist.clearlogo)|Art(tvshow.clearlogo)|Art(clearlogo)"):
            self.properties.update({'CropImage', 'CropImage.Original'})
        super().clear_properties(ignore_keys=ignore_keys)

    @kodi_try_except('lib.monitor.listitem.is_same_folder')
    def is_same_folder(self, update=True):
        self.cur_folder = self.get_cur_folder()
        if self.cur_folder == self.pre_folder:
            return self.cur_folder
        if update:
            self.pre_folder = self.cur_folder

    @kodi_try_except('lib.monitor.listitem.process_artwork')
    def process_artwork(self, artwork, tmdb_type):
        self.clear_property_list(SETMAIN_ARTWORK)
        if not self.is_same_item():
            return
        artwork = self.ib.get_item_artwork(artwork, is_season=True if self.season else False)
        self.set_iter_properties(artwork, SETMAIN_ARTWORK)

        # Crop Image
        if get_condvisibility("Skin.HasSetting(TMDbHelper.EnableCrop)"):
            if self.get_artwork(source="Art(artist.clearlogo)|Art(tvshow.clearlogo)|Art(clearlogo)"):
                return  # We already cropped listitem artwork so we only crop here if it didn't have a clearlogo and we need to look it up
            ImageFunctions(method='crop', is_thread=False, artwork=artwork.get('clearlogo')).run()

    @kodi_try_except('lib.monitor.listitem.process_ratings')
    def process_ratings(self, details, tmdb_type):
        try:
            trakt_type = {'movie': 'movie', 'tv': 'show'}[tmdb_type]
        except KeyError:
            return  # Only lookup ratings for movie or tvshow
        get_property('IsUpdatingRatings', 'True')
        details = self.get_omdb_ratings(details)
        details = self.get_imdb_top250_rank(details, trakt_type=trakt_type)
        details = self.get_trakt_ratings(details, trakt_type, season=self.season, episode=self.episode)
        if not self.is_same_item():
            return get_property('IsUpdatingRatings', clear_property=True)
        self.set_iter_properties(details.get('infoproperties', {}), SETPROP_RATINGS)
        get_property('IsUpdatingRatings', clear_property=True)

    @kodi_try_except('lib.monitor.listitem.clear_on_scroll')
    def clear_on_scroll(self):
        if not self.properties and not self.index_properties:
            return
        if self.is_same_item():
            return
        ignore_keys = None
        if self.dbtype in ['episodes', 'seasons']:
            ignore_keys = SETMAIN_ARTWORK
        self.clear_properties(ignore_keys=ignore_keys)

    @kodi_try_except('lib.monitor.listitem.get_artwork')
    def get_artwork(self, source='', fallback=''):
        source = source.lower()
        lookup = {
            'poster': ['Art(tvshow.poster)', 'Art(poster)', 'Art(thumb)'],
            'fanart': ['Art(fanart)', 'Art(thumb)'],
            'landscape': ['Art(landscape)', 'Art(fanart)', 'Art(thumb)'],
            'thumb': ['Art(thumb)']}
        infolabels = lookup.get(source, source.split("|") if source else lookup.get('thumb'))
        for i in infolabels:
            artwork = self.get_infolabel(i)
            if artwork:
                return artwork
        return fallback

    @kodi_try_except('lib.monitor.listitem.blur_fallback')
    def blur_fallback(self):
        if self._last_blur_fallback:
            return
        fallback = get_property('Blur.Fallback')
        if not fallback:
            return
        if get_condvisibility("Skin.HasSetting(TMDbHelper.EnableBlur)"):
            self.blur_img = ImageFunctions(method='blur', artwork=fallback)
            self.blur_img.setName('blur_img')
            self.blur_img.start()
            self._last_blur_fallback = True

    def run_imagefuncs(self):
        # Blur Image
        if get_condvisibility("Skin.HasSetting(TMDbHelper.EnableBlur)"):
            ImageFunctions(method='blur', is_thread=False, artwork=self.get_artwork(
                source=get_property('Blur.SourceImage'),
                fallback=get_property('Blur.Fallback'))).run()
            self._last_blur_fallback = False

        # Desaturate Image
        if get_condvisibility("Skin.HasSetting(TMDbHelper.EnableDesaturate)"):
            ImageFunctions(method='desaturate', is_thread=False, artwork=self.get_artwork(
                source=get_property('Desaturate.SourceImage'),
                fallback=get_property('Desaturate.Fallback'))).run()

        # CompColors
        if get_condvisibility("Skin.HasSetting(TMDbHelper.EnableColors)"):
            ImageFunctions(method='colors', is_thread=False, artwork=self.get_artwork(
                source=get_property('Colors.SourceImage'),
                fallback=get_property('Colors.Fallback'))).run()

        # Cropping
        if get_condvisibility("Skin.HasSetting(TMDbHelper.EnableCrop)"):
            if self.get_artwork(source="Art(artist.clearlogo)|Art(tvshow.clearlogo)|Art(clearlogo)"):
                ImageFunctions(method='crop', is_thread=False, artwork=self.get_artwork(
                    source="Art(artist.clearlogo)|Art(tvshow.clearlogo)|Art(clearlogo)")).run()

    @kodi_try_except('lib.monitor.listitem.get_listitem')
    def get_listitem(self):
        self.get_container()

        # Don't bother getting new details if we've got the same item
        if self.is_same_item(update=True):
            return

        # Parent folder item so clear properties and stop
        if self.get_infolabel('Label') == '..':
            return self.clear_properties()

        # Set our is_updating flag
        get_property('IsUpdating', 'True')

        # If the folder changed let's clear all the properties before doing a look-up
        # Possible that our new look-up will fail so good to have a clean slate
        if not self.is_same_folder(update=True):
            self.clear_properties()

        # Get look-up details
        self.set_cur_item()

        # Do image functions for blur crop etc. in a separate thread
        Thread(target=self.run_imagefuncs).start()

        # Allow early exit to only do image manipulations
        if get_condvisibility("!Skin.HasSetting(TMDbHelper.Service)"):
            return get_property('IsUpdating', clear_property=True)

        # Need a TMDb type to do a details look-up so exit if we don't have one
        tmdb_type = self.get_tmdb_type()
        if not tmdb_type:
            self.clear_properties(ignore_keys={'cur_item'})
            return get_property('IsUpdating', clear_property=True)

        # Immediately clear some properties like ratings and artwork
        # Don't want these to linger on-screen if the look-up takes a moment
        if self.dbtype not in ['episodes', 'seasons']:
            self.clear_property_list(SETMAIN_ARTWORK)
        self.clear_property_list(SETPROP_RATINGS)

        # Get TMDb Details
        self.multisearch_tmdbtype = None
        tmdb_id = self.get_tmdb_id(
            tmdb_type=tmdb_type,
            query=self.query,
            imdb_id=self.imdb_id if not self.season else None,  # Skip IMDb ID for seasons/episodes as we can't distinguish if the ID is for the episode or the show.
            year=self.year if tmdb_type == 'movie' else None,
            episode_year=self.year if tmdb_type == 'tv' else None,
            media_type='tv' if tmdb_type == 'multi' and (self.get_infolabel('episode') or self.get_infolabel('season')) else None)
        if tmdb_type == 'multi':
            tmdb_type = self.multisearch_tmdbtype
            self.dbtype = convert_type(tmdb_type, 'dbtype')
        self.ib.ftv_api = self.ftv_api if get_setting('service_fanarttv_lookup') else None
        details = self.ib.get_item(tmdb_type, tmdb_id, self.season, self.episode)
        if details:
            artwork = details['artwork']
            details = details['listitem']
        if not details:
            self.clear_properties(ignore_keys={'cur_item'})
            return get_property('IsUpdating', clear_property=True)

        # Need to update Next Aired with a shorter cache time than details
        if tmdb_type == 'tv':
            details['infoproperties'].update(self.tmdb_api.get_tvshow_nextaired(tmdb_id))

        # Get our artwork properties
        if get_condvisibility("!Skin.HasSetting(TMDbHelper.DisableArtwork)"):
            thread_artwork = Thread(target=self.process_artwork, args=[artwork, tmdb_type])
            thread_artwork.start()

        # Item changed whilst retrieving details so lets clear and get next item
        if not self.is_same_item():
            ignore_keys = None
            if self.dbtype in ['episodes', 'seasons']:
                ignore_keys = SETMAIN_ARTWORK
            self.clear_properties(ignore_keys=ignore_keys)
            return get_property('IsUpdating', clear_property=True)

        # Get person library statistics
        if tmdb_type == 'person' and details.get('infolabels', {}).get('title'):
            if get_condvisibility("!Skin.HasSetting(TMDbHelper.DisablePersonStats)"):
                details.setdefault('infoproperties', {}).update(
                    get_person_stats(details['infolabels']['title']) or {})

        # Get our item ratings
        if get_condvisibility("!Skin.HasSetting(TMDbHelper.DisableRatings)"):
            thread_ratings = Thread(target=self.process_ratings, args=[details, tmdb_type])
            thread_ratings.start()

        self.set_properties(details)
        get_property('IsUpdating', clear_property=True)
