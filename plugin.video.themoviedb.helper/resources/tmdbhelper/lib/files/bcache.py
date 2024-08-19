from tmdbhelper.lib.addon.logger import kodi_traceback
from tmdbhelper.lib.files.scache import SimpleCache, SimpleCacheMem
import jurialmunkey.bcache

BasicCache = jurialmunkey.bcache.BasicCache
use_simple_cache = jurialmunkey.bcache.use_simple_cache


class BasicCache(jurialmunkey.bcache.BasicCache):
    _simplecache = SimpleCache

    @staticmethod
    def kodi_traceback(exc, log_msg):
        kodi_traceback(exc, log_msg)


class BasicCacheMem(BasicCache):
    _simplecache = SimpleCacheMem
