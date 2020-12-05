# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

from copy import deepcopy
from html import unescape
from urllib.parse import quote

from ..constants import ADDON_ID
from ..constants import MODES
from ..constants import SCRIPT_MODES
from ..items.directory import Directory
from ..lib.txt_fmt import bold
from ..lib.url_utils import create_addon_path
from ..storage.users import UserStorage
from .data_cache import get_cached
from .data_cache import get_fanart
from .utils import get_thumbnail

users = UserStorage()
HISTORY_PLAYLIST = users.history_playlist
WATCHLATER_PLAYLIST = users.watchlater_playlist
del users


def playlist_generator(context, items):
    cached_playlists = get_cached(
        context,
        context.api.playlists,
        [get_id(item) for item in items if get_id(item)],
        cache_ttl=context.settings.data_cache_ttl
    )

    fanart = get_fanart(
        context,
        context.api.channels,
        [item.get('snippet', {}).get('channelId')
         for _, item in cached_playlists.items() if item.get('snippet', {}).get('channelId')],
        cache_ttl=context.settings.data_cache_ttl
    )

    is_mine = context.query.get('channel_id', '') == 'mine'

    for item in items:
        playlist_id = get_id(item)

        if not playlist_id:
            continue

        playlist = cached_playlists.get(playlist_id, {})

        snippet = playlist.get('snippet', {})
        if not snippet:
            continue

        channel_id = snippet.get('channelId', '')
        channel_name = unescape(snippet.get('channelTitle', ''))

        playlist_title = unescape(item.get('snippet', snippet).get('title', ''))

        payload = Directory(
            label=playlist_title,
            label2=channel_name,
            path=create_addon_path({
                'mode': str(MODES.PLAYLIST),
                'playlist_id': playlist_id,
                'mine': str(is_mine).lower()
            })
        )

        info_labels = {
            'plot': unescape(snippet.get('description', '')),
            'plotoutline': unescape(snippet.get('description', '')),
            'originaltitle': playlist_title,
            'sorttitle': playlist_title,
            'studio': channel_name
        }
        payload.ListItem.setInfo('video', info_labels)

        thumbnail = get_thumbnail(snippet)

        payload.ListItem.setArt({
            'icon': thumbnail,
            'thumb': thumbnail,
            'fanart': fanart.get(channel_id, ''),
        })

        context_menus = get_context_menus(context, item, snippet, channel_id,
                                          channel_name, playlist_id, playlist_title)
        payload.ListItem.addContextMenuItems(context_menus)

        yield tuple(payload)


def get_id(item):
    kind = item.get('kind', '')
    if kind == 'youtube#playlist':
        return item.get('id', '')

    if kind == 'youtube#searchResult':
        return item.get('id', {}).get('playlistId', '')

    return ''


def get_context_menus(context, item, snippet, channel_id,
                      channel_name, playlist_id, playlist_title):
    logged_in = context.api.logged_in
    is_mine = context.query.get('channel_id', '') == 'mine'
    context_menus = []

    if item.get('kind', '') == 'youtube#searchResult':
        query = deepcopy(context.query)
        query['order'] = 'prompt'
        context_menus += [
            (context.i18n('Sort order'),
             'Container.Update(%s)' % create_addon_path(query))
        ]

    if not is_mine:
        if logged_in:
            context_menus += [
                (context.i18n('Subscribe'),
                 'RunScript(%s,mode=%s&action=add&channel_id=%s&channel_name=%s)' %
                 (ADDON_ID, str(SCRIPT_MODES.SUBSCRIPTIONS), channel_id, quote(channel_name))),
            ]

        if context.settings.favorite_channel_maximum > 0:
            context_menus += [
                (context.i18n('Add %s to favorite channels') % bold(channel_name),
                 'RunScript(%s,mode=%s&action=add&channel_id=%s&channel_name=%s)' %
                 (ADDON_ID, str(SCRIPT_MODES.FAVORITE_CHANNELS), channel_id, quote(channel_name))),
            ]

    if context.settings.favorite_playlist_maximum > 0:
        context_menus += [
            (context.i18n('Add %s to favorite playlists') % bold(playlist_title),
             'RunScript(%s,mode=%s&action=add&playlist_id=%s&playlist_name=%s)' %
             (ADDON_ID, str(SCRIPT_MODES.FAVORITE_PLAYLISTS),
              playlist_id, quote(playlist_title))),
        ]

    if not is_mine:
        context_menus += [
            (context.i18n('Go to %s') % bold(unescape(snippet.get('channelTitle', ''))),
             'Container.Update(plugin://%s/?mode=%s&channel_id=%s)' %
             (ADDON_ID, str(MODES.CHANNEL), channel_id))
        ]

    if is_mine and logged_in:
        context_menus += [
            (context.i18n('Rename playlist'),
             'RunScript(%s,mode=%s&action=rename&playlist_id=%s&playlist_title=%s)' %
             (ADDON_ID, str(SCRIPT_MODES.PLAYLIST), playlist_id, quote(playlist_title))),

            (context.i18n('Delete playlist'),
             'RunScript(%s,mode=%s&action=delete&playlist_id=%s&playlist_title=%s)' %
             (ADDON_ID, str(SCRIPT_MODES.PLAYLIST), playlist_id, quote(playlist_title)))
        ]

        if HISTORY_PLAYLIST and HISTORY_PLAYLIST == playlist_id:
            context_menus += [
                (context.i18n('Remove as History'),
                 'RunScript(%s,mode=%s&action=remove&playlist_type=history'
                 '&playlist_id=%s&playlist_title=%s)' %
                 (ADDON_ID, str(SCRIPT_MODES.CONFIGURE_PLAYLISTS),
                  playlist_id, quote(playlist_title)))
            ]

        elif WATCHLATER_PLAYLIST and WATCHLATER_PLAYLIST == playlist_id:
            context_menus += [
                (context.i18n('Remove as Watch Later'),
                 'RunScript(%s,mode=%s&action=remove&playlist_type=watchlater'
                 '&playlist_id=%s&playlist_title=%s)' %
                 (ADDON_ID, str(SCRIPT_MODES.CONFIGURE_PLAYLISTS),
                  playlist_id, quote(playlist_title)))
            ]

        elif playlist_id not in [WATCHLATER_PLAYLIST, HISTORY_PLAYLIST]:
            if not HISTORY_PLAYLIST:
                context_menus += [
                    (context.i18n('Set as History'),
                     'RunScript(%s,mode=%s&action=add&playlist_type=history'
                     '&playlist_id=%s&playlist_title=%s)' %
                     (ADDON_ID, str(SCRIPT_MODES.CONFIGURE_PLAYLISTS),
                      playlist_id, quote(playlist_title))),
                ]

            if not WATCHLATER_PLAYLIST:
                context_menus += [
                    (context.i18n('Set as Watch Later'),
                     'RunScript(%s,mode=%s&action=add&playlist_type=watchlater'
                     '&playlist_id=%s&playlist_title=%s)' %
                     (ADDON_ID, str(SCRIPT_MODES.CONFIGURE_PLAYLISTS),
                      playlist_id, quote(playlist_title)))
                ]

    context_menus += [
        (context.i18n('Refresh'), 'RunScript(%s,mode=%s)' % (ADDON_ID, str(SCRIPT_MODES.REFRESH))),

        (context.i18n('Play'),
         'RunScript(%s,mode=%s&playlist_id=%s)' %
         (ADDON_ID, str(SCRIPT_MODES.PLAY), playlist_id)),
    ]

    return context_menus
