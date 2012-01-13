import os
try:
    import json
except ImportError:
    import simplejson as json
import time
from datetime import timedelta, datetime
from xbmcswift import xbmc


TTL = timedelta(days=1)  # one day


def put_cached_data(contents, filename, timestamp_fn):
    '''Writes contents to filename and writes time.time() to timestamp_fn'''
    file = open(filename, 'w')
    file.write(contents)
    file = open(timestamp_fn, 'w')
    file.write('%d' % time.time())


def get_cached_data(json_fn, timestamp_fn):
    '''Returns a JSON object from json_fn if json_fn exists and if the
    timestamp in timestamp_fn is not older than TTL. Returns None if cache
    isn't valid for any reason.
    '''
    if not os.path.exists(json_fn):
        xbmc.log('Missing Khan Academy cache file at %s' % json_fn)
        return None

    if not os.path.exists(timestamp_fn):
        xbmc.log('Missing Khan Academy cache timestamp file at %s' %
                 timestamp_fn)
        return None

    now = datetime.utcnow()
    file = open(timestamp_fn)
    timestamp = datetime.utcfromtimestamp(float(file.read()))

    if now - timestamp > TTL:
        xbmc.log('Khan Academy cache file is older than TTL.')
        return None

    file = open(json_fn)
    xbmc.log('Returning Khan Data from cache.')
    return json.load(file)
