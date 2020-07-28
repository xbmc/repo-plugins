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
from codequick import Route, Resolver, Listitem, Script
import urlquick
from kodi_six import xbmc
from kodi_six import xbmcgui
from kodi_six import xbmcplugin
from six import string_types

# Local imports

from resources.lib.kodi_utils import build_kodi_url, get_params_in_query
import resources.lib.favourites as fav
from resources.lib.menu_utils import get_sorted_menu, add_context_menus_to_item
from resources.lib.addon_utils import get_item_label, get_item_media_path


@Route.register
def root(plugin):
    """Build root menu of the addon (Live TV, Catch-up TV, Websites, ...)

    Args:
        plugin (codequick.script.Script)
    Returns:
        Iterator[codequick.listing.Listitem]: Kodi root menu
    """

    # First menu to build is the root menu
    # (see 'menu' dictionnary in root.py)
    return generic_menu(plugin, 'root')


@Route.register
def generic_menu(plugin, item_id=None, **kwargs):
    """Build 'item_id' menu of the addon

    Args:
        plugin (codequick.script.Script)
        item_id (str): Menu to build (e.g. root)
    Returns:
        Iterator[codequick.listing.Listitem]: Kodi 'item_id' menu
    """

    if item_id is None:
        # Fix https://github.com/Catch-up-TV-and-More/plugin.video.catchuptvandmore/issues/304
        xbmc.executebuiltin("Action(Back,%s)" % xbmcgui.getCurrentWindowId())
        yield False

    else:
        menu_id = item_id

        # If 'menu_id' menu contains only one item, directly open this item
        plugin.redirect_single_item = True

        # Get ordered 'menu_id' menu
        # without disabled and hidden items
        menu = get_sorted_menu(plugin, menu_id)

        if not menu:
            # If the selected menu is empty just reload the current menu
            yield False

        for index, (item_order, item_id, item_infos) in enumerate(menu):

            item = Listitem()

            # Set item label
            item.label = get_item_label(item_id, item_infos)

            # Set item art
            if 'thumb' in item_infos:
                item.art["thumb"] = get_item_media_path(item_infos['thumb'])

            if 'fanart' in item_infos:
                item.art["fanart"] = get_item_media_path(
                    item_infos['fanart'])

            # Set item params
            # If this item requires a module to work, get
            # the module path to be loaded
            if 'module' in item_infos:
                item.params['item_module'] = item_infos['module']

            if 'xmltv_id' in item_infos:
                item.params['xmltv_id'] = item_infos['xmltv_id']

            item.params['item_id'] = item_id

            # Get cllback function of this item
            item_callback = eval(item_infos['callback'])
            item.set_callback(item_callback)

            # Add needed context menus to this item
            add_context_menus_to_item(item,
                                      item_id,
                                      index,
                                      menu_id,
                                      len(menu),
                                      is_playable=(item_infos['callback'] == 'live_bridge'),
                                      item_infos=item_infos)

            yield item


@Route.register
def tv_guide_menu(plugin, item_id, **kwargs):
    """Build 'item_id' menu of the addon and add TV guide information

    Args:
        plugin (codequick.script.Script)
        item_id (str): Country live TV menu to build (e.g. fr_live)
    Returns:
        Iterator[codequick.listing.Listitem]: Kodi 'item_id' menu
    """

    live_country_id = item_id

    # Move up and move down action only work with this sort method
    plugin.add_sort_methods(xbmcplugin.SORT_METHOD_UNSORTED)

    # Get tv_guide of this country
    xmltv = importlib.import_module('resources.lib.xmltv')
    tv_guide = xmltv.grab_tv_guide(live_country_id)

    # Treat this menu as a generic menu and add, if any, tv guide information
    for item in generic_menu(plugin, live_country_id):

        # If we have program information from the grabber
        if 'xmltv_id' in item.params and item.params['xmltv_id'] in tv_guide:
            guide_infos = tv_guide[item.params['xmltv_id']]

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
                item.art["clearlogo"] = item.art["thumb"]
                item.art["thumb"] = guide_infos['icon']
        yield item


@Route.register
def replay_bridge(plugin, item_id, item_module, **kwargs):
    """Bridge between main.py file and each channel modules files

    Args:
        plugin (codequick.script.Script)
        item_id (str): Catch-up TV channel menu to build (e.g. tf1)
        item_module (str): Channel module (e.g. resources.lib.channels.fr.mytf1)
    Returns:
        Iterator[codequick.listing.Listitem]: Kodi 'item_id' menu
    """

    module = importlib.import_module(item_module)
    return module.replay_entry(plugin, item_id)


