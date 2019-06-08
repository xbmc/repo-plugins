import os
import time
import unittest
import urllib2

def get_HTML(url):
    return urllib2.urlopen(url).read()

EXCLUDE_RATE_LIMITED = os.environ.get('EXCLUDE_RATE_LIMITED') != 'false'
RATE_LIMIT_WAIT_SECONDS = 10

skip_ted_rate_limited = unittest.skipIf(EXCLUDE_RATE_LIMITED, 'Minimal TED website requests.')

__cache__ = {}
__previous_request__ = 0

class CachedHTMLProvider:

    def get_HTML(self, url):
        '''
        Avoid the wrath of TED by caching requests as much as possible.
        '''
        if url not in __cache__:
            # Aggressive TED rate limiting :'(
            now = time.time()
            global __previous_request__
            elapsed = now - __previous_request__
            if elapsed < RATE_LIMIT_WAIT_SECONDS:
                time.sleep(max(0, RATE_LIMIT_WAIT_SECONDS - elapsed))
            __previous_request__ = now
            __cache__[url] = get_HTML(url)
        return __cache__[url]
