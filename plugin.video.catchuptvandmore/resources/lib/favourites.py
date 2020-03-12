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

import os
import json
from builtins import str
from builtins import range
from kodi_six import xbmc
from kodi_six import xbmcgui
from kodi_six import xbmcvfs

from codequick import utils, storage, Script, listing
from hashlib import md5

from resources.lib.labels import LABELS
import resources.lib.mem_storage as mem_storage
from resources.lib.migration_utils import migrate_from_pickled_fav
from resources.lib.kodi_utils import get_selected_item_art, get_selected_item_label, get_selected_item_params, get_selected_item_stream, get_selected_item_info
from resources.lib.addon_utils import get_item_label, get_item_media_path


FAV_JSON_FP = os.path.join(Script.get_info('profile'), "favourites.json")


def get_fav_dict_from_json():
    """Get favourites dict from favourites.json

    Returns:
        dict: Favourites dict
    """

    migrate_from_pickled_fav()
    if not xbmcvfs.exists(FAV_JSON_FP):
        return {}
    try:
        with open(FAV_JSON_FP) as f:
            return json.load(f)
    except Exception:
        Script.log('Failed to load favourites json data')
        xbmcvfs.delete(FAV_JSON_FP)
        return {}


def save_fav_dict_in_json(fav_dict):
    """Dump favourites dict in favourites.json

    Args:
        fav_dict (dict): Favourites dict to save
    """

    with open(FAV_JSON_FP, 'w') as f:
        json.dump(fav_dict, f, indent=4)


def guess_fav_prefix(item_id):
    """Keep in memory the current main category (e.g. Live TV, Catch-up TV, ...)
    This category label will be used as a prefix when the user add a favourite

    """

    prefix = 'empty'
    if item_id == 'live_tv':
        prefix = Script.localize(LABELS['live_tv'])
    elif item_id == 'replay':
        prefix = Script.localize(LABELS['replay'])
    elif item_id == 'websites':
        prefix = Script.localize(LABELS['websites'])
    elif item_id == 'root':
        prefix = ''
    if prefix != 'empty':
        s = mem_storage.MemStorage('fav')
        s['prefix'] = prefix


@Script.register
def add_item_to_favourites(plugin, is_playable=False, item_infos={}):
    """Callback function of the 'Add to add-on favourites' item context menu

    Args:
        plugin (codequick.script.Script)
        is_playable (bool): If 'item' is playable
        item_infos (dict)
    """

    # Need to use same keywords as
    # https://scriptmodulecodequick.readthedocs.io/en/latest/_modules/codequick/listing.html#Listitem.from_dict
    # in order to be able to directly use `Listitem.from_dict` later
    item_dict = {}

    # --> subtitles (TODO)
    # item_dict['subtitles'] = list(item.subtitles)

    # --> art
    item_dict['art'] = get_selected_item_art()

    # --> info
    item_dict['info'] = get_selected_item_info()

    # --> stream
    item_dict['stream'] = get_selected_item_stream()

    # --> context (TODO)
    item_dict['context'] = []

    # --> properties (TODO)
    item_dict['properties'] = {}

    # --> params
    item_dict['params'] = get_selected_item_params()

    # --> label
    item_dict['label'] = get_selected_item_label()

    if item_infos:
        # This item comes from tv_guide_menu
        # We need to remove guide TV related
        # elements

        item_id = item_dict['params']['item_id']
        item_dict['label'] = get_item_label(item_id)

        item_dict['art']["thumb"] = ''
        if 'thumb' in item_infos:
            item_dict['art']["thumb"] = get_item_media_path(
                item_infos['thumb'])

        item_dict['art']["fanart"] = ''
        if 'fanart' in item_infos:
            item_dict['art']["fanart"] = get_item_media_path(
                item_infos['fanart'])

        item_dict['info']['plot'] = ''

    # Extract the callback
    item_path = xbmc.getInfoLabel('ListItem.Path')
    item_dict['callback'] = item_path.replace(
        'plugin://plugin.video.catchuptvandmore', '')

    s = mem_storage.MemStorage('fav')
    prefix = ''
    try:
        prefix = s['prefix']
    except KeyError:
        pass

    label_proposal = item_dict['label']
    if prefix != '':
        label_proposal = prefix + ' - ' + label_proposal

    # Ask the user to edit the label
    label = utils.keyboard(
        plugin.localize(LABELS['Favorite name']), label_proposal)

    # If user aborded do not add this item to favourite
    if label == '':
        return False

    item_dict['label'] = label
    item_dict['params']['_title_'] = label
    item_dict['info']['title'] = label

    item_dict['params']['is_playable'] = is_playable
    item_dict['params']['is_folder'] = not is_playable

    # Compute fav hash
    item_hash = md5(str(item_dict).encode('utf-8')).hexdigest()

    # Add this item to favourites json file
    fav_dict = get_fav_dict_from_json()
    item_dict['params']['order'] = len(fav_dict)

    fav_dict[item_hash] = item_dict

    # Save json file with new fav_dict
    save_fav_dict_in_json(fav_dict)

    Script.notify(Script.localize(30033), Script.localize(30805), display_time=7000)


