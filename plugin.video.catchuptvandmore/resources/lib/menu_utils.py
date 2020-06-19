# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2016  SylvainCecchetto

    This file is part of Catch-up TV & More.

    Catch-up TV & More is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Catch-up TV & More is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with Catch-up TV & More; if not, write to the Free Software Foundation,
    Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

# Core imports
import os
import json
import importlib

# Kodi imports
from codequick import Script, utils
from kodi_six import xbmc
from kodi_six import xbmcvfs
from kodi_six import xbmcgui

# Local imports
from resources.lib.kodi_utils import get_kodi_version
import resources.lib.favourites as fav

from resources.lib.addon_utils import get_item_label
from resources.lib.migration_utils import migrate_old_menus_settings


MENUS_SETTINGS_FP = os.path.join(Script.get_info('profile'), "menus_settings.json")
"""
Json file that keeps, for each menu of the addon,
what elements are hidden and the order of items in each menu

"""


"""Utility functions to deal with user menus settings

"""


def get_menus_settings():
    """Get menus settings dict from json file

    Returns:
        dict: Menus settings
    """
    try:
        migrate_old_menus_settings(MENUS_SETTINGS_FP)  # Migrate old Kodi settings (from settings.xml)
    except Exception:
        Script.log('Failed to migrate old settings to json file')
    if not xbmcvfs.exists(MENUS_SETTINGS_FP):
        return {}
    with open(MENUS_SETTINGS_FP) as f:
        return json.load(f)


def save_menus_settings(j):
    """Save menus settings dict in json file

    Args:
        j (dict): menus_settings dict to save
    """
    with open(MENUS_SETTINGS_FP, 'w') as f:
        json.dump(j, f, indent=4)


def is_item_hidden(item_id, menu_id):
    """Check if item 'item_id' of menu 'menu_id' is hidden by the user setting

    Args:
        item_id (str): (e.g. live_tv)
        menu_id (str): (e.g. root)
    Returns:
        bool
    """
    menus_settings = get_menus_settings()
    return menus_settings.get(menu_id, {}).get(item_id, {}).get('hidden', False)


def set_item_visibility(item_id, menu_id, is_hidden):
    """Set item 'item_id' of menu 'menu_id' visibility in the menus_settings json file

    Args:
        item_id (str): (e.g. live_tv)
        menu_id (str): (e.g. root)
        is_hidden (bool): True if item_id must be hidden
    """
    menus_settings = get_menus_settings()
    if menu_id not in menus_settings:
        menus_settings[menu_id] = {}
    if item_id not in menus_settings[menu_id]:
        menus_settings[menu_id][item_id] = {}
    menus_settings[menu_id][item_id]['hidden'] = is_hidden
    save_menus_settings(menus_settings)


def get_item_order(item_id, menu_id, item_infos):
    """Get item 'item_id' order of menu 'menu_id'

    Args:
        item_id (str): (e.g. live_tv)
        menu_id (str): (e.g. root)
        item_infos (dict): Information from the skeleton 'menu' dict
    Returns:
        int
    """
    menus_settings = get_menus_settings()
    item_order = menus_settings.get(menu_id, {}).get(item_id, {}).get('order', None)
    if item_order is None:
        item_order = item_infos['order']
    return item_order


def set_item_order(item_id, menu_id, order):
    """Set item 'item_id' of menu 'menu_id' order in the menus_settings json file

    Args:
        item_id (str): (e.g. live_tv)
        menu_id (str): (e.g. root)
        order (int): (e.g. 3)
    """
    menus_settings = get_menus_settings()
    if menu_id not in menus_settings:
        menus_settings[menu_id] = {}
    if item_id not in menus_settings[menu_id]:
        menus_settings[menu_id][item_id] = {}
    menus_settings[menu_id][item_id]['order'] = order
    save_menus_settings(menus_settings)


"""Utility functions used to build a Kodi menu

"""


def get_sorted_menu(plugin, menu_id):
    """Get ordered 'menu_id' menu without disabled and hidden items

    Args:
        plugin (codequick.script.Script)
        menu_id (str): Menu to get (e.g. root)
    Returns:
        list<tuple> List of items (item_order, item_id, item_infos)
    """

    # The current menu to build contains
    # all the items present in the 'menu_id'
    # skeleton file
    current_menu = importlib.import_module('resources.lib.skeletons.' +
                                           menu_id).menu

    # Notify user for the new M3U Live TV feature
    if menu_id == "live_tv" and \
            get_kodi_version() >= 18 and \
            plugin.setting.get_boolean('show_live_tv_m3u_info'):

        r = xbmcgui.Dialog().yesno(plugin.localize(30600),
                                   plugin.localize(30605),
                                   plugin.localize(30606))
        if not r:
            plugin.setting['show_live_tv_m3u_info'] = False

    # Keep in memory the first menu taken
    # in order to provide a prefix when the user
    # add a favourite
    fav.guess_fav_prefix(menu_id)

    # First, we have to sort the current menu items
    # according to each item order and we have
    # to hide each disabled item
    menu = []
    for item_id, item_infos in list(current_menu.items()):

        add_item = True

        # If the item is disabled in skeleton file
        # (e.g. if a channel is not available anymore)
        if item_infos['enabled'] is False:
            add_item = False

        # If the item is hidden by the user setting
        if is_item_hidden(item_id, menu_id):
            add_item = False

        # If the desired language is not available
        if 'available_languages' in item_infos:
            desired_language = utils.ensure_unicode(Script.setting[item_id + '.language'])
            if desired_language not in item_infos['available_languages']:
                add_item = False

        if add_item:
            item_order = get_item_order(item_id, menu_id, item_infos)

            item = (item_order, item_id, item_infos)

            menu.append(item)

    # We sort the menu according to the item_order values
    return sorted(menu, key=lambda x: x[0])


