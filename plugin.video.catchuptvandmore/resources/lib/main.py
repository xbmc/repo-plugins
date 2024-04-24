# -*- coding: utf-8 -*-
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import importlib
import sys

from codequick import Route, Resolver, Listitem, Script, utils
import urlquick
from kodi_six import xbmc, xbmcgui, xbmcplugin

from resources.lib.addon_utils import get_item_label, get_item_media_path
import resources.lib.favourites as fav
from resources.lib.kodi_utils import build_kodi_url, get_params_in_query
from resources.lib.menu_utils import get_sorted_menu, add_context_menus_to_item


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

            # If it's a live channel we retrieve xmltv id
            if 'available_languages' in item_infos:
                if isinstance(item_infos['available_languages'], dict):
                    lang = utils.ensure_unicode(Script.setting[item_id + '.language'])
                    lang_infos = item_infos['available_languages'][lang]
                    item.params['xmltv_id'] = lang_infos.get('xmltv_id')
            else:
                item.params['xmltv_id'] = item_infos.get('xmltv_id')

            item.params['item_id'] = item_id

            # Set callback function for this item
            if 'route' in item_infos:
                item.set_callback((Route.ref(item_infos['route'])))
            elif 'resolver' in item_infos:
                item.set_callback((Resolver.ref(item_infos['resolver'])))
            else:
                # This case should not happen
                # Ignore this item to prevent any error for this menu
                continue

            # Add needed context menus to this item
            add_context_menus_to_item(item,
                                      item_id,
                                      index,
                                      menu_id,
                                      len(menu),
                                      is_playable='resolver' in item_infos,
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
    tv_guide = xmltv.grab_current_programmes(live_country_id)

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

        # Playcount is useless for live streams
        item.info['playcount'] = 0

        yield item


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
    for item_hash, item_dict in list(fav_dict['items'].items()):
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
