import time
import os
import simplejson as json

CACHE_VERSION = 1


class Cache(object):

    def __init__(self, cache_path, cache_filename='cache.json'):
        self.cache_path = cache_path
        self.cache_filename = cache_filename
        self.__read_cache()

    def __read_cache(self):
        log('Cache.__read_cache started')
        cache_file = os.path.join(self.cache_path, self.cache_filename)
        if os.path.isfile(cache_file):
            try:
                c = json.load(open(cache_file, 'r'))
                if 'version' in c and c['version'] == CACHE_VERSION:
                    self.__cache = c
                else:
                    log('Cache.__read_cache cache in wrong version')
                    self.__recreate_cache()
            except ValueError:
                log('Cache.__read_cache could not read: "%s"' % cache_file)
                self.__recreate_cache()
        else:
            log('Cache.__read_cache file does not exist: "%s"' % cache_file)
            self.__recreate_cache()
        log('Cache.__read_cache finished')

    def __recreate_cache(self):
        log('Cache.__recreate_cache version: %d' % CACHE_VERSION)
        self.__cache = {'version': CACHE_VERSION,
                        'content': {}}

    def __write_cache(self):
        log('Cache.__write_cache started')
        if not os.path.isdir(self.cache_path):
            os.makedirs(self.cache_path)
        cache_file = os.path.join(self.cache_path, 'cache.json')
        json.dump(self.__cache, open(cache_file, 'w'), indent=1)
        log('Cache.__write_cache finished')

    def get(self, element_id, max_age):
        log('Cache.get started with element_id: %s' % element_id)
        if element_id in self.__cache['content']:
            log('Cache.get found element')
            element = self.__cache['content'][element_id]
            if max_age and time.time() - element['timestamp'] > max_age:
                log('Cache.get element too old')
            else:
                log('Cache.get successful')
                return element['data']

    def set(self, element_id, element_data):
        log('Cache.set started with element_id: %s' % element_id)
        self.__cache['content'][element_id] = {'timestamp': time.time(),
                                               'data': element_data}
        self.__write_cache()


def log(msg):
    print 'HWCLIPS.com: %s' % msg