def add_context_menus_to_item(item, item_id, item_index, menu_id, menu_len, is_playable=False, item_infos={}):
    """Add basic context menus to the item

    Args:
        plugin (codequick.script.Script)
        item (codequick.listing.Listitem): Item for which we want to add context menus
        item_id (str): Id of the item
        item_index (int): Index of the item
        menu_id (str): Menu to get (e.g. root)
        menu_len (int): Length of the item menu
    """

    # Move up
    if item_index > 0:
        item.context.script(move_item,
                            Script.localize(30501),
                            direction='up',
                            item_id=item_id,
                            menu_id=menu_id)

    # Move down
    if item_index < menu_len - 1:
        item.context.script(move_item,
                            Script.localize(30500),
                            direction='down',
                            item_id=item_id,
                            menu_id=menu_id)

    # Hide
    item.context.script(hide_item,
                        Script.localize(30502),
                        item_id=item_id,
                        menu_id=menu_id)


    # Add to add-on favourites
    item.context.script(fav.add_item_to_favourites,
                        Script.localize(30800),
                        is_playable=is_playable,
                        item_infos=item_infos)

    return


def item_post_treatment(item, is_playable=False, is_downloadable=False):
    """Add needed context menus to 'item'

    Args:
        is_playable (bool): If 'item' is playable
        is_downloadable (bool): If 'item' is downloadable
    Returns:
        str: (translated) label of 'item_id'
    """

    # Add `Download` context menu to 'item' if 'item' is downloadable
    if is_downloadable:
        item.context.script(item.path,
                            Script.localize(30503),
                            download_mode=True,
                            **item.params)

    # Add `Add to add-on favourites` context menu to 'item'
    item.context.script(fav.add_item_to_favourites,
                        Script.localize(30800),
                        is_playable=is_playable)

    return


"""Context menu callback functions

"""


@Script.register
def move_item(plugin, direction, item_id, menu_id):
    """Callback function of 'move item' conext menu

    Args:
        plugin (codequick.script.Script)
        direction (str): 'down' or 'up'
        item_id (str): item_id to move
        menu_id (str): menu_id of the item
    """
    if direction == 'down':
        offset = 1
    elif direction == 'up':
        offset = -1

    item_to_move_id = item_id

    menu = get_sorted_menu(plugin, menu_id)

    for k in range(0, len(menu)):
        item = menu[k]
        item_order = item[0]
        item_id = item[1]
        if item_to_move_id == item_id:
            item_to_swap = menu[k + offset]
            item_to_swap_order = item_to_swap[0]
            item_to_swap_id = item_to_swap[1]
            set_item_order(item_to_move_id, menu_id, item_to_swap_order)
            set_item_order(item_to_swap_id, menu_id, item_order)
            xbmc.executebuiltin('Container.Refresh()')
            break


@Script.register
def hide_item(plugin, item_id, menu_id):
    """Callback function of 'hide item' context menu

    Args:
        plugin (codequick.script.Script)
        item_id (str): item_id to move
        menu_id (str): menu_id of the item
    """
    if plugin.setting.get_boolean('show_hidden_items_information'):
        xbmcgui.Dialog().ok(
            plugin.localize(30600),
            plugin.localize(30601))
        plugin.setting['show_hidden_items_information'] = False

    set_item_visibility(item_id, menu_id, True)
    xbmc.executebuiltin('Container.Refresh()')


"""Settings callback functions


"""


@Script.register
def restore_default_order(plugin):
    """Callback function of 'Restore default order of all menus' setting button

    Args:
        plugin (codequick.script.Script)
    """

    menus_settings = get_menus_settings()
    for menu_id, items in menus_settings.items():
        for item_id, item in items.items():
            item.pop('order', None)
    save_menus_settings(menus_settings)
    plugin.notify(plugin.localize(30407), '')


@Script.register
def unmask_all_hidden_items(plugin):
    """Callback function of 'Unmask all hidden items' setting button

    Args:
        plugin (codequick.script.Script)
    """

    menus_settings = get_menus_settings()
    for menu_id, items in menus_settings.items():
        for item_id, item in items.items():
            item.pop('hidden', None)
    save_menus_settings(menus_settings)
    plugin.notify(plugin.localize(30408), '')


@Script.register
def unmask_items(plugin, menu_id):
    """Callback function of 'Unmask items' setting buttons

    Args:
        plugin (codequick.script.Script)
        menu_id (str): Menu for which we cant to unmask items
    """

    menus_settings = get_menus_settings()
    if menu_id not in menus_settings:
        return

    menu = importlib.import_module('resources.lib.skeletons.' + menu_id).menu

    hidden_items = []
    hidden_items_labels = []
    for item_id, item in menus_settings[menu_id].items():
        if item.get('hidden', False):
            hidden_items.append(item_id)
            hidden_items_labels.append(get_item_label(item_id, menu[item_id]))

    if not hidden_items:
        return

    seleted_item = xbmcgui.Dialog().select(
        plugin.localize(30406),
        hidden_items_labels)
    if seleted_item == -1:
        return

    menus_settings[menu_id][hidden_items[seleted_item]].pop('hidden')
    save_menus_settings(menus_settings)
