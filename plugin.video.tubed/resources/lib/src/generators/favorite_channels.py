# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

from html import unescape

from infotagger.listitem import ListItemInfoTag  # pylint: disable=import-error

from ..constants import ADDON_ID
from ..constants import MODES
from ..constants import SCRIPT_MODES
from ..items.directory import Directory
from ..lib.url_utils import create_addon_path
from .data_cache import get_cached
from .utils import get_fanart
from .utils import get_thumbnail


def favorite_channels_generator(context, channel_ids):
    cached_channels = get_cached(
        context,
        context.api.channels,
        channel_ids,
        cache_ttl=context.settings.data_cache_ttl
    )

    for channel_id in channel_ids:

        channel = cached_channels.get(channel_id, {})

        snippet = channel.get('snippet', {})
        if not snippet:
            continue

        channel_name = unescape(snippet.get('title', ''))

        payload = Directory(
            label=unescape(snippet.get('title', '')),
            path=create_addon_path({
                'mode': str(MODES.PLAYLISTS),
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

        context_menus = [
            (context.i18n('Remove...'),
             'RunScript(%s,mode=%s&action=remove&channel_id=%s)' %
             (ADDON_ID, str(SCRIPT_MODES.FAVORITE_CHANNELS), channel_id)),

            (context.i18n('Clear favorite channels'),
             'RunScript(%s,mode=%s&action=clear)' %
             (ADDON_ID, str(SCRIPT_MODES.FAVORITE_CHANNELS))),

            (context.i18n('Refresh'), 'RunScript(%s,mode=%s)' %
             (ADDON_ID, str(SCRIPT_MODES.REFRESH))),
        ]

        payload.ListItem.addContextMenuItems(context_menus)
        yield tuple(payload)
