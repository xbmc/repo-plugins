import urllib

import random
import time

from threading import Thread

from de.generia.kodi.plugin.backend.zdf.Teaser import Teaser
from de.generia.kodi.plugin.backend.zdf.TeaserLazyloadResource import TeaserLazyloadResource       


class LazyloadTeaserThread(Thread):
    log = None
    lazyloadTeaser = None
    teaser = None
    
    def __init__(self, lazyloadTeaser, log):
        super(LazyloadTeaserThread, self).__init__()
        self.log = log
        self.lazyloadTeaser = lazyloadTeaser
        
    def run(self):
        resource = TeaserLazyloadResource(self.lazyloadTeaser)
        resource.log = self.log
        resource.parse()
        self.teaser = resource.teaser


class TeaserLazyloadResolver(object):
    log = None
    
    def __init__(self, log=None):
        self.log = log

    def resolveTeasers(self, lazyloadTeasers):
        threads = []
        i = 0
        # using 'multiprocessing.pool' would have been nice, but this does not work inside kodi
        for lazyloadTeaser in lazyloadTeasers:
            thread = LazyloadTeaserThread(lazyloadTeaser, self.log)
            threads.append(thread)
            thread.start()
            i = i + 1
        
        for thread in threads:
            thread.join()

        teasers = []            
        for thread in threads:
            teaser = thread.teaser
            if teaser is not None:
                teasers.append(teaser)
        
        return teasers