@Route.register
def website_bridge(plugin, item_id, item_module, **kwargs):
    """Bridge between main.py file and each website modules files

    Args:
        plugin (codequick.script.Script)
        item_id (str): Website menu to build (e.g. allocine)
        item_module (str): Channel module (e.g. resources.lib.websites.allocine)
    Returns:
        Iterator[codequick.listing.Listitem]: Kodi 'item_id' menu
    """

    module = importlib.import_module(item_module)
    return module.website_entry(plugin, item_id)


@Route.register
def multi_live_bridge(plugin, item_id, item_module, **kwargs):
    """Bridge between main.py file and each channel modules files

    Args:
        plugin (codequick.script.Script)
        item_id (str): Multi live TV channel menu to build (e.g. auvio)
        item_module (str): Channel module (e.g. resources.lib.channels.be.rtbf)
    Returns:
        Iterator[codequick.listing.Listitem]: Kodi 'item_id' menu
    """

    # Let's go to the module file ...
    module = importlib.import_module(item_module)
    return module.multi_live_entry(plugin, item_id)


@Resolver.register
def live_bridge(plugin, item_id, item_module, **kwargs):
    """Bridge between main.py file and each channel modules files

    Args:
        plugin (codequick.script.Script)
        item_id (str): Live TV channel menu to build (e.g. tf1)
        item_module (str): Channel module (e.g. resources.lib.channels.fr.mytf1)
        **kwargs: Arbitrary keyword arguments
    Returns:
        Iterator[codequick.listing.Listitem]: Kodi 'item_id' menu
    """

    # Let's go to the module file ...
    module = importlib.import_module(item_module)
    return module.live_entry(plugin, item_id, **kwargs)


@Route.register
def favourites(plugin, start=0, **kwargs):
    """Build 'favourites' menu of the addon ('favourites' menu callback function)

    Args:
        plugin (codequick.script.Script)
        start (int): Index of the menu starting item (multiple pages support)
        **kwargs: Arbitrary keyword arguments
    Returns:
        Iterator[codequick.listing.Listitem]: Kodi 'favourites' menu
    """

    # Get sorted items
    sorted_menu = []
    fav_dict = fav.get_fav_dict_from_json()
    menu = []
    for item_hash, item_dict in list(fav_dict.items()):
        item = (item_dict['params']['order'], item_hash, item_dict)
        menu.append(item)

    # We sort the menu according to the item_order values
    sorted_menu = sorted(menu, key=lambda x: x[0])

    # Notify the user if there is no item in favourites
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

        item_dict['params']['from_fav'] = True
        item_dict['params']['item_hash'] = item_hash

        try:
            # Build item from dict
            item = Listitem.from_dict(**item_dict)

            # Generate a valid callback
            url = build_kodi_url(item_dict['callback'], item_dict['params'])
            item.set_callback(url, is_folder=item_dict['params']['is_folder'], is_playbale=item_dict['params']['is_playable'])

            item.is_folder = item_dict['params']['is_folder']
            item.is_playbale = item_dict['params']['is_playable']

            # Rename
            item.context.script(fav.rename_favourite_item,
                                plugin.localize(30804),
                                item_hash=item_hash)

            # Remove
            item.context.script(fav.remove_favourite_item,
                                plugin.localize(30802),
                                item_hash=item_hash)

            # Move up
            if item_dict['params']['order'] > 0:
                item.context.script(fav.move_favourite_item,
                                    plugin.localize(30501),
                                    direction='up',
                                    item_hash=item_hash)

            # Move down
            if item_dict['params']['order'] < len(fav_dict) - 1:
                item.context.script(fav.move_favourite_item,
                                    plugin.localize(30500),
                                    direction='down',
                                    item_hash=item_hash)

            yield item
        except Exception:
            fav.remove_favourite_item(plugin, item_hash)


def error_handler(exception):
    """Callback function called when the run() triggers an error

    Args:
        exception (Exception)
    """

    # Parameters found in Kodi URL during this error
    params = get_params_in_query(sys.argv[2])

    # If it's an HTTPError
    if isinstance(exception, urlquick.HTTPError):
        code = exception.code
        msg = exception.msg
        # hdrs = exception.hdrs
        # url = exception.filename
        Script.log('urlquick.get() failed with HTTPError code {} with message "{}"'.format(code, msg, lvl=Script.ERROR))

        # Build dialog message
        dialog_message = msg

        http_code_msg = {
            500: 30891,
            401: 30892,
            403: 30893,
            402: 30894,
            404: 30895
        }

        if code in http_code_msg:
            dialog_message = Script.localize(http_code_msg[code])

        # Build dialog title
        dialog_title = Script.localize(30890) + ' ' + str(code)

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
        fav.ask_to_delete_error_fav_item(params['item_hash'])

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
