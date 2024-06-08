import jurialmunkey.reqapi
from tmdbhelper.lib.addon.plugin import get_setting
from tmdbhelper.lib.addon.logger import kodi_log
from tmdbhelper.lib.files.bcache import BasicCache


class RequestAPI(jurialmunkey.reqapi.RequestAPI):
    error_notification = get_setting('connection_notifications')
    _basiccache = BasicCache

    @staticmethod
    def kodi_log(msg, level=0):
        kodi_log(msg, level)
