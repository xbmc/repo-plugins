'''
    qobuz.cache.file
    ~~~~~~~~~~~~~~~~

    Class that implement caching to disk

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
try:
    """cPickle is a faster implementation of pickle, we are using it if
    present
    """
    import cPickle as pickle
except ImportError:
    import pickle
import os

from base import CacheBase
from util.file import RenamedTemporaryFile, unlink
from util.hash import hashit


class CacheFile(CacheBase):

    def __init__(self):
        self.base_path = None
        self.ventile = False
        super(CacheFile, self).__init__()

    def load(self, key, *a, **ka):
        filename = self._make_path(key)
        return self.load_from_store(filename)

    def make_key(self, *a, **ka):
        argstr = '/'.join(a[:])
        argstr += '/'.join(['%s=%s' % (key, ka[key]) for key in sorted(ka)])
        return hashit(argstr)

    def _make_path(self, key):
        xpath = []
        xpath.append(self.base_path)
        fileName = key + '.dat'
        return os.path.join(os.path.join(*xpath), fileName)

    def sync(self, key, data):
        filename = self._make_path(key)
        unlink(filename)
        try:
            with RenamedTemporaryFile(filename) as fo:
                pickle.dump(data, fo, protocol=pickle.HIGHEST_PROTOCOL)
                fo.flush()
                os.fsync(fo)
        except Exception as e:
            print "Error: writing failed %s\nMessage %s" % (filename, e)
            return False
        return True

    def load_from_store(self, filename):
        path = os.path.join(self.base_path, filename)
        if not os.path.exists(path):
            return None
        with open(filename, 'rb') as f:
            return pickle.load(f)
        return None

    def get_ttl(self, *a, **ka):
        return 3600

    def delete(self, key, *a, **ka):
        filename = self._make_path(key)
        if not os.path.exists(filename):
            print "Cache file doesn't exist %s" % (filename)
            return False
        return unlink(filename)
