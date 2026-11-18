# ------------------------------------------------------------------------------
#  Copyright (c) 2026 Dimitri Kroon.
#  This file is part of plugin.audio.bbcsounds.
#  SPDX-License-Identifier: GPL-3.0-or-later
#  See LICENSE.txt or https://www.gnu.org/licenses/gpl-3.0.txt
# ------------------------------------------------------------------------------

from __future__ import annotations
import os
import json
import time

from datetime import datetime
from typing import TYPE_CHECKING

import xbmc
import xbmcgui
import xbmcplugin

from resources.lib.log import log
from resources.lib.route import content, script, build_callback

if TYPE_CHECKING:
    from resources.lib.plugin import Plugin


TXT_ID_REMOVE_TERM = 30606
TXT_ID_EDIT_TERM = 30607
TXT_ID_CLEAR_HISTORY = 30608


class SearchHistory:
    """
    A class providing an easy interface to saved search terms.

    :param profile_dir: The directory with the addon's user data.
    """

    def __init__(self, profile_dir: str):
        self.full_path = os.path.join(profile_dir, 'search_terms.json')
        self._keywords = self._read_file()

    def _read_file(self):
        try:
            with open(self.full_path, 'r', encoding='utf8') as f:
                data = json.load(f)
                return data
        except (OSError, KeyError, TypeError, json.JSONDecodeError) as err:
            log("Error: Failed to read search history file: %r.", err)
            return {}

    def _save_file(self):
        new_data = json.dumps(self._keywords)
        with open(self.full_path, 'w', encoding='utf8') as f:
            f.write(new_data)

    def append(self, keyword: str):
        """Add `keyword` to the saved search terms.

        :param keyword: The search term to save.

        """
        log("Search: Adding new search term '%r' to the list", keyword)
        if not keyword:
            return

        if keyword in self._keywords.keys():
            self.update_last_used(keyword)
            return

        now = time.time()
        self._keywords[keyword] = {'created': now, 'last_used': now}
        self._save_file()

    def update_last_used(self, keyword):
        try:
            self._keywords[keyword]['last_used'] = time.time()
        except KeyError:
            raise ValueError(f"Keyword '{keyword}' is not in present in the search history.") from None
        self._save_file()

    def remove(self, keyword: str):
        """Remove `keyword` from the saved search terms for the specified media type.
        Fails silently when `term` does not exist in the search history.

        :param keyword: The search term to remove.

        """
        log("Search: Removing search term '%s'", keyword)
        if keyword not in self._keywords.keys():
            return
        del self._keywords[keyword]
        self._save_file()

    def clear(self):
        """Remove al search terms."""
        log("Search: Clear search history.")
        self._keywords.clear()
        self._save_file()

    def replace(self, existing: str, new: str):
        """Replace an existing keyword with a new one.

        :param existing: The existing keyword to replace.
        :param new: The new keyword that will replace the existing.
        :raises: ValueError if `existing` is not present in the search history
        """
        log("Search: replacing search term '%s' for '%s'.", existing, new)
        # log("keywords = %s", self._keywords)
        try:
            date_info = self._keywords.pop(existing)
        except KeyError:
            raise ValueError(f"Keyword '{existing}' is not in present in the search history.") from None
        self._keywords[new] = date_info
        self._save_file()

    def __bool__(self):
        return bool(self._keywords)

    def __iter__(self):
        try:
            return iter(sorted(self._keywords.items(), key=lambda a: a[1]['last_used'], reverse=True))
        except AttributeError:
            log("Search history file has an invalid format. Items will be cleared.")
            self._keywords = {}
            self._save_file()
            raise RuntimeError("Invalid search history file.")


def open_keyboard():
    keyboard = xbmc.Keyboard('', xbmc.getLocalizedString(16017))
    keyboard.doModal()
    if keyboard.isConfirmed():
        return keyboard.getText()
    else:
        return ''


# noinspection unused-parameter
@content
def list_search_terms(plugin: Plugin, slug=''):
    """Create a listing of saved search terms, starting with an item that enables
    users to enter a new search term using the on-screen keyboard.

    """
    search_history = SearchHistory(plugin.user_dir)
    txt_remove = plugin.translate(TXT_ID_REMOVE_TERM)
    txt_edit = plugin.translate(TXT_ID_EDIT_TERM)
    txt_clear = plugin.translate(TXT_ID_CLEAR_HISTORY)

    li = xbmcgui.ListItem('New Search', offscreen=True)
    li.setArt({'thumb': 'DefaultAddonsSearch.png'})
    li.setProperties({'IsPlayable': 'false',
                      'SpecialSort': 'top'})
    yield build_callback('search/new_search'), li, False

    cmd_clear_history = f'RunPlugin(plugin://{plugin.addon_id}/search/context_menu?action=clear)'

    for keyword, date_info in search_history:
        cmd_remove = f"RunPlugin({build_callback('search/context_menu', action='remove', keyword=keyword)})"
        cmd_edit = f"RunPlugin({build_callback('search/context_menu', action='edit', keyword=keyword)})"
        ctx_mnu = [(txt_remove, cmd_remove),
                   (txt_edit, cmd_edit),
                   (txt_clear, cmd_clear_history)
                   ]
        li = xbmcgui.ListItem(keyword, offscreen=True)
        li.addContextMenuItems(ctx_mnu)
        info = li.getVideoInfoTag()
        info.setDateAdded(datetime.fromtimestamp(date_info['created']).strftime('%Y-%m-%d %H:%M:%S'))
        yield build_callback('search/do_search', keyword=keyword, slug='search / ' + keyword), li, True

    plugin.set_sort_methods({xbmcplugin.SORT_METHOD_DATEADDED})


@script
def new_search(plugin: Plugin):
    keyword = open_keyboard()
    if keyword:
        history = SearchHistory(plugin.user_dir)
        history.append(keyword)
        url = build_callback('search/do_search', keyword=keyword)
        xbmc.executebuiltin(f'Container.Update({url})')


@content
def do_search(plugin: Plugin, keyword, slug=''):
    from resources.lib.parse import Parser
    from resources.lib import fetch

    history = SearchHistory(plugin.user_dir)
    history.update_last_used(keyword)

    parser = Parser(plugin, slug=slug)
    resp = fetch.get(parser.api_domain + 'experience/inline/search',
                     params={'q': keyword})
    resp_data = json.loads(resp.content)

    first_item = resp_data['data'][0]
    if first_item['id'] == 'search_empty':
        xbmcgui.Dialog().ok(plugin.addon.getAddonInfo('name'),
                            first_item['description'])
        return

    # Search usually returns 2 rails; one with 'shows' and another with 'episodes'.
    # To prevent having to call the same search over again, list the contents of
    # all rails in one go.
    for rail in resp_data['data']:
        if rail['type'] == 'inline_display_module':
            yield from parser.parse_items_list(rail['data'])


@script
def context_menu(plugin: Plugin, action: str, keyword: str = ''):
    """Handle all search-related context menu items."""
    history = SearchHistory(plugin.user_dir)

    if action == 'remove':
        history.remove(keyword)
    elif action == 'clear':
        history.clear()
    elif action == 'edit':
        heading = ' - '.join((plugin.translate(TXT_ID_EDIT_TERM), keyword))
        keyboard = xbmc.Keyboard(keyword, heading)
        keyboard.doModal()
        if not keyboard.isConfirmed():
            return
        new_term = keyboard.getText()
        if new_term == '':
            history.remove(keyword)
        else:
            history.replace(keyword, new_term)
    else:
        raise ValueError("Search: invalid context menu action '%s'.", action)
    xbmc.executebuiltin('Container.Refresh')
