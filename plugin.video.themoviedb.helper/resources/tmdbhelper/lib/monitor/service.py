from tmdbhelper.lib.addon.plugin import get_setting
from jurialmunkey.window import get_property, wait_for_property
from tmdbhelper.lib.monitor.listitemtools import ListItemMonitorFunctions
from tmdbhelper.lib.monitor.cronjob import CronJobMonitor
from tmdbhelper.lib.monitor.player import PlayerMonitor
from tmdbhelper.lib.monitor.update import UpdateMonitor
from tmdbhelper.lib.monitor.imgmon import ImagesMonitor
from tmdbhelper.lib.monitor.poller import Poller, POLL_MIN_INCREMENT, POLL_MID_INCREMENT
from threading import Thread, Lock


class ServiceMonitor(Poller):
    def __init__(self):
        self.exit = False
        self.listitem = None

    def run(self):
        self.mutex_lock = Lock()

        self.update_monitor = UpdateMonitor()
        self.player_monitor = PlayerMonitor()

        self.cron_job = CronJobMonitor(self, update_hour=get_setting('library_autoupdate_hour', 'int'))
        self.cron_job.setName('Cron Thread')
        self.cron_job.start()

        self.images_monitor = ImagesMonitor(self)
        self.images_monitor.setName('Image Thread')
        self.images_monitor.start()

        self.listitem_funcs = ListItemMonitorFunctions(self)

        get_property('ServiceStarted', 'True')

        self.poller()

    def _on_listitem(self):
        self.listitem_funcs.on_listitem()
        self._on_idle(POLL_MIN_INCREMENT)

    def _on_scroll(self):
        self.listitem_funcs.on_scroll()
        self._on_idle(POLL_MIN_INCREMENT)

    def _on_player(self):
        if self.player_monitor.isPlayingVideo():
            self.player_monitor.current_time = self.player_monitor.getTime()

    def _on_context(self):
        self.listitem_funcs.on_context_listitem()
        self._on_idle(POLL_MID_INCREMENT)

    def _on_clear(self):
        """
        IF we've got properties to clear lets clear them and then jump back in the loop
        Otherwise we should sit for a second so we aren't constantly polling
        """
        if self.listitem_funcs.properties or self.listitem_funcs.index_properties:
            return self.listitem_funcs.clear_properties()
        self._on_idle(POLL_MID_INCREMENT)

    def _on_exit(self):
        self.cron_job.exit = True
        if not self.update_monitor.abortRequested():
            get_property('ServiceStarted', clear_property=True)
            get_property('ServiceStop', clear_property=True)
        del self.images_monitor
        del self.player_monitor
        del self.update_monitor
        del self.listitem_funcs


def restart_service_monitor():
    if get_property('ServiceStarted') == 'True':
        wait_for_property('ServiceStop', value='True', set_property=True)  # Stop service
    wait_for_property('ServiceStop', value=None)  # Wait until Service clears property
    Thread(target=ServiceMonitor().run).start()
