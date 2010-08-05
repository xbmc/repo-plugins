import os
import md5
import time
from misc import _get_path

try:
    import Foundation
    platform = 'osx'
except:
    if os.name == 'nt':
        platform = 'win'
    else:
        platform = 'unix'
        
if platform == 'win' or platform == 'osx':
    import cPickle as pickler
else:
    import pickle as pickler

class Caching:
    ''' Implements local caching of parsed RSS feeds '''
    def __init__(self, url, cache_time):
        path = _get_path('cache')
        file = md5.new(url).hexdigest()
        file += '.rss'
        
        self.cache_path = os.path.join(path, file)
        self.feed = url
        self.cache_time = cache_time
        
    def _save(self, feed_data):
        try:
            f = open(self.cache_path, 'wb')
            pickler.dump(feed_data, f)
            f.close()
        except:
            print 'Failed to save feed: %s cache: %s' % (self.feed, self.cache_path)
            
    def _fetch(self):
        ''' Return the cache if it exists, otherwise return nothing '''
        if self._check_cache_exists():
            return self._open()
        else:
            return ''
        
    def _open(self):
        ''' Open the parsed rss feed'''
        print 'opening cache: %s' % self.cache_path
        try:
            f = open(self.cache_path, 'rb')
            feed_data = pickler.load(f)
            f.close()
            return feed_data
        except:
            print 'Failed to open cache file'
            return ''
        
        
    def _check_cache_exists(self):
        if os.path.exists(self.cache_path):
            stats = os.stat(self.cache_path)
            ct = stats.st_ctime
            t = time.time()
            if t - ct < self.cache_time:
                print 'Using cached copy of feed'
                return True
            
        print 'Feed cache old or non existant, using fresh feed'
        return False