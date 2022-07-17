import xbmc


class Logger:
    """Wrapper of the XBMC Logger"""
    def __init__(self, plugin):
        self.plugin = plugin

    def _log(self, message, level):
        fmt_message = f"[{self.plugin.ADDON_ID}]: {str(message)}"
        xbmc.log(fmt_message, level=level)

    def debug(self, message):
        self._log(message, xbmc.LOGDEBUG)

    def info(self, message):
        self._log(message, xbmc.LOGINFO)

    def warning(self, message):
        self._log(message, xbmc.LOGWARNING)

    def error(self, message):
        self._log(message, xbmc.LOGERROR)

    def fatal(self, message):
        self._log(message, xbmc.LOGFATAL)
