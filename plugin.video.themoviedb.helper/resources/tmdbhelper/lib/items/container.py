from jurialmunkey.parser import try_int, boolean
from tmdbhelper.lib.addon.consts import NO_UNAIRED_LABEL, NO_UNAIRED_CHECK, REMOVE_EPISODE_COUNT
from tmdbhelper.lib.addon.plugin import get_setting, executebuiltin, get_localized, get_condvisibility
from tmdbhelper.lib.api.contains import CommonContainerAPIs
from tmdbhelper.lib.addon.logger import TimerList


""" Lazyimports
from tmdbhelper.lib.items.kodi import KodiDb
"""


class Container(CommonContainerAPIs):
    def __init__(self, handle, paramstring, **kwargs):
        # Log Settings
        self.log_timers = get_setting('timer_reports')
        self.timer_lists = {}

        # plugin:// params configuration
        self.handle = handle  # plugin:// handle
        self.paramstring = paramstring  # plugin://plugin.video.themoviedb.helper?paramstring
        self.params = kwargs  # paramstring dictionary
        self.parent_params = self.params.copy()  # TODO: CLEANUP
        self.filters = {
            'filter_key': self.params.get('filter_key', None),
            'filter_value': self.params.get('filter_value', None),
            'filter_operator': self.params.get('filter_operator', None),
            'exclude_key': self.params.get('exclude_key', None),
            'exclude_value': self.params.get('exclude_value', None),
            'exclude_operator': self.params.get('exclude_operator', None)
        }

        # endOfDirectory
        self.update_listing = False  # endOfDirectory(updateListing=) set True to replace current path
        self.plugin_category = ''  # Container.PluginCategory / ListItem.Property(widget)
        self.container_content = ''  # Container.Content({})
        self.container_update = ''  # Add path to call Containr.Update({}) at end of directory
        self.container_refresh = False  # True call Container.Refresh at end of directory
        self.library = None  # TODO: FIX -- Currently broken -- SetInfo(library, info)
        self.sort_methods = []  # List of kwargs dictionaries [{'sortMethod': SORT_METHOD_UNSORTED}]
        self.sort_by_dbid = False

        # KodiDB
        self.kodi_db = None
        self.thumb_override = 0

    @property
    def is_fanarttv(self):
        try:
            return self._is_fanarttv
        except AttributeError:
            self._is_fanarttv = self.params.get('fanarttv', '').lower()
            return self._is_fanarttv

    @property
    def is_widget(self):
        try:
            return self._is_widget
        except AttributeError:
            self._is_widget = boolean(self.params.get('widget', False))
            return self._is_widget

    @property
    def is_cacheonly(self):
        try:
            return self._is_cacheonly
        except AttributeError:
            self._is_cacheonly = boolean(self.params.get('cacheonly', False))
            return self._is_cacheonly

    @property
    def is_detailed(self):
        try:
            return self._is_detailed
        except AttributeError:
            self._is_detailed = boolean(self.params.get('detailed', False)) or self.params.get('info') == 'details'
            return self._is_detailed

    @property
    def context_additions(self):
        try:
            return self._context_additions
        except AttributeError:
            self._context_additions = []
            if self.context_additions_make_node:
                self._context_additions += [(get_localized(32496), 'RunScript(plugin.video.themoviedb.helper,make_node)')]
            return self._context_additions

    @property
    def context_additions_make_node(self):
        try:
            return self._context_additions_make_node
        except AttributeError:
            self._context_additions_make_node = get_setting('contextmenu_make_node') if not self.is_widget else False
            return self._context_additions_make_node

    @property
    def hide_watched(self):
        try:
            return self._hide_watched
        except AttributeError:
            self._hide_watched = get_setting('widgets_hidewatched') if self.is_widget else False
            return self._hide_watched

    @property
    def nodate_is_unaired(self):
        try:
            return self._nodate_is_unaired
        except AttributeError:
            self._nodate_is_unaired = get_setting('nodate_is_unaired')
            return self._nodate_is_unaired

    @property
    def tmdb_cache_only(self):
        try:
            return self._tmdb_cache_only
        except AttributeError:
            def _tmdb_is_cache_only():
                if self.is_cacheonly:  # cacheonly=true param overrides all other settings
                    return True
                if not self.ftv_is_cache_only:  # fanarttv lookups require TMDb lookups for tvshow ID -- TODO: only force on tvshows
                    return False
                if get_setting('tmdb_details'):  # user setting
                    return False
                return True
            self._tmdb_cache_only = _tmdb_is_cache_only()
            return self._tmdb_cache_only

    @tmdb_cache_only.setter
    def tmdb_cache_only(self, value):
        self._tmdb_cache_only = value

    @property
    def is_excluded(self):
        try:
            return self._is_excluded
        except AttributeError:
            from tmdbhelper.lib.items.filters import is_excluded
            self._is_excluded = is_excluded
            return self._is_excluded

    @property
    def trakt_method(self):
        try:
            return self._trakt_method
        except AttributeError:
            from tmdbhelper.lib.items.trakt import TraktMethods
            self._trakt_method = TraktMethods(
                watchedindicators=get_setting('trakt_watchedindicators'),
                pauseplayprogress=get_setting('trakt_playprogress'),
                unwatchedepisodes=get_setting('trakt_watchedinprogress'))
            return self._trakt_method

    @property
    def ib(self):
        try:
            return self._ib
        except AttributeError:
            from tmdbhelper.lib.items.builder import ItemBuilder
            self._ib = ItemBuilder(
                tmdb_api=self.tmdb_api, ftv_api=self.ftv_api, trakt_api=self.trakt_api,
                log_timers=self.log_timers, timer_lists=self.timer_lists)
            return self._ib

    @property
    def page_length(self):
        if self.is_widget or not get_condvisibility('Window.IsVisible(MyVideoNav.xml)'):
            return 1
        return get_setting('pagemulti_library', 'int')

    @property
    def pagination(self):
        try:
            return self._pagination
        except AttributeError:
            def _pagination_is_allowed():
                if not boolean(self.params.get('nextpage', True)):
                    return False
                if self.is_widget and not get_setting('widgets_nextpage'):
                    return False
                return True

            self._pagination = _pagination_is_allowed()
            return self._pagination

    @property
    def ftv_is_cache_only(self):
        if self.is_cacheonly:  # cacheonly=true param overrides all other settings
            return True
        if self.is_fanarttv == 'true':
            return False
        if self.is_fanarttv == 'false':
            return True
        if self.is_widget and get_setting('widget_fanarttv_lookup'):  # user settings
            return False
        if not self.is_widget and get_setting('fanarttv_lookup'):  # user setting
            return False
        return True

    def get_kodi_database(self, tmdb_type):
        with TimerList(self.timer_lists, 'get_kodi', log_threshold=0.05, logging=self.log_timers):
            if not get_setting('local_db'):
                return
            from tmdbhelper.lib.items.kodi import KodiDb
            return KodiDb(tmdb_type)

    def _build_item(self, i):
        if not self.pagination and 'next_page' in i:
            return
        with TimerList(self.timer_lists, 'item_api', log_threshold=0.05, logging=self.log_timers):
            li = self.ib.get_listitem(i, use_iterprops=self.is_detailed)
            if li.infoproperties.get('plot_affix'):
                li.infolabels['plot'] = f"{li.infoproperties['plot_affix']}. {li.infolabels.get('plot')}"
            return li

    def _make_item(self, li):
        if not li:
            return

        with TimerList(self.timer_lists, 'item_abc', log_threshold=0.05, logging=self.log_timers):

            # Remove episode counts for some types of lists (eg stars_in_tvshows) where API uses episode_count for appearances instead of totalepisodes
            if self.remove_episode_counts:
                li.infolabels.pop('episode', None)

            # Reformat ListItem.Label for episodes to match Kodi default 1x01.Title
            li.set_episode_label()

            # Check if unaired and either apply special formatting or hide item depending on user settings
            if self.format_unaired_labels and not li.infoproperties.get('specialseason'):
                is_unaired = li.is_unaired(no_date=self.nodate_is_unaired)
                if self.remove_unaired_object and is_unaired:
                    return

            # Add details from Kodi library
            try:
                li.set_details(details=self.kodi_db.get_kodi_details(li), reverse=True)
            except AttributeError:
                pass

            # Filter out items that are excluded (done after adding Kodi details so can filter against them)
            if not li.next_page and self.is_excluded(li, is_listitem=True, **self.filters):
                return

        with TimerList(self.timer_lists, 'item_xyz', log_threshold=0.05, logging=self.log_timers):
            # Add Trakt playcount and watched status
            li.set_playcount(playcount=self.trakt_method.get_playcount(li))
            if self.hide_watched and try_int(li.infolabels.get('playcount')) != 0:
                return

            li.set_context_menu(additions=self.context_additions)  # Set the context menu items
            li.set_uids_to_info()  # Add unique ids to properties so accessible in skins
            li.set_thumb_to_art(self.thumb_override == 2) if self.thumb_override else None  # Special override for calendars to prevent thumb spoilers
            li.set_params_reroute(self.is_fanarttv, self.params.get('extended'), self.is_cacheonly)  # Reroute details to proper end point
            li.set_params_to_info(self.plugin_category)  # Set path params to properties for use in skins
            li.infoproperties.update(self.property_params or {})
            if self.thumb_override:
                li.infolabels.pop('dbid', None)  # Need to pop the DBID if overriding thumb to prevent Kodi overwriting
            if li.next_page:
                li.params['plugin_category'] = self.plugin_category  # Carry the plugin category to next page in plugin:// path
            self.trakt_method.set_playprogress(li)
            return li

    def precache_parent(self, tmdb_id, season=None):
        self.ib.get_parents(tmdb_type='tv', tmdb_id=tmdb_id, season=season)
        # PREBUILD_PARENTSHOW = ['seasons', 'episodes', 'episode_groups', 'trakt_upnext', 'episode_group_seasons']

    def build_items(self, items):
        """ Build items in threads """
        from tmdbhelper.lib.addon.thread import ParallelThread
        self.ib.cache_only = self.tmdb_cache_only
        with TimerList(self.timer_lists, '--build', log_threshold=0.05, logging=self.log_timers):
            self.ib.parent_params = self.parent_params
            with ParallelThread(items, self._build_item) as pt:
                item_queue = pt.queue
            all_listitems = [i for i in item_queue if i]

        # Wait for sync thread
        with TimerList(self.timer_lists, '--sync', log_threshold=0.05, logging=self.log_timers):
            self._pre_sync.join()

        # Finalise listitems in parallel threads
        with TimerList(self.timer_lists, '--make', log_threshold=0.05, logging=self.log_timers):
            info = self.parent_params.get('info')
            self.remove_unaired_object = info not in NO_UNAIRED_CHECK
            self.format_unaired_labels = info not in NO_UNAIRED_LABEL
            self.remove_episode_counts = info in REMOVE_EPISODE_COUNT
            with ParallelThread(all_listitems, self._make_item) as pt:
                item_queue = pt.queue

        if self.sort_by_dbid:
            item_queue_dbid = [li for li in item_queue if li and li.infolabels.get('dbid')]
            item_queue_tmdb = [li for li in item_queue if li and not li.infolabels.get('dbid')]
            item_queue = item_queue_dbid + item_queue_tmdb

        return item_queue

    def add_items(self, items):
        from xbmcplugin import addDirectoryItems
        addDirectoryItems(self.handle, [(li.get_url(), li.get_listitem(), li.is_folder) for li in items if li])

    def set_mixed_content(self, response):
        self.library = 'video'

        lengths = [
            len(response.get('movies', [])),
            len(response.get('shows', [])),
            len(response.get('persons', [])),
            len(response.get('seasons', [])),
            len(response.get('episodes', []))
        ]

        if lengths.index(max(lengths)) == 0:
            self.container_content = 'movies'
        elif lengths.index(max(lengths)) == 1:
            self.container_content = 'tvshows'
        elif lengths.index(max(lengths)) == 2:
            self.container_content = 'actors'
        elif lengths.index(max(lengths)) == 3:
            self.container_content = 'seasons'
        elif lengths.index(max(lengths)) == 4:
            self.container_content = 'episodes'

        if lengths[0] and (lengths[1] or lengths[3] or lengths[4]):
            self.kodi_db = self.get_kodi_database('both')
        elif lengths[0]:
            self.kodi_db = self.get_kodi_database('movie')
        elif (lengths[1] or lengths[3] or lengths[4]):
            self.kodi_db = self.get_kodi_database('tv')

    def set_params_to_container(self):
        params = {f'Param.{k}': f'{v}' for k, v in self.params.items() if k and v}
        if self.handle == -1:
            return params
        from xbmcplugin import setProperty
        for k, v in params.items():
            setProperty(self.handle, k, v)  # Set params to container properties
        return params

    def finish_container(self):
        from xbmcplugin import setPluginCategory, setContent, endOfDirectory, addSortMethod
        setPluginCategory(self.handle, self.plugin_category)  # Container.PluginCategory
        setContent(self.handle, self.container_content)  # Container.Content
        for i in self.sort_methods:
            addSortMethod(self.handle, **i)
        endOfDirectory(self.handle, updateListing=self.update_listing)

    def get_tmdb_id(self):

        if self.params.get('info') == 'collection' and self.params.get('tmdb_type') == 'movie':
            movie_tmdb_id = self.params.get('tmdb_id') or self.tmdb_api.get_tmdb_id(**self.params)
            self.params['tmdb_id'] = self.tmdb_api.get_collection_tmdb_id(movie_tmdb_id)
            self.params['tmdb_type'] = 'collection'
            return

        if self.params.get('tmdb_id'):
            return

        self.params['tmdb_id'] = self.tmdb_api.get_tmdb_id(**self.params)

    def get_items(self, **kwargs):
        """ Abstract method for getting items
        TODO: abc.abstractmethod to force ???
        """
        return

    def get_directory(self, items_only=False, build_items=True):
        from threading import Thread
        with TimerList(self.timer_lists, 'total', logging=self.log_timers):
            self._pre_sync = Thread(target=self.trakt_method.pre_sync, kwargs=self.params)
            self._pre_sync.start()
            with TimerList(self.timer_lists, 'get_list', logging=self.log_timers):
                items = self.get_items(**self.params)
            if not items:
                return
            if not build_items:
                return items
            self.property_params = self.set_params_to_container()
            self.plugin_category = self.params.get('plugin_category') or self.plugin_category
            with TimerList(self.timer_lists, 'add_items', logging=self.log_timers):
                items = self.build_items(items)
                if items_only:
                    return items
                self.add_items(items)
            self.finish_container()
        if self.log_timers:
            from tmdbhelper.lib.addon.logger import log_timer_report
            log_timer_report(self.timer_lists, self.paramstring)
        if self.container_update:
            executebuiltin(f'Container.Update({self.container_update})')
        if self.container_refresh:
            executebuiltin('Container.Refresh')
