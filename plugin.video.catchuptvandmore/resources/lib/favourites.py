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
from builtins import str
from builtins import range
from kodi_six import xbmc
from kodi_six import xbmcgui
from kodi_six import xbmcvfs

from codequick import utils, storage, Script
from hashlib import md5

from resources.lib.labels import LABELS
from resources.lib import common
import resources.lib.mem_storage as mem_storage


def guess_fav_prefix(item_id):
    """
    When the use add a favourite,
    guess the prefix to add for the
    favourite label according to the
    current main category
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
def add_item_to_favourites(plugin, item_dict={}, **kwargs):
    """
    Callback function called when the user click
    on 'add item to favourite' from an item
    context menu
    """

    if 'channel_infos' in kwargs and \
            kwargs['channel_infos'] is not None:

        # This item come from tv_guide_menu
        # We need to remove guide TV related
        # elements

        item_id = item_dict['params']['item_id']
        label = item_id
        if item_id in LABELS:
            label = LABELS[item_id]
            if isinstance(label, int):
                label = Script.localize(label)
        item_dict['label'] = label

        if 'thumb' in kwargs['channel_infos']:
            item_dict['art']["thumb"] = common.get_item_media_path(
                kwargs['channel_infos']['thumb'])

        if 'fanart' in kwargs['channel_infos']:
            item_dict['art']["fanart"] = common.get_item_media_path(
                kwargs['channel_infos']['fanart'])

        item_dict['info'] = {}

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
    item_dict['label'] = utils.keyboard(
        plugin.localize(LABELS['Favorite name']), label_proposal)

    # If user aborded do not add this item to favourite
    if item_dict['label'] == '':
        return False

    # Add this item to favourite db
    with storage.PersistentDict("favourites.pickle") as db:

        # Compute hash value used as key in the DB
        item_hash = md5(str(item_dict).encode('utf-8')).hexdigest()

        item_dict['params']['order'] = len(db)

        db[item_hash] = item_dict

    Script.notify(Script.localize(30033), Script.localize(30805), display_time=7000)


@Script.register
def rename_favourite_item(plugin, item_hash):
    """
    Callback function called when the user click
    on 'rename' from a favourite item
    context menu
    """
    item_label = utils.keyboard(plugin.localize(LABELS['Favorite name']),
                                xbmc.getInfoLabel('ListItem.Label'))

    # If user aborded do not edit this item
    if item_label == '':
        return False
    with storage.PersistentDict("favourites.pickle") as db:
        db[item_hash]['label'] = item_label
    xbmc.executebuiltin('XBMC.Container.Refresh()')


@Script.register
def remove_favourite_item(plugin, item_hash):
    """
    Callback function called when the user click
    on 'remove' from a favourite item
    context menu
    """
    with storage.PersistentDict("favourites.pickle") as db:
        del db[item_hash]

        # We need to fix the order param
        # in order to not break the move up/down action
        menu = []
        for item_hash, item_dict in list(db.items()):
            item = (item_dict['params']['order'], item_hash)

            menu.append(item)
        menu = sorted(menu, key=lambda x: x[0])

        for k in range(0, len(menu)):
            item = menu[k]
            item_hash = item[1]
            db[item_hash]['params']['order'] = k

    xbmc.executebuiltin('XBMC.Container.Refresh()')


@Script.register
def move_favourite_item(plugin, direction, item_hash):
    """
    Callback function called when the user click
    on 'Move up/down' from a favourite item
    context menu
    """
    if direction == 'down':
        offset = 1
    elif direction == 'up':
        offset = -1

    with storage.PersistentDict("favourites.pickle") as db:
        item_to_move_id = item_hash
        item_to_move_order = db[item_hash]['params']['order']

        menu = []
        for item_hash, item_dict in list(db.items()):
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
                db[item_to_move_id]['params']['order'] = item_to_swap_order
                db[item_to_swap_id]['params']['order'] = item_to_move_order
                xbmc.executebuiltin('XBMC.Container.Refresh()')
                break

        return False


def add_fav_context(item, item_dict, **kwargs):
    """
    Add the 'Add to add-on favourites'
    context menu to item
    """
    if kwargs.get('is_playable', False):
        item_dict['params']['is_folder'] = False
        item_dict['params']['is_playable'] = True
    else:
        item_dict['params']['is_folder'] = True
        item_dict['params']['is_playable'] = False

    item.context.script(add_item_to_favourites,
                        Script.localize(LABELS['Add to add-on favourites']),
                        item_dict=item_dict,
                        **kwargs)


def ask_to_delete_error_fav_item(params):
    """
    Suggest user to delete
    the fav item that trigger the error
    """
    r = xbmcgui.Dialog().yesno(Script.localize(LABELS['Information']),
                               Script.localize(30807))
    if r:
        remove_favourite_item(plugin=None, item_hash=params['item_hash'])


@Script.register
def delete_favourites(plugin):
    """
    Callback function of 'Delete favourites'
    setting button
    """

    Script.log('Delete favourites db')
    xbmcvfs.delete(os.path.join(Script.get_info('profile'), 'favourites.pickle'))
    Script.notify(Script.localize(30374), '')
