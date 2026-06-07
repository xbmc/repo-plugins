import xbmc
import xbmcaddon

class KodiLogger:
    def __init__(self):
        addon = xbmcaddon.Addon()
        self.addon_id = addon.getAddonInfo("id")

    def _log(self, level, msg):
        xbmc.log(f"[{self.addon_id}] {msg}", level)

    def debug(self, msg):
        self._log(xbmc.LOGDEBUG, msg)

    def info(self, msg):
        self._log(xbmc.LOGINFO, msg)

    def warning(self, msg):
        self._log(xbmc.LOGWARNING, msg)

    def error(self, msg):
        self._log(xbmc.LOGERROR, msg)

    def fatal(self, msg):
        self._log(xbmc.LOGFATAL, msg)


# Create a module-level logger instance
log = KodiLogger()
