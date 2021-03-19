# -*- coding: utf-8 -*-
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import range, str
from hashlib import md5
import json
import os

from codequick import Script, utils
from kodi_six import xbmc, xbmcgui, xbmcvfs

from resources.lib.addon_utils import get_item_label, get_item_media_path
from resources.lib.kodi_utils import get_selected_item_art, get_selected_item_label, get_selected_item_params, get_selected_item_stream, get_selected_item_info
import resources.lib.mem_storage as mem_storage

FAV_JSON_FP = os.path.join(Script.get_info('profile'), "favourites.json")
FAV_FORMAT_VERSION = 1


def migrate_fav_format(current_fav_format, fav_dict):
    """Migrate favourites dict in last format version

    Args:
        current_fav_format (int): Current format version of the favourites json file
        fav_dict (dict): Favourites dict in old format
    Returns:
        dict: Updated favourites dict in latest format version
    """
    Script.log('Migrate favourites dict in last format version')
    new_dict = fav_dict
    if current_fav_format == 0:
        items = fav_dict
        new_dict = {
            'items': items,
            'format_version': 1
        }
        current_fav_format = 1
    return new_dict


def get_fav_dict_from_json():
    """Get favourites dict from favourites.json

    Returns:
        dict: Favourites dict
    """

    def get_fresh_dict():
        return {
            'items': {},
            'format_version': FAV_FORMAT_VERSION
        }

    if not xbmcvfs.exists(FAV_JSON_FP):
        return get_fresh_dict()
    try:
        with open(FAV_JSON_FP) as f:
            fav_dict = json.load(f)
            current_fav_format = fav_dict.get('format_version', 0)
            if current_fav_format < FAV_FORMAT_VERSION:
                fav_dict = migrate_fav_format(current_fav_format, fav_dict)
            return fav_dict
    except Exception:
        Script.log('Failed to load favourites json data')
        xbmcvfs.delete(FAV_JSON_FP)
        return get_fresh_dict()


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
    prefixes = {
        'root': '',
        'live_tv': Script.localize(30030),
        'replay': Script.localize(30031),
        'websites': Script.localize(30032)
    }
    if item_id in prefixes:
        s = mem_storage.MemStorage('fav')
        s['prefix'] = prefixes[item_id]


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

    # --> callback (string)
    item_dict['callback'] = xbmc.getInfoLabel('ListItem.Path').replace(
        'plugin://plugin.video.catchuptvandmore', '')

    # --> label (string)
    item_dict['label'] = get_selected_item_label()

    # --> art (dict)
    item_dict['art'] = get_selected_item_art()

    # --> info (dict)
    item_dict['info'] = get_selected_item_info()

    # --> stream (dict)
    item_dict['stream'] = get_selected_item_stream()

    # --> context (list) (TODO)
    item_dict['context'] = []

    # --> properties (dict) (TODO)
    item_dict['properties'] = {}

    # --> params (dict)
    item_dict['params'] = get_selected_item_params()

    # --> subtitles (list) (TODO)
    item_dict['subtitles'] = []

    if item_infos:
        # This item comes from tv_guide_menu
        # We need to remove guide TV related
        # elements

        item_id = item_dict['params']['item_id']
        item_dict['label'] = get_item_label(item_id, item_infos)

        item_dict['art']["thumb"] = ''
        if 'thumb' in item_infos:
            item_dict['art']["thumb"] = get_item_media_path(
                item_infos['thumb'])

        item_dict['art']["fanart"] = ''
        if 'fanart' in item_infos:
            item_dict['art']["fanart"] = get_item_media_path(
                item_infos['fanart'])

        item_dict['info']['plot'] = ''

    s = mem_storage.MemStorage('fav')
    try:
        prefix = s['prefix']
    except KeyError:
        prefix = ''

    label_proposal = item_dict['label']
    if prefix != '':
        label_proposal = prefix + ' - ' + label_proposal

    # Ask the user to edit the label
    label = utils.keyboard(
        plugin.localize(30801), label_proposal)

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

    fav_dict['items'][item_hash] = item_dict

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

    item_label = utils.keyboard(plugin.localize(30801),
                                xbmc.getInfoLabel('ListItem.Label'))

    # If user aborded do not edit this item
    if item_label == '':
        return False
    fav_dict = get_fav_dict_from_json()
    fav_dict['items'][item_hash]['label'] = item_label
    fav_dict['items'][item_hash]['params']['_title_'] = item_label
    fav_dict['items'][item_hash]['info']['title'] = item_label
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
    del fav_dict['items'][item_hash]

    # We need to fix the order param
    # in order to not break the move up/down action
    menu = []
    for item_hash, item_dict in list(fav_dict['items'].items()):
        item = (item_dict['params']['order'], item_hash)

        menu.append(item)
    menu = sorted(menu, key=lambda x: x[0])

    for k in range(0, len(menu)):
        item = menu[k]
        item_hash = item[1]
        fav_dict['items'][item_hash]['params']['order'] = k
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
    item_to_move_order = fav_dict['items'][item_hash]['params']['order']

    menu = []
    for item_hash, item_dict in list(fav_dict['items'].items()):
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
            fav_dict['items'][item_to_move_id]['params']['order'] = item_to_swap_order
            fav_dict['items'][item_to_swap_id]['params']['order'] = item_to_move_order
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

    r = xbmcgui.Dialog().yesno(Script.localize(30600),
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
    xbmcvfs.delete(os.path.join(Script.get_info('profile'), 'favourites.json'))
    Script.notify(Script.localize(30374), '')
