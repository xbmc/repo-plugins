import xbmcgui
from tmdbhelper.lib.addon.plugin import get_infolabel, get_condvisibility, get_localized, get_setting, get_skindir
from tmdbhelper.lib.addon.logger import kodi_try_except
from jurialmunkey.window import get_property, get_current_window
from tmdbhelper.lib.monitor.common import CommonMonitorFunctions, SETMAIN_ARTWORK, SETPROP_RATINGS
from tmdbhelper.lib.monitor.itemdetails import ListItemDetails
from tmdbhelper.lib.monitor.readahead import ListItemReadAhead, READAHEAD_CHANGED
from tmdbhelper.lib.monitor.baseitem import BaseItemSkinDefaults
from tmdbhelper.lib.items.listitem import ListItem
from tmdbhelper.lib.files.bcache import BasicCache
from threading import Thread

CV_USE_LISTITEM = (
    "!Skin.HasSetting(TMDbHelper.ForceWidgetContainer) + "
    "!Window.IsActive(script-tmdbhelper-recommendations.xml) + ["
    "!Skin.HasSetting(TMDbHelper.UseLocalWidgetContainer) | String.IsEmpty(Window.Property(TMDbHelper.WidgetContainer))] + ["
    "Window.IsVisible(movieinformation) | "
    "Window.IsVisible(musicinformation) | "
    "Window.IsVisible(songinformation) | "
    "Window.IsVisible(addoninformation) | "
    "Window.IsVisible(pvrguideinfo) | "
    "Window.IsVisible(tvchannels) | "
    "Window.IsVisible(tvguide)]")

CV_USE_LOCAL_CONTAINER = "Skin.HasSetting(TMDbHelper.UseLocalWidgetContainer)"


class ListItemInfoGetter():
    def get_infolabel(self, info, position=0):
        return get_infolabel(f'{self._container_item.format(position)}{info}')

    def get_condvisibility(self, info, position=0):
        return get_condvisibility(f'{self._container_item.format(position)}{info}')

    def get_item_identifier(self, position=0):
        return str((
            'current_listitem_v5.1.17',
            self.get_infolabel('dbtype', position),
            self.get_infolabel('dbid', position),
            self.get_infolabel('IMDBNumber', position),
            self.get_infolabel('title', position) or self.get_infolabel('label', position),
            self.get_infolabel('tvshowtitle', position),
            self.get_infolabel('year', position),
            self.get_infolabel('season', position),
            self.get_infolabel('episode', position),))

    # ==========
    # PROPERTIES
    # ==========

    @property
    def cur_item(self):
        return self.get_item_identifier()

    @property
    def cur_window(self):
        return get_current_window()

    @property  # CHANGED _cur_window
    def widget_id(self):
        window_id = self._cur_window if get_condvisibility(CV_USE_LOCAL_CONTAINER) else None
        return get_property('WidgetContainer', window_id=window_id, is_type=int)

    @property  # CHANGED _widget_id and assign
    def container(self):
        return f'Container({self._widget_id}).' if self._widget_id else 'Container.'

    @property  # CHANGED _container
    def container_item(self):
        return 'ListItem.' if get_condvisibility(CV_USE_LISTITEM) else f'{self._container}ListItem({{}}).'

    @property
    def container_content(self):
        return get_infolabel('Container.Content()')

    # ==================
    # COMPARISON METHODS
    # ==================

    def is_same_item(self, update=False):
        self._cur_item = self.cur_item
        if self._cur_item == self._pre_item:
            return self._cur_item
        if update:
            self._pre_item = self._cur_item

    def is_same_window(self, update=True):
        self._cur_window = self.cur_window
        if self._cur_window == self._pre_window:
            return self._cur_window
        if update:
            self._pre_window = self._cur_window

    # ================
    # SETUP PROPERTIES
    # ================

    def setup_current_container(self):
        """ Cache property getter return values for performance """
        self._cur_window = self.cur_window
        self._widget_id = self.widget_id
        self._container = self.container
        self._container_item = self.container_item


