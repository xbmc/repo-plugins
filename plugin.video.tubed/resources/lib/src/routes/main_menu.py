# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

from urllib.parse import quote

import xbmcplugin  # pylint: disable=import-error

from ..constants import ADDON_ID
from ..constants import MODES
from ..constants import SCRIPT_MODES
from ..constants.media import GOOGLE_SIGN_IN
from ..items.action import Action
from ..items.directory import Directory
from ..lib.txt_fmt import bold
from ..lib.url_utils import create_addon_path
from ..lib.utils import prompt_to_enable_inputstream_adaptive
from ..storage.users import UserStorage


def invoke(context):  # pylint: disable=too-many-branches,too-many-statements
    xbmcplugin.setPluginCategory(context.handle, context.addon.getAddonInfo('name'))

    if not prompt_to_enable_inputstream_adaptive(context):
        xbmcplugin.endOfDirectory(context.handle, False)
        return

    show_main_menu_item = context.settings.show_main_menu_item

    items = []
    users = None

    logged_in = context.api.logged_in
    tv_logged_in = context.api.tv_logged_in

    fanart = context.addon.getAddonInfo('fanart')

    has_channel_mine = False
    if logged_in:
        has_channel_mine = context.api.channel_by_username('mine') != {}

    if not logged_in or not tv_logged_in:
        if show_main_menu_item('sign.in'):
            label = context.i18n('Sign in with Google')
            action = Action(
                label=bold(label),
                path=create_addon_path(parameters={
                    'mode': str(MODES.SIGN_IN)
                })
            )
            action.ListItem.setArt({
                'icon': GOOGLE_SIGN_IN,
                'thumb': GOOGLE_SIGN_IN,
                'fanart': fanart,
            })

            # artificial centering of plot
            unicode_spaces = ''
            spaces_required = (15 - (len(label) - 19))
            if spaces_required > 0:
                unicode_spaces = '\u2008' * spaces_required
            plot = unicode_spaces + bold(label)
            action.ListItem.setInfo('video', {
                'plot': plot,
                'plotoutline': plot,
            })

            context_menus = _context_menu_hide_menu_item(context, 'sign.in', label)
            action.ListItem.addContextMenuItems(context_menus)
            items.append(tuple(action))

    if show_main_menu_item('most.popular'):
        label = context.i18n('Most Popular')
        directory = Directory(
            label=label,
            path=create_addon_path(parameters={
                'mode': str(MODES.MOST_POPULAR)
            })
        )
        directory.ListItem.setArt({
            'icon': 'DefaultTVShows.png',
            'thumb': 'DefaultTVShows.png',
            'fanart': fanart,
        })
        context_menus = _context_menu_hide_menu_item(context, 'most.popular', label)
        directory.ListItem.addContextMenuItems(context_menus)
        items.append(tuple(directory))

    if show_main_menu_item('most.popular.regionally'):
        label = context.i18n('Most Popular Regionally')
        directory = Directory(
            label=label,
            path=create_addon_path(parameters={
                'mode': str(MODES.MOST_POPULAR_REGIONALLY)
            })
        )
        directory.ListItem.setArt({
            'icon': 'DefaultCountry.png',
            'thumb': 'DefaultCountry.png',
            'fanart': fanart,
        })
        context_menus = _context_menu_hide_menu_item(context, 'most.popular.regionally', label)
        directory.ListItem.addContextMenuItems(context_menus)
        items.append(tuple(directory))

    if show_main_menu_item('categories'):
        label = context.i18n('Categories')
        directory = Directory(
            label=label,
            path=create_addon_path(parameters={
                'mode': str(MODES.CATEGORIES)
            })
        )
        directory.ListItem.setArt({
            'icon': 'DefaultGenre.png',
            'thumb': 'DefaultGenre.png',
            'fanart': fanart,
        })
        context_menus = _context_menu_hide_menu_item(context, 'categories', label)
        directory.ListItem.addContextMenuItems(context_menus)
        items.append(tuple(directory))

    if logged_in:
        if show_main_menu_item('my.channel') and has_channel_mine:
            label = context.i18n('My Channel')
            directory = Directory(
                label=label,
                path=create_addon_path(parameters={
                    'mode': str(MODES.MY_CHANNEL)
                })
            )
            directory.ListItem.setArt({
                'icon': 'DefaultTVShows.png',
                'thumb': 'DefaultTVShows.png',
                'fanart': fanart,
            })
            context_menus = _context_menu_hide_menu_item(context, 'my.channel', label)
            directory.ListItem.addContextMenuItems(context_menus)
            items.append(tuple(directory))

        if show_main_menu_item('liked.videos'):
            label = context.i18n('Liked Videos')
            directory = Directory(
                label=label,
                path=create_addon_path(parameters={
                    'mode': str(MODES.LIKED_VIDEOS)
                })
            )
            directory.ListItem.setArt({
                'icon': 'DefaultTVShows.png',
                'thumb': 'DefaultTVShows.png',
                'fanart': fanart,
            })
            context_menus = _context_menu_hide_menu_item(context, 'liked.videos', label)
            directory.ListItem.addContextMenuItems(context_menus)
            items.append(tuple(directory))

        if show_main_menu_item('disliked.videos'):
            label = context.i18n('Disliked Videos')
            directory = Directory(
                label=label,
                path=create_addon_path(parameters={
                    'mode': str(MODES.DISLIKED_VIDEOS)
                })
            )
            directory.ListItem.setArt({
                'icon': 'DefaultTVShows.png',
                'thumb': 'DefaultTVShows.png',
                'fanart': fanart,
            })
            context_menus = _context_menu_hide_menu_item(context, 'disliked.videos', label)
            directory.ListItem.addContextMenuItems(context_menus)
            items.append(tuple(directory))

        if show_main_menu_item('history'):
            users = UserStorage()
            if users.history_playlist:
                label = context.i18n('History')
                directory = Directory(
                    label=label,
                    path=create_addon_path(parameters={
                        'mode': str(MODES.PLAYLIST),
                        'playlist_id': users.history_playlist
                    })
                )
                directory.ListItem.setArt({
                    'icon': 'DefaultVideoPlaylists.png',
                    'thumb': 'DefaultVideoPlaylists.png',
                    'fanart': fanart,
                })
                context_menus = _context_menu_hide_menu_item(context, 'history', label)
                directory.ListItem.addContextMenuItems(context_menus)
                items.append(tuple(directory))

        if show_main_menu_item('watch.later'):
            if not users:
                users = UserStorage()

            if users.watchlater_playlist:
                label = context.i18n('Watch Later')
                directory = Directory(
                    label=label,
                    path=create_addon_path(parameters={
                        'mode': str(MODES.PLAYLIST),
                        'playlist_id': users.watchlater_playlist
                    })
                )
                directory.ListItem.setArt({
                    'icon': 'DefaultVideoPlaylists.png',
                    'thumb': 'DefaultVideoPlaylists.png',
                    'fanart': fanart,
                })
                context_menus = _context_menu_hide_menu_item(context, 'watch.later', label)
                directory.ListItem.addContextMenuItems(context_menus)
                items.append(tuple(directory))

        if show_main_menu_item('playlists') and has_channel_mine:
            label = context.i18n('Playlists')
            directory = Directory(
                label=label,
                path=create_addon_path(parameters={
                    'mode': str(MODES.PLAYLISTS),
                    'channel_id': 'mine'
                })
            )
            directory.ListItem.setArt({
                'icon': 'DefaultVideoPlaylists.png',
                'thumb': 'DefaultVideoPlaylists.png',
                'fanart': fanart,
            })
            context_menus = _context_menu_hide_menu_item(context, 'playlists', label)
            directory.ListItem.addContextMenuItems(context_menus)
            items.append(tuple(directory))

        if show_main_menu_item('subscriptions'):
            label = context.i18n('Subscriptions')
            directory = Directory(
                label=label,
                path=create_addon_path(parameters={
                    'mode': str(MODES.SUBSCRIPTIONS)
                })
            )
            directory.ListItem.setArt({
                'icon': 'DefaultStudios.png',
                'thumb': 'DefaultStudios.png',
                'fanart': fanart,
            })
            context_menus = _context_menu_hide_menu_item(context, 'subscriptions', label)
            directory.ListItem.addContextMenuItems(context_menus)
            items.append(tuple(directory))

    if context.settings.favorite_channel_maximum > 0 and show_main_menu_item('favorite.channels'):
        label = context.i18n('Favorite Channels')
        directory = Directory(
            label=label,
            path=create_addon_path(parameters={
                'mode': str(MODES.FAVORITE_CHANNELS)
            })
        )
        directory.ListItem.setArt({
            'icon': 'DefaultStudios.png',
            'thumb': 'DefaultStudios.png',
            'fanart': fanart,
        })
        context_menus = [
            (context.i18n('Import from xml'),
             'RunScript(%s,mode=%s&action=import)' %
             (ADDON_ID, str(SCRIPT_MODES.FAVORITE_CHANNELS))),
        ]
        context_menus += _context_menu_hide_menu_item(context, 'favorite.channels', label)
        directory.ListItem.addContextMenuItems(context_menus)
        items.append(tuple(directory))

    if context.settings.favorite_playlist_maximum > 0 and show_main_menu_item('favorite.playlists'):
        label = context.i18n('Favorite Playlists')
        directory = Directory(
            label=label,
            path=create_addon_path(parameters={
                'mode': str(MODES.FAVORITE_PLAYLISTS)
            })
        )
        directory.ListItem.setArt({
            'icon': 'DefaultVideoPlaylists.png',
            'thumb': 'DefaultVideoPlaylists.png',
            'fanart': fanart,
        })
        context_menus = _context_menu_hide_menu_item(context, 'favorite.playlists', label)
        directory.ListItem.addContextMenuItems(context_menus)
        items.append(tuple(directory))

    if show_main_menu_item('live'):
        label = context.i18n('Live')
        directory = Directory(
            label=label,
            path=create_addon_path(parameters={
                'mode': str(MODES.LIVE)
            })
        )
        directory.ListItem.setArt({
            'icon': 'DefaultMovies.png',
            'thumb': 'DefaultMovies.png',
            'fanart': fanart,
        })
        context_menus = _context_menu_hide_menu_item(context, 'live', label)
        directory.ListItem.addContextMenuItems(context_menus)
        items.append(tuple(directory))

    if show_main_menu_item('search'):
        label = context.i18n('Search')
        directory = Directory(
            label=label,
            path=create_addon_path(parameters={
                'mode': str(MODES.SEARCH)
            })
        )
        directory.ListItem.setArt({
            'icon': 'DefaultAddonsSearch.png',
            'thumb': 'DefaultAddonsSearch.png',
            'fanart': fanart,
        })
        context_menus = _context_menu_hide_menu_item(context, 'search', label)
        directory.ListItem.addContextMenuItems(context_menus)
        items.append(tuple(directory))

    if logged_in:
        if show_main_menu_item('sign.out'):
            label = context.i18n('Sign Out')
            action = Action(
                label=label,
                path=create_addon_path(parameters={
                    'mode': str(MODES.SIGN_OUT)
                })
            )
            action.ListItem.setArt({
                'icon': 'OverlayLocked.png',
                'thumb': 'OverlayLocked.png',
                'fanart': fanart,
            })
            context_menus = _context_menu_hide_menu_item(context, 'sign.out', label)
            action.ListItem.addContextMenuItems(context_menus)
            items.append(tuple(action))

    if show_main_menu_item('manage.users'):
        if not users:
            users = UserStorage()

        label = context.i18n('Manage Users')
        action = Action(
            label=label,
            path=create_addon_path(parameters={
                'mode': str(MODES.MANAGE_USERS)
            })
        )
        action.ListItem.setArt({
            'icon': users.avatar or 'DefaultUser.png',
            'thumb': users.avatar or 'DefaultUser.png',
            'fanart': fanart,
        })
        context_menus = _context_menu_hide_menu_item(context, 'manage.users', label)
        action.ListItem.addContextMenuItems(context_menus)
        items.append(tuple(action))

    if show_main_menu_item('open.settings'):
        label = context.i18n('Settings')
        action = Action(
            label=label,
            path=create_addon_path(parameters={
                'mode': str(MODES.SETTINGS)
            })
        )
        action.ListItem.setArt({
            'icon': 'DefaultIconInfo.png',
            'thumb': 'DefaultIconInfo.png',
            'fanart': fanart,
        })
        context_menus = _context_menu_hide_menu_item(context, 'open.settings', label)
        action.ListItem.addContextMenuItems(context_menus)
        items.append(tuple(action))

    xbmcplugin.addDirectoryItems(context.handle, items, len(items))

    xbmcplugin.endOfDirectory(context.handle, True)


def _context_menu_hide_menu_item(context, setting_id, label):
    return [
        (context.i18n('Hide %s') % bold(label),
         'RunScript(%s,mode=%s&setting_id=%s&menu_title=%s)' %
         (ADDON_ID, str(SCRIPT_MODES.HIDE_MENU), setting_id, quote(label))),
    ]
