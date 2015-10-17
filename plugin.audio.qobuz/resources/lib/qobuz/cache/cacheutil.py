'''
    qobuz.cache.cacheutil
    ~~~~~~~~~~~~~~~~~~~~~

    Little utility class for cleaning cache purpose

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
from util.file import find


def clean_old(cache):
    """Callback deleting one file
    """
    def delete_one(filename, info):
        data = cache.load_from_store(filename)
        if not cache.check_magic(data):
            raise TypeError('magic mismatch')
        ttl = cache.is_fresh(data['key'], data)
        if ttl:
            return True
        cache.delete(data['key'])
        return True
    find(cache.base_path, '^.*\.dat$', delete_one)
    return True


def clean_all(cache):
    """Clean all data from cache
    """
    def delete_one(filename, info):
        '''::callback that delete one file
        '''
        data = cache.load_from_store(filename)
        if not cache.check_magic(data):
            print "Error: bad magic, skipping file %s" % (filename)
            return True
        cache.delete(data['key'])
        return True
    find(cache.base_path, '^.*\.dat$', delete_one)
    return True
