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


def favorite_playlists_generator(context, playlist_ids):
    cached_playlists = get_cached(
        context,
        context.api.playlists,
        playlist_ids,
        cache_ttl=context.settings.data_cache_ttl
    )

    for playlist_id in playlist_ids:

        playlist = cached_playlists.get(playlist_id, {})

        snippet = playlist.get('snippet', {})
        if not snippet:
            continue

        playlist_name = unescape(snippet.get('title', ''))

        payload = Directory(
            label=unescape(snippet.get('title', '')),
            path=create_addon_path({
                'mode': str(MODES.PLAYLIST),
                'playlist_id': playlist_id
            })
        )

        info_labels = {
            'plot': unescape(snippet.get('description', '')),
            'plotoutline': unescape(snippet.get('description', '')),
            'originaltitle': playlist_name,
            'sorttitle': playlist_name,
        }

        info_tag = ListItemInfoTag(payload.ListItem, 'video')
        info_tag.set_info(info_labels)

        thumbnail = get_thumbnail(snippet)

        payload.ListItem.setArt({
            'icon': thumbnail,
            'thumb': thumbnail,
            'fanart': get_fanart(playlist.get('brandingSettings', {})),
        })

        context_menus = [
            (context.i18n('Remove...'),
             'RunScript(%s,mode=%s&action=remove&playlist_id=%s)' %
             (ADDON_ID, str(SCRIPT_MODES.FAVORITE_PLAYLISTS), playlist_id)),

            (context.i18n('Clear favorite playlists'),
             'RunScript(%s,mode=%s&action=clear)' %
             (ADDON_ID, str(SCRIPT_MODES.FAVORITE_PLAYLISTS))),

            (context.i18n('Refresh'), 'RunScript(%s,mode=%s)' %
             (ADDON_ID, str(SCRIPT_MODES.REFRESH))),
        ]

        payload.ListItem.addContextMenuItems(context_menus)
        yield tuple(payload)
