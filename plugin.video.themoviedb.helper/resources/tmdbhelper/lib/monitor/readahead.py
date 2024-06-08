from tmdbhelper.lib.monitor.itemdetails import ListItemDetails
from jurialmunkey.window import get_property, get_current_window
from tmdbhelper.lib.addon.plugin import get_setting

READAHEAD_QUEUE = [1, 2, 3, -1, 4, -2, 5, -3, 6, 7, 8, 9]  # Mostly only check items ahead but cache a few behind in case user scrolls back
READAHEAD_CHANGED = -1  # Underlying item changed in the meantime so we reset readahead on this condition
READAHEAD_SUCCESS = 0  # Got an item so will get next() on next while loop cycle
READAHEAD_COMPLETED = 1  # Exausted queue so we sit idle until item changes


class ListItemReadAhead():
    def __init__(self, parent, cur_window, cur_item):
        self._locked = False
        self._parent = parent
        self._pre_window = cur_window
        self._pre_item = cur_item
        self._queue = (x for x in READAHEAD_QUEUE)
        self._debug = get_setting('debug_logging')

    def _on_readahead(self, x):
        _item = ListItemDetails(self._parent, x)
        _item.setup_current_listitem()

        # If we already cached this item before then move to next queue
        if self._parent._item_memory_cache.get(f'_get_itemdetails_quick.{self._parent.get_item_identifier(x)}'):
            get_property('ReadAheadStatus', f'{x} - Skipped') if self._debug else None
            return self._next_readahead()

        if _item.get_itemdetails(func=None):
            _item.get_image_manipulations()
            _item.get_all_ratings()

        get_property('ReadAheadStatus', f'{x} - {_item._itemdetails.listitem["infolabels"].get("title")}') if self._debug else None
        return READAHEAD_SUCCESS

    def _next_readahead(self):
        if self._pre_window != get_current_window() or self._pre_item != self._parent.cur_item:
            get_property('ReadAheadStatus', 'WindowChanged') if self._debug else None
            return READAHEAD_CHANGED
        if not self._queue:
            get_property('ReadAheadStatus', 'QueueComplete') if self._debug else None
            return READAHEAD_COMPLETED
        try:
            return self._on_readahead(next(self._queue))
        except StopIteration:
            self._queue = None
            get_property('ReadAheadStatus', 'StopIteration') if self._debug else None
            return READAHEAD_COMPLETED

    def next_readahead(self):
        self._locked = True
        status = self._next_readahead()
        self._locked = False
        return status
