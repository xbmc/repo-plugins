'''
    qobuz.cache.qobuz
    ~~~~~~~~~~~~~~~~~

    We are setting ttl here based on key type
    We are caching key who return data in dictionary so further request of
    the same key return data from memory.

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
from file import CacheFile
from gui.util import getSetting


class CacheQobuz(CacheFile):

    def __init__(self, *a, **ka):
        self.store = {}
        self.black_keys = ['password']
        super(CacheQobuz, self).__init__()

    def load(self, key, *a, **ka):
        if key in self.store:
            return self.store[key]
        data = super(CacheQobuz, self).load(key, *a, **ka)
        if not data:
            return None
        self.store[key] = data
        return data

    def get_ttl(self, key, *a, **ka):
        if len(a) > 0:
            if a[0] == '/track/getFileUrl':
                return 60 * 15
        if 'user_id' in ka:
            return getSetting('cache_duration_middle', isInt=True) * 60
        return getSetting('cache_duration_long', isInt=True) * 60
