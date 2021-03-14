import xbmc
from resources.lib.addon.window import get_property, wait_for_property
from resources.lib.addon.plugin import ADDON
from resources.lib.monitor.cronjob import CronJobMonitor
from resources.lib.monitor.listitem import ListItemMonitor
from resources.lib.monitor.player import PlayerMonitor
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
        self.cron_job = CronJobMonitor(ADDON.getSettingInt('library_autoupdate_hour'))
        self.cron_job.setName('Cron Thread')
        self.player_monitor = None
        self.listitem_monitor = ListItemMonitor()
        self.xbmc_monitor = xbmc.Monitor()

    def _on_listitem(self):
        self.listitem_monitor.get_listitem()
        self.xbmc_monitor.waitForAbort(0.3)

    def _on_scroll(self):
        self.listitem_monitor.clear_on_scroll()
        self.xbmc_monitor.waitForAbort(1)

    def _on_fullscreen(self):
        if self.player_monitor.isPlayingVideo():
            self.player_monitor.current_time = self.player_monitor.getTime()
        self.xbmc_monitor.waitForAbort(1)

    def _on_idle(self):
        self.xbmc_monitor.waitForAbort(30)

    def _on_modal(self):
        self.xbmc_monitor.waitForAbort(2)

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
        del self.listitem_monitor
        del self.xbmc_monitor

    def poller(self):
        while not self.xbmc_monitor.abortRequested() and not self.exit:
            if get_property('ServiceStop'):
                self.cron_job.exit = True
                self.exit = True

            # If we're in fullscreen video then we should update the playermonitor time
            elif xbmc.getCondVisibility("Window.IsVisible(fullscreenvideo)"):
                self._on_fullscreen()

            # Sit idle in a holding pattern if the skin doesn't need the service monitor yet
            elif xbmc.getCondVisibility(
                    "System.ScreenSaverActive | "
                    "[!Skin.HasSetting(TMDbHelper.Service) + "
                    "!Skin.HasSetting(TMDbHelper.EnableBlur) + "
                    "!Skin.HasSetting(TMDbHelper.EnableDesaturate) + "
                    "!Skin.HasSetting(TMDbHelper.EnableColors)]"):
                self._on_idle()

            # skip when modal / busy dialogs are opened (e.g. context / select / busy etc.)
            elif xbmc.getCondVisibility(
                    "Window.IsActive(DialogSelect.xml) | "
                    "Window.IsActive(progressdialog) | "
                    "Window.IsActive(contextmenu) | "
                    "Window.IsActive(busydialog) | "
                    "Window.IsActive(shutdownmenu)"):
                self._on_modal()

            # skip when container scrolling
            elif xbmc.getCondVisibility(
                    "Container.OnScrollNext | "
                    "Container.OnScrollPrevious | "
                    "Container.Scrolling"):
                self._on_scroll()

            # media window is opened or widgetcontainer set - start listitem monitoring!
            elif xbmc.getCondVisibility(
                    "Window.IsMedia | "
                    "Window.IsVisible(MyPVRChannels.xml) | "
                    "Window.IsVisible(MyPVRGuide.xml) | "
                    "Window.IsVisible(DialogPVRInfo.xml) | "
                    "!String.IsEmpty(Window(Home).Property(TMDbHelper.WidgetContainer)) | "
                    "Window.IsVisible(movieinformation)"):
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
        self.poller()
