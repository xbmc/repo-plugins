# -*- coding: utf-8 -*-
"""Cache manager for Funhaus Archive add-on."""

import json
import os
import time

try:
    import xbmcvfs
    import xbmcaddon
    ADDON = xbmcaddon.Addon()
    PROFILE_DIR = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
except (ImportError, AttributeError):
    PROFILE_DIR = os.path.join(os.path.expanduser('~'), '.funhaus_archive_cache')


class SimpleCache:
    """Simple disk cache for scraped HTML/JSON payloads."""

    def __init__(self, cache_dir=None, default_ttl_hours=24):
        self.cache_dir = cache_dir or os.path.join(PROFILE_DIR, 'cache')
        self.default_ttl = default_ttl_hours * 3600
        self._ensure_dir()

    def _ensure_dir(self):
        if not os.path.exists(self.cache_dir):
            try:
                os.makedirs(self.cache_dir, exist_ok=True)
            except OSError:
                pass

    def _get_key_path(self, key):
        safe_key = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in key)
        return os.path.join(self.cache_dir, f"{safe_key}.json")

    def get(self, key, ttl_hours=None):
        path = self._get_key_path(key)
        if not os.path.exists(path):
            return None

        ttl = (ttl_hours * 3600) if ttl_hours is not None else self.default_ttl
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            cached_at = data.get('timestamp', 0)
            if (time.time() - cached_at) > ttl:
                return None

            return data.get('payload')
        except Exception:
            return None

    def set(self, key, payload):
        self._ensure_dir()
        path = self._get_key_path(key)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({'timestamp': time.time(), 'payload': payload}, f)
            return True
        except Exception:
            return False

    def clear(self):
        if os.path.exists(self.cache_dir):
            for fname in os.listdir(self.cache_dir):
                if fname.endswith('.json'):
                    try:
                        os.remove(os.path.join(self.cache_dir, fname))
                    except OSError:
                        pass
