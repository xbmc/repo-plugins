import json
import os
import time

import xbmc

# Bump when the shape of a cached value changes, so old files are ignored
VERSION = 1


class Cache:
    """Small JSON cache in the add-on profile folder.

    Kodi starts a new Python process for every folder, so anything worth keeping
    between clicks (the 1.5 MB catalogue, programme ids) has to live on disk.
    """

    def __init__(self, profile_dir):
        self.dir = os.path.join(profile_dir, 'cache')

    def _path(self, key):
        return os.path.join(self.dir, key + '.v' + str(VERSION) + '.json')

    def get(self, key, max_age=None):
        """Return the cached value, or None when missing or older than max_age seconds."""
        try:
            with open(self._path(key), encoding='utf-8') as f:
                entry = json.load(f)
            if max_age is not None and time.time() - entry['time'] > max_age:
                return None
            return entry['value']
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def set(self, key, value):
        path = self._path(key)
        tmp = path + '.' + str(os.getpid()) + '.tmp'
        try:
            os.makedirs(self.dir, exist_ok=True)
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump({'time': time.time(), 'value': value}, f)
            os.replace(tmp, path)
        except (OSError, TypeError, ValueError) as e:
            xbmc.log("plugin.video.3cat - cache write failed for " + key + ": " + str(e), xbmc.LOGWARNING)