@Script.register
def rename_favourite_item(plugin, item_hash):
    """Callback function of the 'Rename' favourite item context menu

    Args:
        plugin (codequick.script.Script)
        item_hash (str): Item hash of the favourite item to rename
    """

    item_label = utils.keyboard(plugin.localize(LABELS['Favorite name']),
                                xbmc.getInfoLabel('ListItem.Label'))

    # If user aborded do not edit this item
    if item_label == '':
        return False
    fav_dict = get_fav_dict_from_json()
    fav_dict[item_hash]['label'] = item_label
    fav_dict[item_hash]['params']['_title_'] = item_label
    fav_dict[item_hash]['info']['title'] = item_label
    save_fav_dict_in_json(fav_dict)
    xbmc.executebuiltin('Container.Refresh()')


@Script.register
def remove_favourite_item(plugin, item_hash):
    """Callback function of the 'Remove' favourite item context menu

    Args:
        plugin (codequick.script.Script)
        item_hash (str): Item hash of the favourite item to remove
    """

    fav_dict = get_fav_dict_from_json()
    del fav_dict[item_hash]

    # We need to fix the order param
    # in order to not break the move up/down action
    menu = []
    for item_hash, item_dict in list(fav_dict.items()):
        item = (item_dict['params']['order'], item_hash)

        menu.append(item)
    menu = sorted(menu, key=lambda x: x[0])

    for k in range(0, len(menu)):
        item = menu[k]
        item_hash = item[1]
        fav_dict[item_hash]['params']['order'] = k
    save_fav_dict_in_json(fav_dict)
    xbmc.executebuiltin('Container.Refresh()')


@Script.register
def move_favourite_item(plugin, direction, item_hash):
    """Callback function of the 'Move Up/Down' favourite item context menu

    Args:
        plugin (codequick.script.Script)
        direction (str): 'down' or 'up'
        item_hash (str): Item hash of the favourite item to move
    """

    if direction == 'down':
        offset = 1
    elif direction == 'up':
        offset = -1

    fav_dict = get_fav_dict_from_json()
    item_to_move_id = item_hash
    item_to_move_order = fav_dict[item_hash]['params']['order']

    menu = []
    for item_hash, item_dict in list(fav_dict.items()):
        item = (item_dict['params']['order'], item_hash, item_dict)

        menu.append(item)
    menu = sorted(menu, key=lambda x: x[0])

    for k in range(0, len(menu)):
        item = menu[k]
        item_hash = item[1]
        if item_to_move_id == item_hash:
            item_to_swap = menu[k + offset]
            item_to_swap_order = item_to_swap[0]
            item_to_swap_id = item_to_swap[1]
            fav_dict[item_to_move_id]['params']['order'] = item_to_swap_order
            fav_dict[item_to_swap_id]['params']['order'] = item_to_move_order
            save_fav_dict_in_json(fav_dict)
            xbmc.executebuiltin('Container.Refresh()')
            break

    return False


def ask_to_delete_error_fav_item(item_hash):
    """Callback function if a favourite item trigger an error

    Suggest user to delete
    the fav item that trigger an error

    Args:
        item_hash (str): Item hash that trigger an error
    """

    r = xbmcgui.Dialog().yesno(Script.localize(LABELS['Information']),
                               Script.localize(30807))
    if r:
        remove_favourite_item(plugin=None, item_hash=item_hash)


@Script.register
def delete_favourites(plugin):
    """Callback function of 'Delete favourites' setting button

    Args:
        plugin (codequick.script.Script)
    """

    Script.log('Delete favourites db')
    xbmcvfs.delete(os.path.join(Script.get_info('profile'), 'favourites.pickle'))
    xbmcvfs.delete(os.path.join(Script.get_info('profile'), 'favourites.json'))
    Script.notify(Script.localize(30374), '')
