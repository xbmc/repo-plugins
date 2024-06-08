from xbmc import Monitor
from tmdbhelper.lib.addon.plugin import get_setting, get_condvisibility
from jurialmunkey.window import get_property, wait_for_property
from tmdbhelper.lib.monitor.cronjob import CronJobMonitor
from tmdbhelper.lib.monitor.listitem import ListItemMonitor
from tmdbhelper.lib.monitor.player import PlayerMonitor
from tmdbhelper.lib.monitor.update import UpdateMonitor
from threading import Thread


def restart_service_monitor():
    if get_property('ServiceStarted') == 'True':
        wait_for_property('ServiceStop', value='True', set_property=True)  # Stop service
    wait_for_property('ServiceStop', value=None)  # Wait until Service clears property
    Thread(target=ServiceMonitor().run).start()


class ServiceMonitor(object):
    def __init__(self):
        self.exit = False
        self.listitem = None
        self.cron_job = CronJobMonitor(get_setting('library_autoupdate_hour', 'int'))
        self.cron_job.setName('Cron Thread')
        self.player_monitor = None
        self.update_monitor = None
        self.listitem_monitor = ListItemMonitor()
        self.xbmc_monitor = Monitor()

    def _on_listitem(self):
        self.listitem_monitor.on_listitem()
        self.xbmc_monitor.waitForAbort(0.2)

    def _on_scroll(self):
        self.listitem_monitor.on_scroll_clear()
        self.xbmc_monitor.waitForAbort(0.2)

    def _on_fullscreen(self):
        if self.player_monitor.isPlayingVideo():
            self.player_monitor.current_time = self.player_monitor.getTime()
        if get_condvisibility(
                "Skin.HasSetting(TMDbHelper.UseLocalWidgetContainer) + ["
                "!String.IsEmpty(Window.Property(TMDbHelper.WidgetContainer)) | "
                "Window.IsVisible(movieinformation) | "
                "Window.IsVisible(musicinformation) | "
                "Window.IsVisible(songinformation) | "
                "Window.IsVisible(addoninformation) | "
                "Window.IsVisible(pvrguideinfo)]"):
            return self._on_listitem()
        self.xbmc_monitor.waitForAbort(1)

    def _on_idle(self, wait_time=30):
        self.xbmc_monitor.waitForAbort(wait_time)

    def _on_modal(self):
        self.xbmc_monitor.waitForAbort(1)

    def _on_context(self):
        self.listitem_monitor.on_context_listitem()
        self.xbmc_monitor.waitForAbort(1)

    def _on_clear(self):
        """
        IF we've got properties to clear lets clear them and then jump back in the loop
        Otherwise we should sit for a second so we aren't constantly polling
        """
        if self.listitem_monitor.properties or self.listitem_monitor.index_properties:
            return self.listitem_monitor.clear_properties()
        self.listitem_monitor.blur_fallback()
        self.xbmc_monitor.waitForAbort(1)

    def _on_exit(self):
        if not self.xbmc_monitor.abortRequested():
            self.listitem_monitor.clear_properties()
            get_property('ServiceStarted', clear_property=True)
            get_property('ServiceStop', clear_property=True)
        del self.player_monitor
        del self.update_monitor
        del self.listitem_monitor
        del self.xbmc_monitor

    def poller(self):
        while not self.xbmc_monitor.abortRequested() and not self.exit:
            if get_property('ServiceStop'):
                self.cron_job.exit = True
                self.exit = True

            # If we're in fullscreen video then we should update the playermonitor time
            elif get_condvisibility("Window.IsVisible(fullscreenvideo)"):
                self._on_fullscreen()

            # Sit idle in a holding pattern if the skin doesn't need the service monitor yet
            elif get_condvisibility(
                    "!Skin.HasSetting(TMDbHelper.Service) + "
                    "!Skin.HasSetting(TMDbHelper.EnableBlur) + "
                    "!Skin.HasSetting(TMDbHelper.EnableDesaturate) + "
                    "!Skin.HasSetting(TMDbHelper.EnableColors)"):
                self._on_idle(30)

            # Sit idle in a holding pattern if screen saver is active
            elif get_condvisibility("System.ScreenSaverActive"):
                self._on_idle(4)

            # skip when modal or busy dialogs are opened (e.g. select / progress / busy etc.)
            elif get_condvisibility(
                    "Window.IsActive(DialogSelect.xml) | "
                    "Window.IsActive(progressdialog) | "
                    "Window.IsActive(busydialog) | "
                    "Window.IsActive(shutdownmenu) | "
                    "!String.IsEmpty(Window.Property(TMDbHelper.ServicePause))"):
                self._on_modal()

            # manage context menu separately from other modals to pass info through
            elif get_condvisibility(
                    "Window.IsActive(contextmenu) | "
                    "!String.IsEmpty(Window.Property(TMDbHelper.ContextMenu))"):
                self._on_context()

            # skip when container scrolling
            elif get_condvisibility("Container.Scrolling"):
                self._on_scroll()

            # media window is opened or widgetcontainer set - start listitem monitoring!
            elif get_condvisibility(
                    "Window.IsMedia | "
                    "!String.IsEmpty(Window(Home).Property(TMDbHelper.WidgetContainer)) | "
                    "!String.IsEmpty(Window.Property(TMDbHelper.WidgetContainer)) | "
                    "Window.IsVisible(movieinformation) | "
                    "Window.IsVisible(musicinformation) | "
                    "Window.IsVisible(songinformation) | "
                    "Window.IsVisible(addoninformation) | "
                    "Window.IsVisible(pvrguideinfo) | "
                    "Window.IsVisible(tvchannels) | "
                    "Window.IsVisible(tvguide)"):
                self._on_listitem()

            # Otherwise just sit here and wait
            else:
                self._on_clear()

        # Some clean-up once service exits
        self._on_exit()

    def run(self):
        get_property('ServiceStarted', 'True')
        self.cron_job.start()
        self.player_monitor = PlayerMonitor()
        self.update_monitor = UpdateMonitor()
        self.poller()
