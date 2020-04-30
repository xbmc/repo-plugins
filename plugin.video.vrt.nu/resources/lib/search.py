# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Implementation of Search class"""

from __future__ import absolute_import, division, unicode_literals
from favorites import Favorites
from kodiutils import (colour, addon_profile, container_refresh, container_update, end_of_directory, get_json_data,
                       get_search_string, get_setting_int, input_down, localize, ok_dialog, open_file,
                       show_listing, ttl, url_for)
from resumepoints import ResumePoints


class Search:
    """Search and cache search queries"""

    def __init__(self):
        """Initialize searchtes, relies on XBMC vfs"""
        self._favorites = Favorites()
        self._resumepoints = ResumePoints()
        self._search_history = addon_profile() + 'search_history.json'

    def read_history(self):
        """Read search history from disk"""
        with open_file(self._search_history, 'r') as fdesc:
            return get_json_data(fdesc, fail=[])

    def write_history(self, history):
        """Write search history to disk"""
        from json import dump
        with open_file(self._search_history, 'w') as fdesc:
            dump(history, fdesc)

    def search_menu(self):
        """Main search menu"""
        from helperobjects import TitleItem
        menu_items = [
            TitleItem(
                label=localize(30424),  # New search...
                path=url_for('search_query'),
                art_dict=dict(thumb='DefaultAddonsSearch.png'),
                info_dict=dict(plot=localize(30425)),
                is_playable=False,
            )
        ]

        history = self.read_history()
        for keywords in history:
            menu_items.append(TitleItem(
                label=keywords,
                path=url_for('search_query', keywords=keywords),
                is_playable=False,
                context_menu=[(
                    localize(30033),  # Edit
                    'RunPlugin(%s)' % url_for('edit_search', keywords=keywords),
                ), (
                    localize(30030),  # Remove
                    'RunPlugin(%s)' % url_for('remove_search', keywords=keywords),
                )],
            ))

        if history:
            menu_items.append(TitleItem(
                label=localize(30426),  # Clear search history
                path=url_for('clear_search'),
                info_dict=dict(plot=localize(30427)),
                art_dict=dict(thumb='icons/infodialogs/uninstall.png'),
                is_playable=False,
            ))

        show_listing(menu_items, category=30031, cache=False)

    def search(self, keywords=None, page=0, edit=False):
        """The VRT NU add-on Search functionality and results"""
        if keywords is None or edit is True:
            keywords = get_search_string(keywords)

        if not keywords:
            end_of_directory()
            return
        if edit is True:
            container_update(url_for('search_query', keywords=keywords))
            return

        from apihelper import ApiHelper
        from utils import realpage
        page = realpage(page)

        self.add(keywords)

        search_items, sort, ascending, content = ApiHelper(self._favorites, self._resumepoints).list_search(keywords, page=page)
        if not search_items:
            ok_dialog(heading=localize(30135), message=localize(30136, keywords=keywords))
            end_of_directory()
            return

        # Add 'More…' entry at the end
        from helperobjects import TitleItem
        if len(search_items) == get_setting_int('itemsperpage', default=50):
            search_items.append(TitleItem(
                label=colour(localize(30300)),  # More…
                path=url_for('search_query', keywords=keywords, page=page + 1),
                art_dict=dict(thumb='DefaultAddonSearch.png'),
                info_dict=dict(),
            ))

        self._favorites.refresh(ttl=ttl('indirect'))
        show_listing(search_items, category=30032, sort=sort, ascending=ascending, content=content, cache=False)

    def clear(self):
        """Clear the search history"""
        self.write_history([])
        end_of_directory()

    def add(self, keywords):
        """Add new keywords to search history"""
        history = self.read_history()

        # Remove if keywords already was listed
        try:
            history.remove(keywords)
        except ValueError:
            pass

        history.insert(0, keywords)

        self.write_history(history)

    def remove(self, keywords):
        """Remove existing keywords from search history"""
        history = self.read_history()

        try:
            history.remove(keywords)
        except ValueError:
            return

        # If keywords was successfully removed, write to disk
        self.write_history(history)

        input_down()
        container_refresh()
