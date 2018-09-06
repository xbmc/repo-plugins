"""
    Original Source:
    https://github.com/jdf76/plugin.video.youtube/blob/master/resources/lib/youtube_plugin/kodion/utils/storage.py
    @ commit: 5c32bc002d4a30350f8f44d7ca3970da9066b7ef
    Modified: 2018-02-16

    Copyright (C) bromix, plugin.video.youtube

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import hashlib

from .storage import Storage


class SearchHistory(Storage):
    def __init__(self, filename, max_items=10):
        path = 'special://profile/addon_data/plugin.video.twitch/search/'
        Storage.__init__(self, path, filename, max_item_count=max_items)

    def is_empty(self):
        return self._is_empty()

    def list(self):
        result = []

        keys = self._get_ids(oldest_first=False)
        for key in keys:
            item = self._get(key)
            result.append(item[0])

        return result

    def clear(self):
        self._clear()

    def _make_id(self, search_text):
        m = hashlib.md5()
        try:
            m.update(search_text.encode('utf-8'))
        except UnicodeDecodeError:
            m.update(search_text)
        return m.hexdigest()

    def rename(self, old_search_text, new_search_text):
        self.remove(old_search_text)
        self.update(new_search_text)

    def remove(self, search_text):
        self._remove(self._make_id(search_text))

    def update(self, search_text):
        self._set(self._make_id(search_text), search_text)
