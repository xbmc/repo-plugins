from tmdbhelper.lib.addon.plugin import get_condvisibility
from jurialmunkey.window import get_property


POLL_MIN_INCREMENT = 0.2
POLL_MID_INCREMENT = 1
POLL_MAX_INCREMENT = 2


ON_DISABLED = (
    "!Skin.HasSetting(TMDbHelper.Service) + "
    "!Skin.HasSetting(TMDbHelper.EnableBlur) + "
    "!Skin.HasSetting(TMDbHelper.EnableDesaturate) + "
    "!Skin.HasSetting(TMDbHelper.EnableColors)")

ON_MODAL = (
    "["
    "Window.IsVisible(DialogSelect.xml) | "
    "Window.IsVisible(DialogKeyboard.xml) | "
    "Window.IsVisible(DialogNumeric.xml) | "
    "Window.IsVisible(DialogConfirm.xml) | "
    "Window.IsVisible(DialogSettings.xml) | "
    "Window.IsVisible(DialogMediaSource.xml) | "
    "Window.IsVisible(DialogTextViewer.xml) | "
    "Window.IsVisible(DialogSlider.xml) | "
    "Window.IsVisible(DialogSubtitles.xml) | "
    "Window.IsVisible(DialogFavourites.xml) | "
    "Window.IsVisible(DialogColorPicker.xml) | "
    "Window.IsVisible(FileBrowser.xml) | "
    "Window.IsVisible(progressdialog) | "
    "Window.IsVisible(busydialog) | "
    "Window.IsVisible(shutdownmenu) | "
    "!String.IsEmpty(Window.Property(TMDbHelper.ServicePause))"
    "]")

ON_INFODIALOG = (
    "["
    "Window.IsVisible(movieinformation) | "
    "Window.IsVisible(musicinformation) | "
    "Window.IsVisible(songinformation) | "
    "Window.IsVisible(pvrguideinfo) | "
    "Window.IsVisible(tvchannels) | "
    "Window.IsVisible(tvguide)"
    "]")

ON_LISTITEM = (
    "["
    "Window.IsMedia | "
    "!String.IsEmpty(Window(Home).Property(TMDbHelper.WidgetContainer)) | "
    "!String.IsEmpty(Window.Property(TMDbHelper.WidgetContainer))"
    "] | ") + ON_INFODIALOG

ON_FULLSCREEN_LISTITEM = (
    "["
    "Skin.HasSetting(TMDbHelper.UseLocalWidgetContainer) + "
    "!String.IsEmpty(Window.Property(TMDbHelper.WidgetContainer))"
    "] | ") + ON_INFODIALOG

ON_SCROLL = "Container.Scrolling"

ON_CONTEXT = (
    "Window.IsVisible(contextmenu) | "
    "Window.IsVisible(DialogVideoManager.xml) | "
    "Window.IsVisible(DialogAddonSettings.xml) | "
    "Window.IsVisible(DialogAddonInfo.xml) | "
    "Window.IsVisible(DialogPictureInfo.xml) | "
    "!String.IsEmpty(Window.Property(TMDbHelper.ContextMenu))")

ON_SCREENSAVER = "System.ScreenSaverActive"

ON_FULLSCREEN = "Window.IsVisible(fullscreenvideo)"


class Poller():
    def _on_idle(self, wait_time=30):
        self.update_monitor.waitForAbort(wait_time)

    def _on_modal(self):
        self._on_idle(POLL_MID_INCREMENT)

    def _on_context(self):
        self._on_idle(POLL_MID_INCREMENT)

    def _on_scroll(self):
        self._on_idle(POLL_MIN_INCREMENT)

    def _on_listitem(self):
        self._on_idle(POLL_MIN_INCREMENT)

    def _on_clear(self):
        self._on_idle(POLL_MIN_INCREMENT)

    def _on_exit(self):
        return

    def _on_player(self):
        return

    def _on_fullscreen(self):
        self._on_player()
        if get_condvisibility(ON_FULLSCREEN_LISTITEM):
            return self._on_listitem()
        self._on_idle(POLL_MID_INCREMENT)

    def poller(self):
        while not self.update_monitor.abortRequested() and not self.exit:
            if get_property('ServiceStop'):
                self.exit = True

            # If we're in fullscreen video then we should update the playermonitor time
            elif get_condvisibility(ON_FULLSCREEN):
                self._on_fullscreen()

            # Sit idle in a holding pattern if the skin doesn't need the service monitor yet
            elif get_condvisibility(ON_DISABLED):
                self._on_idle(30)

            # Sit idle in a holding pattern if screen saver is active
            elif get_condvisibility(ON_SCREENSAVER):
                self._on_idle(POLL_MAX_INCREMENT)

            # skip when modal or busy dialogs are opened (e.g. select / progress / busy etc.)
            elif get_condvisibility(ON_MODAL):
                self._on_modal()

            # manage context menu separately from other modals to pass info through
            elif get_condvisibility(ON_CONTEXT):
                self._on_context()

            # skip when container scrolling
            elif get_condvisibility(ON_SCROLL):
                self._on_scroll()

            # media window is opened or widgetcontainer set - start listitem monitoring!
            elif get_condvisibility(ON_LISTITEM):
                self._on_listitem()

            # Otherwise just sit here and wait
            else:
                self._on_clear()

        # Some clean-up once service exits
        self._on_exit()
