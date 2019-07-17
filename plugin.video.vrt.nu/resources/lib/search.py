# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' Implementation of Search class '''

from __future__ import absolute_import, division, unicode_literals
import json
from resources.lib import favorites, vrtapihelper
from resources.lib.helperobjects import TitleItem
from resources.lib.statichelper import realpage


class Search:
    ''' Search and cache search queries '''

    def __init__(self, _kodi):
        ''' Initialize searchtes, relies on XBMC vfs '''
        self._kodi = _kodi
        self._favorites = favorites.Favorites(_kodi)
        self._apihelper = vrtapihelper.VRTApiHelper(_kodi, self._favorites)

        self._search_history = _kodi.get_userdata_path() + 'search_history.json'

    def search_menu(self):
        ''' Main search menu '''
        menu_items = [
            TitleItem(
                title=self._kodi.localize(30424),  # New search...
                path=self._kodi.url_for('search_query'),
                art_dict=dict(thumb='DefaultAddonsSearch.png', fanart='DefaultAddonsSearch.png'),
                info_dict=dict(plot=self._kodi.localize(30425)),
                is_playable=False,
            )
        ]

        try:
            with self._kodi.open_file(self._search_history, 'r') as f:
                history = json.load(f)
        except Exception:
            history = []

        for keywords in history:
            menu_items.append(TitleItem(
                title=keywords,
                path=self._kodi.url_for('search_query', keywords=keywords),
                art_dict=dict(thumb='DefaultAddonsSearch.png', fanart='DefaultAddonsSearch.png'),
                is_playable=False,
            ))

        if history:
            menu_items.append(TitleItem(
                title=self._kodi.localize(30426),  # Clear search history
                path=self._kodi.url_for('clear_search'),
                info_dict=dict(plot=self._kodi.localize(30427)),
                art_dict=dict(thumb='icons/infodialogs/uninstall.png', fanart='icons/infodialogs/uninstall.png'),
                is_playable=False,
            ))

        self._kodi.show_listing(menu_items)

    def search(self, keywords=None, page=None):
        ''' The VRT NU add-on Search functionality and results '''
        if keywords is None:
            keywords = self._kodi.get_search_string()

        if not keywords:
            self._kodi.end_of_directory()
            return

        page = realpage(page)

        self.add(keywords)
        search_items, sort, ascending, content = self._apihelper.get_search_items(keywords, page=page)
        if not search_items:
            self._kodi.show_ok_dialog(heading=self._kodi.localize(30098), message=self._kodi.localize(30099).format(keywords=keywords))
            self._kodi.end_of_directory()
            return

        # Add 'More...' entry at the end
        if len(search_items) == 50:
            search_items.append(TitleItem(
                title=self._kodi.localize(30300),
                path=self._kodi.url_for('search', keywords=keywords, page=page + 1),
                art_dict=dict(thumb='DefaultAddonSearch.png', fanart='DefaultAddonSearch.png'),
                info_dict=dict(),
            ))

        self._favorites.get_favorites(ttl=60 * 60)
        self._kodi.show_listing(search_items, sort=sort, ascending=ascending, content=content, cache=False)

    def clear(self):
        ''' Clear the search history '''
        with self._kodi.open_file(self._search_history, 'w') as f:
            json.dump([], f)
        self._kodi.end_of_directory()

    def add(self, keywords):
        ''' Add new keywords to search history '''
        from collections import OrderedDict
        try:
            with self._kodi.open_file(self._search_history, 'r') as f:
                history = json.load(f)
        except Exception:
            history = []

        history.insert(0, keywords)

        # Remove duplicates while preserving order
        history = list(OrderedDict((element, None) for element in history))

        with self._kodi.open_file(self._search_history, 'w') as f:
            json.dump(history, f)
