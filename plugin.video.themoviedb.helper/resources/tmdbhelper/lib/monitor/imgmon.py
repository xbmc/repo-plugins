from tmdbhelper.lib.monitor.images import ImageManipulations
from tmdbhelper.lib.monitor.poller import Poller, POLL_MIN_INCREMENT
from tmdbhelper.lib.monitor.listitemtools import ListItemInfoGetter
from tmdbhelper.lib.addon.logger import kodi_try_except
from threading import Thread


class ImagesMonitor(Thread, ListItemInfoGetter, ImageManipulations, Poller):
    def __init__(self, parent):
        Thread.__init__(self)
        self._cur_item = 0
        self._pre_item = 1
        self._cur_window = 0
        self._pre_window = 1
        self.exit = False
        self.update_monitor = parent.update_monitor
        self.crop_image_cur = None
        self.blur_image_cur = None
        self._allow_on_scroll = True  # Allow updating while scrolling
        self._parent = parent

    @kodi_try_except('lib.monitor.imgmon.on_listitem')
    def on_listitem(self):
        with self._parent.mutex_lock:
            self.setup_current_container()
            if self.is_same_item(update=True):
                return
            self.get_image_manipulations(use_winprops=True)

    def _on_listitem(self):
        self.on_listitem()
        self._on_idle(POLL_MIN_INCREMENT)

    def _on_scroll(self):
        if self._allow_on_scroll:
            return self._on_listitem()
        self._on_idle(POLL_MIN_INCREMENT)

    def run(self):
        self.poller()
