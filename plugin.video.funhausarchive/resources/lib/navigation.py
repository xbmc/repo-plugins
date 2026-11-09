# -*- coding: utf-8 -*-
"""Navigation state manager for Funhaus Archive Kodi add-on.

Persists pagination position and last visited sections across Kodi restarts.
"""

import json
import os
import time

try:
    import xbmcvfs
    import xbmcaddon
    ADDON = xbmcaddon.Addon("plugin.video.funhausarchive")
    PROFILE_DIR = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
except (ImportError, AttributeError, Exception):
    PROFILE_DIR = os.path.join(os.path.expanduser('~'), '.funhaus_archive_cache')


class NavigationManager:
    """Manages persistent navigation state across Kodi restarts."""

    def __init__(self, profile_dir=None):
        self.profile_dir = profile_dir or PROFILE_DIR
        self.state_file = os.path.join(self.profile_dir, 'navigation_state.json')
        self._ensure_dir()

    def _ensure_dir(self):
        if not os.path.exists(self.profile_dir):
            try:
                os.makedirs(self.profile_dir, exist_ok=True)
            except OSError:
                pass

    def _load(self) -> dict:
        if not os.path.exists(self.state_file):
            return {}
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self, data: dict) -> bool:
        self._ensure_dir()
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception:
            return False

    def save_position(self, action: str, query: dict, page: int, total_pages: int, title: str):
        """Saves current viewing position.

        Args:
            action: Plugin action string (e.g. 'list_all_videos', 'list_filtered')
            query: Query dictionary for the view
            page: Current 1-based page number
            total_pages: Total number of pages
            title: Human-readable view title
        """
        data = self._load()
        clean_query = {k: str(v) for k, v in query.items() if k != 'page'}
        clean_query['page'] = str(page)

        entry = {
            'action': action,
            'query': clean_query,
            'page': int(page),
            'total_pages': int(total_pages),
            'title': title,
            'updated_at': time.time()
        }

        # Track last overall position
        data['last_overall'] = entry

        # Track oldest chronological sort specifically
        if action == 'list_all_videos' and query.get('sort') == 'oldest':
            data['last_oldest'] = entry

        # Specific key for direct section lookups
        key = f"{action}_{query.get('sort', '')}_{query.get('slug', '')}_{query.get('year', '')}_{query.get('cast', '')}_{query.get('content_type', '')}"
        data[key] = entry

        self._save(data)

    def get_last_oldest(self) -> dict:
        """Returns last saved state for 'All Videos - Oldest First' if page > 1."""
        data = self._load()
        entry = data.get('last_oldest')
        if entry and int(entry.get('page', 1)) > 1:
            return entry
        return None

    def get_last_overall(self) -> dict:
        """Returns last overall browsing state if page > 1."""
        data = self._load()
        entry = data.get('last_overall')
        if entry and int(entry.get('page', 1)) > 1:
            return entry
        return None

    def get_saved_page(self, action: str, sort: str = '', slug: str = '', year: str = '', cast: str = '', content_type: str = '') -> dict:
        """Retrieves saved position for a specific section."""
        data = self._load()
        key = f"{action}_{sort}_{slug}_{year}_{cast}_{content_type}"
        return data.get(key)

    def clear_resume(self, sort_key: str = 'oldest') -> bool:
        """Clears resume state for a given key or all."""
        data = self._load()
        if sort_key == 'oldest':
            data.pop('last_oldest', None)
        elif sort_key == 'all':
            data.clear()
        else:
            data.pop(f"list_all_videos_{sort_key}_____", None)
        return self._save(data)
