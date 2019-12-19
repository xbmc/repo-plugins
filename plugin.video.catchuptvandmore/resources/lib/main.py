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
from builtins import str
from builtins import range
import importlib
import sys

# Kodi imports
from codequick import Route, Resolver, Listitem, Script, utils, storage
import urlquick
from kodi_six import xbmc
from kodi_six import xbmcgui
from kodi_six import xbmcplugin
from six import string_types

# Local imports
from resources.lib.labels import LABELS, save_labels_in_mem_storage
from resources.lib import common
import resources.lib.cq_utils as cqu
from resources.lib import entrypoint_utils
from resources.lib.listitem_utils import item2dict, get_item_label
import resources.lib.favourites as fav


def get_sorted_menu(plugin, menu_id):
    # The current menu to build contains
    # all the items present in the 'menu_id'
    # skeleton file
    current_menu = importlib.import_module('resources.lib.skeletons.' +
                                           menu_id).menu

    # Notify user for the new M3U Live TV feature
    if menu_id == "live_tv" and \
            cqu.get_kodi_version() >= 18 and \
            plugin.setting.get_boolean('show_live_tv_m3u_info'):

        r = xbmcgui.Dialog().yesno(plugin.localize(LABELS['Information']),
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

        # If the item is enable
        if not Script.setting.get_boolean(item_id):
            add_item = False

        # If the desired language is not avaible
        if 'available_languages' in item_infos:
            desired_language = utils.ensure_unicode(Script.setting[item_id + '.language'])
            if desired_language not in item_infos['available_languages']:
                add_item = False

        if add_item:
            # Get order value in settings file
            item_order = Script.setting.get_int(item_id + '.order')

            item = (item_order, item_id, item_infos)

            menu.append(item)

    # We sort the menu according to the item_order values
    return sorted(menu, key=lambda x: x[0])


def add_context_menus_to_item(plugin, item, index, menu_id, menu_len,
                              **kwargs):

    # Move up
    if index > 0:
        item.context.script(move_item,
                            plugin.localize(LABELS['Move up']),
                            direction='up',
                            item_id=item.params['item_id'],
                            menu_id=menu_id)

    # Move down
    if index < menu_len - 1:
        item.context.script(move_item,
                            plugin.localize(LABELS['Move down']),
                            direction='down',
                            item_id=item.params['item_id'],
                            menu_id=menu_id)

    # Hide
    item.context.script(hide_item,
                        plugin.localize(LABELS['Hide']),
                        item_id=item.params['item_id'])


    # Add to add-on favourites
    is_playable = False
    if 'is_playable' in kwargs:
        is_playable = kwargs['is_playable']
    elif 'item_infos' in kwargs and \
            kwargs['item_infos']['callback'] == 'live_bridge':
        is_playable = True

    fav.add_fav_context(item,
                        item2dict(item),
                        is_playable=is_playable,
                        channel_infos=kwargs.get('channel_infos', None))

    return


@Route.register
def root(plugin):
    """
    root is the entry point
    of Catch-up TV & More
    """
    # Save LABELS dict in mem storage
    # to improve addon navigation speed
    save_labels_in_mem_storage()

    # First menu to build is the root menu
    # (see ROOT dictionnary in skeleton.py)
    return generic_menu(plugin, item_id='root')


@Route.register
def generic_menu(plugin, **kwargs):
    """
    Build a generic addon menu
    with all not hidden items
    """
    plugin.redirect_single_item = True

    menu_id = kwargs.get('item_id')
    menu = get_sorted_menu(plugin, menu_id)

    if not menu:
        # If the selected menu is empty just reload the current menu
        yield False

    for index, (item_order, item_id, item_infos) in enumerate(menu):

        item = Listitem()

        # Set item label
        item.label = get_item_label(item_id)

        # Set item art
        if 'thumb' in item_infos:
            item.art["thumb"] = common.get_item_media_path(item_infos['thumb'])

        if 'fanart' in item_infos:
            item.art["fanart"] = common.get_item_media_path(
                item_infos['fanart'])

        # Set item params
        # If this item requires a module to work, get
        # the module path to be loaded
        if 'module' in item_infos:
            item.params['item_module'] = item_infos['module']

        item.params['item_id'] = item_id
        item.params['item_dict'] = item2dict(item)

        # Get the next action to trigger if this
        # item will be selected by the user
        item_callback = eval(item_infos['callback'])
        item.set_callback(item_callback)

        add_context_menus_to_item(plugin,
                                  item,
                                  index,
                                  menu_id,
                                  len(menu),
                                  item_infos=item_infos)

        yield item


@Route.register
def tv_guide_menu(plugin, **kwargs):

    # Move up and move down action only work with this sort method
    plugin.add_sort_methods(xbmcplugin.SORT_METHOD_UNSORTED)

    # Get sorted menu of this live TV country
    menu_id = kwargs.get('item_id')
    menu = get_sorted_menu(plugin, menu_id)

    try:
        # Load xmltv module
        xmltv = importlib.import_module('resources.lib.xmltv')

        # Get tv_guide of this country
        tv_guide = xmltv.grab_tv_guide(menu_id, menu)
    except Exception as e:
        Script.notify(
            Script.localize(LABELS['TV guide']),
            Script.localize(LABELS['An error occurred while getting TV guide']),
            display_time=7000)
        Script.log('xmltv module failed with error: {}'.format(e, lvl=Script.ERROR))
        tv_guide = {}

    for index, (channel_order, channel_id, channel_infos) in enumerate(menu):

        item = Listitem()

        # Set item label
        item.label = get_item_label(channel_id)

        # Set item art
        if 'thumb' in channel_infos:
            item.art["thumb"] = common.get_item_media_path(
                channel_infos['thumb'])

        if 'fanart' in channel_infos:
            item.art["fanart"] = common.get_item_media_path(
                channel_infos['fanart'])

        # If this item requires a module to work, get
        # the module path to be loaded
        if 'module' in channel_infos:
            item.params['item_module'] = channel_infos['module']

        # If we have program infos from the grabber
        if 'xmltv_id' in channel_infos and channel_infos['xmltv_id'] in tv_guide:
            guide_infos = tv_guide[channel_infos['xmltv_id']]

            # Title
            if 'title' in guide_infos:
                item.label = item.label + ' — ' + guide_infos['title']

            # Credits
            credits = []
            for credit, l in guide_infos.get('credits', {}).items():
                for s in l:
                    credits.append(s)
            item.info['credits'] = credits

            # Country
            if 'country' in guide_infos:
                item.info['country'] = guide_infos['country']

            # Category
            if 'category' in guide_infos:
                item.info['genre'] = guide_infos['category']

            # Plot
            plot = []

            # start_time and stop_time must be a string
            if 'start' in guide_infos and 'stop' in guide_infos:
                s = guide_infos['start'] + ' - ' + guide_infos['stop']
                plot.append(s)
            elif 'stop' in guide_infos:
                plot.append(guide_infos['stop'])

            if 'sub-title' in guide_infos:
                plot.append(guide_infos['sub-title'])

            if 'desc' in guide_infos:
                plot.append(guide_infos['desc'])

            item.info['plot'] = '\n'.join(plot)

            # Duration
            item.info["duration"] = guide_infos.get('length')

            # Art
            if 'icon' in guide_infos:
                item.art["thumb"] = guide_infos['icon']

        item.params['item_id'] = channel_id
        item.params['item_dict'] = item2dict(item)

        # Get the next action to trigger if this
        # item will be selected by the user
        item.set_callback(eval(channel_infos['callback']))

        add_context_menus_to_item(plugin,
                                  item,
                                  index,
                                  menu_id,
                                  len(menu),
                                  is_playable=True,
                                  channel_infos=channel_infos)

        yield item


@Route.register
def replay_bridge(plugin, **kwargs):
    """
    replay_bridge is the bridge between the
    addon.py file and each channel modules files.
    Because each time the user enter in a new
    menu level the PLUGIN.run() function is
    executed.
    So we have to load on the fly the corresponding
    module of the channel.
    """

    # Let's go to the module file ...
    item_module = importlib.import_module(kwargs.get('item_module'))
    return item_module.replay_entry(plugin, kwargs.get('item_id'))


@Route.register
def website_bridge(plugin, **kwargs):
    """
    Like replay_bridge
    """

    # Let's go to the module file ...
    item_module = importlib.import_module(kwargs.get('item_module'))
    return item_module.website_entry(plugin, kwargs.get('item_id'))


@Route.register
def multi_live_bridge(plugin, **kwargs):
    """
    Like replay_bridge
    """

    # Let's go to the module file ...
    item_module = importlib.import_module(kwargs.get('item_module'))
    return item_module.multi_live_entry(plugin, kwargs.get('item_id'))


@Resolver.register
def live_bridge(plugin, **kwargs):
    """
    Like replay_bridge
    """

    # If we come from a M3U file, we need to
    # convert the string dict
    # to the real dict object
    if 'item_dict' in kwargs and \
            isinstance(kwargs['item_dict'], string_types):
        kwargs['item_dict'] = eval(kwargs['item_dict'])

    # Let's go to the module file ...
    item_module = importlib.import_module(kwargs.get('item_module'))
    return item_module.live_entry(plugin, kwargs.get('item_id'),
                                  kwargs.get('item_dict', {}))


@Script.register
def move_item(plugin, direction, item_id, menu_id):
    # Callback function of move item conext menu
    if direction == 'down':
        offset = 1
    elif direction == 'up':
        offset = -1

    item_to_move_id = item_id
    item_to_move_order = plugin.setting.get_int(item_to_move_id + '.order')

    menu = get_sorted_menu(plugin, menu_id)

    for k in range(0, len(menu)):
        item = menu[k]
        item_id = item[1]
        if item_to_move_id == item_id:
            item_to_swap = menu[k + offset]
            item_to_swap_order = item_to_swap[0]
            item_to_swap_id = item_to_swap[1]
            plugin.setting[item_to_move_id + '.order'] = item_to_swap_order
            plugin.setting[item_to_swap_id + '.order'] = item_to_move_order
            xbmc.executebuiltin('XBMC.Container.Refresh()')
            break


@Script.register
def hide_item(plugin, item_id):
    # Callback function of hide item context menu
    if plugin.setting.get_boolean('show_hidden_items_information'):
        xbmcgui.Dialog().ok(
            plugin.localize(LABELS['Information']),
            plugin.localize(
                LABELS['To re-enable hidden items go to the plugin settings']))
        plugin.setting['show_hidden_items_information'] = False

    plugin.setting[item_id] = False
    xbmc.executebuiltin('XBMC.Container.Refresh()')


@Route.register
def favourites(plugin, start=0, **kwargs):
    """
    Callback function called when the user enter in the
    favourites folder
    """

    # Get sorted items
    sorted_menu = []
    with storage.PersistentDict("favourites.pickle") as db:
        menu = []
        for item_hash, item_dict in list(db.items()):
            item = (item_dict['params']['order'], item_hash, item_dict)

            menu.append(item)

        # We sort the menu according to the item_order values
        sorted_menu = sorted(menu, key=lambda x: x[0])

    # Notify the user if there is not item in favourites
    if len(sorted_menu) == 0:
        Script.notify(Script.localize(30033), Script.localize(30806), display_time=7000)
        yield False

    # Add each item in the listing
    cnt = 0
    for index, (item_order, item_hash, item_dict) in enumerate(sorted_menu):
        if index < start:
            continue

        # If more thant 30 items add a new page
        if cnt == 30:
            yield Listitem().next_page(start=index)
            break

        cnt += 1
        # Listitem.from_dict fails with subtitles
        # See https://github.com/willforde/script.module.codequick/issues/30
        item_dict.pop('subtitles')

        # Listitem.from_dict only works if context is a list
        if not isinstance(item_dict['context'], list):
            item_dict.pop('context')

        item_dict['params']['from_fav'] = True
        item_dict['params']['item_hash'] = item_hash

        item = Listitem.from_dict(**item_dict)
        url = cqu.build_kodi_url(item_dict['callback'], item_dict['params'])

        item.set_callback(url)

        item.is_folder = item_dict['params']['is_folder']
        item.is_playbale = item_dict['params']['is_playable']

        # Hack for the rename feature
        item.label = item_dict['label']

        # Rename
        item.context.script(fav.rename_favourite_item,
                            plugin.localize(LABELS['Rename']),
                            item_hash=item_hash)

        # Remove
        item.context.script(fav.remove_favourite_item,
                            plugin.localize(LABELS['Remove']),
                            item_hash=item_hash)

        # Move up
        if item_dict['params']['order'] > 0:
            item.context.script(fav.move_favourite_item,
                                plugin.localize(LABELS['Move up']),
                                direction='up',
                                item_hash=item_hash)

        # Move down
        if item_dict['params']['order'] < len(db) - 1:
            item.context.script(fav.move_favourite_item,
                                plugin.localize(LABELS['Move down']),
                                direction='down',
                                item_hash=item_hash)

        yield item


def error_handler(exception):
    """
    This function is called each time
    run() trigger an Exception
    """
    params = entrypoint_utils.get_params_in_query(sys.argv[2])

    # If it's an HTTPError
    if isinstance(exception, urlquick.HTTPError):
        code = exception.code
        msg = exception.msg
        # hdrs = exception.hdrs
        # url = exception.filename
        Script.log('urlquick.get() failed with HTTPError code {} with message "{}"'.format(code, msg, lvl=Script.ERROR))

        # Build dialog message
        dialog_message = msg
        if 'http_code_' + str(code) in LABELS:
            dialog_message = Script.localize(LABELS['http_code_' + str(code)])

        # Build dialog title
        dialog_title = Script.localize(LABELS['HTTP Error code']) + ' ' + str(code)

        # Show xbmc dialog
        xbmcgui.Dialog().ok(dialog_title, dialog_message)

        # If error code is in avoid_log_uploader, then return
        # Else, let log_uploader run
        avoid_log_uploader = [403, 404]
        if code in avoid_log_uploader:
            return

    # If we come from fav menu we
    # suggest user to delete this item
    if 'from_fav' in params:
        fav.ask_to_delete_error_fav_item(params)

    # Else, we ask the user if he wants
    # to share his log to addon devs
    elif Script.setting.get_boolean('log_pop_up'):
        ask_to_share_log = True
        log_exceptions = ['No items found', 'Youtube-DL: Video geo-restricted by the owner']
        for log_exception in log_exceptions:
            if log_exception in str(exception):
                ask_to_share_log = False

        if ask_to_share_log:
            log_uploader = importlib.import_module('resources.lib.log_uploader')
            log_uploader.ask_to_share_log()