class ListItemMonitorFunctions(CommonMonitorFunctions, ListItemInfoGetter):
    def __init__(self, parent):
        super(ListItemMonitorFunctions, self).__init__()
        self._cur_item = 0
        self._pre_item = 1
        self._cur_window = 0
        self._pre_window = 1
        self._cache = BasicCache(filename=f'QuickService.db')
        self._ignored_labels = ['..', get_localized(33078).lower(), get_localized(209).lower()]
        self._listcontainer = None
        self._last_listitem = None
        self._readahead = None
        self._item = None
        self.property_prefix = 'ListItem'
        self._clearfunc_wp = {'func': None}
        self._clearfunc_lc = {'func': None}
        self._readahead_li = get_setting('service_listitem_read_ahead')  # Allows readahead queue of next ListItems when idle
        self._pre_artwork_thread = None
        self._baseitem_skindefaults = BaseItemSkinDefaults()
        self._parent = parent

    # ==========
    # PROPERTIES
    # ==========

    @property
    def listcontainer_id(self):
        return int(get_infolabel('Skin.String(TMDbHelper.MonitorContainer)') or 0)

    @property
    def listcontainer(self):
        return self.get_listcontainer(self._cur_window, self._listcontainer_id)

    @property
    def baseitem_properties(self):
        infoproperties = {}
        for k, v, func in self._baseitem_skindefaults[get_skindir()]:
            if func == 'boolean':
                infoproperties[k] = 'True' if all([self.get_condvisibility(i) for i in v]) else None
                continue
            try:
                value = next(j for j in (self.get_infolabel(i) for i in v) if j)
                value = func(value) if func else value
                infoproperties[k] = value
            except StopIteration:
                infoproperties[k] = None
        return infoproperties

    # =======
    # GETTERS
    # =======

    def get_listcontainer(self, window_id=None, container_id=None):
        if not window_id or not container_id:
            return
        if not get_condvisibility(f'Control.IsVisible({container_id})'):
            return -1
        return container_id

    # ================
    # SETUP PROPERTIES
    # ================

    def setup_current_container(self):
        """ Cache property getter return values for performance """
        super().setup_current_container()
        self._listcontainer_id = self.listcontainer_id
        self._listcontainer = self.listcontainer

    def setup_current_item(self):
        self._item = ListItemDetails(self, position=0)
        self._item.setup_current_listitem()

    # =========
    # FUNCTIONS
    # =========

    def clear_properties(self, ignore_keys=None):
        super().clear_properties(ignore_keys=ignore_keys)

    def add_item_listcontainer(self, listitem, window_id=None, container_id=None):
        try:
            _win = xbmcgui.Window(window_id or self._cur_window)  # Note get _win separate from _lst
            _lst = _win.getControl(container_id or self._listcontainer)  # Note must get _lst in same func as addItem else crash
        except Exception:
            _lst = None
        if not _lst:
            return
        _lst.addItem(listitem)  # Note dont delay adding listitem after retrieving list else memory reference changes
        return listitem

    # =======
    # ACTIONS
    # =======

    def on_finalise_listcontainer(self, process_artwork=True, process_ratings=True):
        """ Constructs ListItem adds to hidden container
        process_artwork=True: Optional bool to process artwork
        process_ratings=True: Optional bool to process ratings
        Processing of artwork and ratings is done in a background thread to avoid locking main loop
        """
        _item = self._item
        _item.get_additional_properties(self.baseitem_properties)
        _listitem = self._last_listitem = _item.get_builtitem()
        _pre_item = self._pre_item
        _detailed = {'artwork': None, 'ratings': None}

        if _pre_item != self.cur_item:
            return

        self.add_item_listcontainer(_listitem)

        def _process_artwork():
            _artwork = _item.get_builtartwork()
            _artwork.update(_item.get_image_manipulations(built_artwork=_artwork, use_winprops=True))
            _detailed['artwork'] = _artwork

        def _process_ratings():
            _ratings = _item.get_all_ratings() or {}
            _ratings = _ratings.get('infoproperties')
            _detailed['ratings'] = _ratings

        def _process_artwork_ratings():
            self.get_property('IsUpdatingRatings', 'True')

            # Thread ratings and artwork processing
            t_artwork = Thread(target=_process_artwork) if process_artwork else None
            t_ratings = Thread(target=_process_ratings) if process_ratings else None
            t_artwork.start() if t_artwork else None
            t_ratings.start() if t_ratings else None

            # Wait for threads to join before readding listitem
            t_artwork.join() if t_artwork else None
            t_ratings.join() if t_ratings else None

            self.get_property('IsUpdatingRatings', clear_property=True)

            # Check focused item is still the same before updating
            if _pre_item != self.cur_item:
                return

            self._parent.images_monitor._pre_item = _pre_item

            _listitem.setArt(_detailed['artwork'] or {}) if process_artwork else None
            _listitem.setProperties(_detailed['ratings'] or {}) if process_ratings else None

        if process_artwork or process_ratings:
            t = Thread(target=_process_artwork_ratings)
            t.start()

    def on_finalise_winproperties(self, process_artwork=True, process_ratings=True):
        _item = self._item
        _item.get_additional_properties(self.baseitem_properties)
        _pre_item = self._pre_item

        if _pre_item != self.cur_item:
            return

        # Proces artwork in a thread
        def _process_artwork():
            _artwork = _item.get_builtartwork()
            _artwork.update(_item.get_image_manipulations(built_artwork=_artwork, use_winprops=False))
            _artwork_properties = set()

            with self._parent.mutex_lock:
                if _pre_item != self.cur_item:
                    return
                self._parent.images_monitor._pre_item = _pre_item
                self.set_iter_properties(_artwork, SETMAIN_ARTWORK, property_object=_artwork_properties)
                self.clear_property_list(SETMAIN_ARTWORK.difference(_artwork_properties))

        # Process ratings in a thread
        def _process_ratings():
            _details = _item.get_all_ratings() or {}
            _ratings_properties = set()

            with self._parent.mutex_lock:
                if _pre_item != self.cur_item:
                    return
                self.set_iter_properties(_details.get('infoproperties', {}), SETPROP_RATINGS, property_object=_ratings_properties)
                self.clear_property_list(SETPROP_RATINGS.difference(_ratings_properties))

        def _process_artwork_ratings():
            self.get_property('IsUpdatingRatings', 'True')

            # Thread ratings and artwork processing
            t_artwork = Thread(target=_process_artwork) if process_artwork else None
            t_ratings = Thread(target=_process_ratings) if process_ratings else None
            t_artwork.start() if t_artwork else None
            t_ratings.start() if t_ratings else None

            # Wait for threads to join before readding listitem
            t_artwork.join() if t_artwork else None
            t_ratings.join() if t_ratings else None

            self.get_property('IsUpdatingRatings', clear_property=True)

        if process_artwork or process_ratings:
            t = Thread(target=_process_artwork_ratings)
            t.start()

        with self._parent.mutex_lock:
            # Copy previous properties for clearing intersection
            prev_properties = self.properties.copy()
            self.properties = set()

            # Set our properties
            self.set_properties(_item._itemdetails.listitem, self.baseitem_properties)

            ignore_keys = prev_properties.intersection(self.properties)
            ignore_keys.update(SETPROP_RATINGS)
            ignore_keys.update(SETMAIN_ARTWORK)
            for k in prev_properties - ignore_keys:
                self.clear_property(k)

    def on_finalise(self):
        func = self.on_finalise_listcontainer if self._listcontainer else self.on_finalise_winproperties
        func(
            process_artwork=get_condvisibility("!Skin.HasSetting(TMDbHelper.DisableArtwork)"),
            process_ratings=get_condvisibility("!Skin.HasSetting(TMDbHelper.DisableRatings)"))
        self.get_property('IsUpdating', clear_property=True)

    def on_readahead(self):
        # No readahead if disabled by user
        if not self._readahead_li:
            return

        # No readahead in info dialog
        if get_condvisibility(CV_USE_LISTITEM):
            return

        # No readahead has started so let's start one
        if not self._readahead:
            self._readahead = ListItemReadAhead(self, self._cur_window, self._cur_item)

        # Readahead next item and if the main item changes in the meantime we reset to None
        def _next_readahead():
            if self._readahead._locked:
                return
            if self._readahead.next_readahead() != READAHEAD_CHANGED:
                return
            self._readahead = None

        # Readahead is threaded to avoid locking up main lookup while loop
        t = Thread(target=_next_readahead)
        t.start()

    @kodi_try_except('lib.monitor.listitem.on_listitem')
    def on_listitem(self):
        self.setup_current_container()

        # We want to set a special container but it doesn't exist so exit
        if self._listcontainer == -1:
            return

        # Check if the item has changed before retrieving details again
        if self.is_same_window(update=True) and self.is_same_item(update=True):
            return self.on_readahead()

        # Ignore some special folders like next page and parent folder
        if (self.get_infolabel('Label') or '').lower().split(' (', 1)[0] in self._ignored_labels:
            return self.on_exit()

        # Set a property for skins to check if item details are updating
        self.get_property('IsUpdating', 'True')

        # Get the current listitem details for the details lookup
        self.setup_current_item()

        # Get item details
        uncached_func = self._clearfunc_lc if self._listcontainer else self._clearfunc_wp
        self._item.get_itemdetails(**uncached_func)

        # Get library stats for person
        if get_condvisibility("!Skin.HasSetting(TMDbHelper.DisablePersonStats)"):
            self._item.get_person_stats()

        # Finish up setting our details to the container/window
        self.on_finalise()

    @kodi_try_except('lib.monitor.listitem.on_context_listitem')
    def on_context_listitem(self):
        if not self._last_listitem:
            return
        _id_dialog = xbmcgui.getCurrentWindowDialogId()
        _id_d_list = self.get_listcontainer(_id_dialog, self._listcontainer_id)
        if not _id_d_list or _id_d_list == -1:
            return
        _id_window = xbmcgui.getCurrentWindowId()
        _id_w_list = self.get_listcontainer(_id_window, self._listcontainer_id)
        if not _id_w_list or _id_w_list == -1:
            return
        self.add_item_listcontainer(self._last_listitem, _id_dialog, _id_d_list)

    def on_scroll(self):
        return

    def on_exit(self, is_done=True):

        if self._listcontainer:
            self.add_item_listcontainer(ListItem().get_listitem())

        self.clear_properties()

        if is_done:
            self.get_property('IsUpdating', clear_property=True)
