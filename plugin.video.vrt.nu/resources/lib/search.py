# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
''' Implementation of Search class '''

from __future__ import absolute_import, division, unicode_literals
import json
from favorites import Favorites
from helperobjects import TitleItem


class Search:
    ''' Search and cache search queries '''

    def __init__(self, _kodi):
        ''' Initialize searchtes, relies on XBMC vfs '''
        self._kodi = _kodi
        self._favorites = Favorites(_kodi)

        self._search_history = _kodi.get_userdata_path() + 'search_history.json'

    def search_menu(self):
        ''' Main search menu '''
        menu_items = [
            TitleItem(
                title=self._kodi.localize(30424),  # New search...
                path=self._kodi.url_for('search_query'),
                art_dict=dict(thumb='DefaultAddonsSearch.png'),
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
                art_dict=dict(thumb='DefaultAddonsSearch.png'),
                is_playable=False,
                context_menu=[(self._kodi.localize(30030), 'RunPlugin(%s)' % self._kodi.url_for('remove_search', keywords=keywords))]
            ))

        if history:
            menu_items.append(TitleItem(
                title=self._kodi.localize(30426),  # Clear search history
                path=self._kodi.url_for('clear_search'),
                info_dict=dict(plot=self._kodi.localize(30427)),
                art_dict=dict(thumb='icons/infodialogs/uninstall.png'),
                is_playable=False,
            ))

        self._kodi.show_listing(menu_items, category=30031)

    def search(self, keywords=None, page=None):
        ''' The VRT NU add-on Search functionality and results '''
        if keywords is None:
            keywords = self._kodi.get_search_string()

        if not keywords:
            self._kodi.end_of_directory()
            return

        from statichelper import realpage
        page = realpage(page)

        self.add(keywords)

        from apihelper import ApiHelper
        search_items, sort, ascending, content = ApiHelper(self._kodi, self._favorites).list_search(keywords, page=page)
        if not search_items:
            self._kodi.show_ok_dialog(heading=self._kodi.localize(30098), message=self._kodi.localize(30099, keywords=keywords))
            self._kodi.end_of_directory()
            return

        # Add 'More...' entry at the end
        if len(search_items) == 50:
            search_items.append(TitleItem(
                title=self._kodi.localize(30300),
                path=self._kodi.url_for('search_query', keywords=keywords, page=page + 1),
                art_dict=dict(thumb='DefaultAddonSearch.png'),
                info_dict=dict(),
            ))

        self._favorites.get_favorites(ttl=60 * 60)
        self._kodi.show_listing(search_items, category=30032, sort=sort, ascending=ascending, content=content, cache=False)

    def clear(self):
        ''' Clear the search history '''
        with self._kodi.open_file(self._search_history, 'w') as f:
            json.dump([], f)
        self._kodi.end_of_directory()

    def add(self, keywords):
        ''' Add new keywords to search history '''
        try:
            with self._kodi.open_file(self._search_history, 'r') as f:
                history = json.load(f)
        except Exception:
            history = []

        # Remove if keywords already was listed
        try:
            history.remove(keywords)
        except ValueError:
            pass

        history.insert(0, keywords)

        with self._kodi.open_file(self._search_history, 'w') as f:
            json.dump(history, f)

    def remove(self, keywords):
        ''' Remove existing keywords from search history '''
        try:
            with self._kodi.open_file(self._search_history, 'r') as f:
                history = json.load(f)
        except Exception:
            history = []

        try:
            history.remove(keywords)
        except ValueError:
            return

        self._kodi.container_refresh()

        # If keywords was successfully removed, write to disk
        with self._kodi.open_file(self._search_history, 'w') as f:
            json.dump(history, f)
