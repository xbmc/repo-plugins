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

from infotagger.listitem import ListItemInfoTag  # pylint: disable=import-error

from ..constants import ADDON_ID
from ..constants import MODES
from ..constants import SCRIPT_MODES
from ..items.directory import Directory
from ..lib.url_utils import create_addon_path
from .data_cache import get_cached
from .utils import get_fanart
from .utils import get_thumbnail


def channel_generator(context, items):
    logged_in = context.api.logged_in

    cached_channels = get_cached(
        context,
        context.api.channels,
        [get_id(item) for item in items if get_id(item)],
        cache_ttl=context.settings.data_cache_ttl
    )

    for item in items:
        channel_id = get_id(item)

        if not channel_id:
            continue

        channel = cached_channels.get(channel_id, {})

        snippet = channel.get('snippet', {})
        if not snippet:
            continue

        channel_name = unescape(snippet.get('title', ''))

        payload = Directory(
            label=channel_name,
            path=create_addon_path({
                'mode': str(MODES.CHANNEL),
                'channel_id': channel_id
            })
        )

        info_labels = {
            'plot': unescape(snippet.get('description', '')),
            'plotoutline': unescape(snippet.get('description', '')),
            'originaltitle': channel_name,
            'sorttitle': channel_name,
            'studio': channel_name
        }

        info_tag = ListItemInfoTag(payload.ListItem, 'video')
        info_tag.set_info(info_labels)

        thumbnail = get_thumbnail(snippet)

        payload.ListItem.setArt({
            'icon': thumbnail,
            'thumb': thumbnail,
            'fanart': get_fanart(channel.get('brandingSettings', {})),
        })

        context_menus = []
        if item.get('kind', '') == 'youtube#searchResult':
            query = deepcopy(context.query)
            query['order'] = 'prompt'
            context_menus += [
                (context.i18n('Sort order'),
                 'Container.Update(%s)' % create_addon_path(query))
            ]

        if logged_in:
            context_menus += [
                (context.i18n('Subscribe'),
                 'RunScript(%s,mode=%s&action=add&channel_id=%s&channel_name=%s)' %
                 (ADDON_ID, str(SCRIPT_MODES.SUBSCRIPTIONS), channel_id, quote(channel_name))),
            ]

        if context.settings.favorite_channel_maximum > 0:
            context_menus += [
                (context.i18n('Add to favorite channels'),
                 'RunScript(%s,mode=%s&action=add&channel_id=%s&channel_name=%s)' %
                 (ADDON_ID, str(SCRIPT_MODES.FAVORITE_CHANNELS), channel_id, quote(channel_name))),
            ]

        context_menus += [
            (context.i18n('Refresh'), 'RunScript(%s,mode=%s)' %
             (ADDON_ID, str(SCRIPT_MODES.REFRESH))),
        ]

        payload.ListItem.addContextMenuItems(context_menus)
        yield tuple(payload)


def get_id(item):
    kind = item.get('kind', '')
    if kind == 'youtube#channel':
        return item.get('id', '')

    if kind == 'youtube#searchResult':
        return item.get('id', {}).get('channelId')

    return ''
