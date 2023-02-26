# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import xbmcgui  # pylint: disable=import-error
import xbmcplugin  # pylint: disable=import-error

from ..constants import MODES
from ..generators.video import video_generator
from ..items.next_page import NextPage
from ..lib.sorting import set_video_sort_methods
from ..lib.url_utils import create_addon_path
from ..storage.users import UserStorage

users = UserStorage()
WATCH_LATER_PLAYLIST = users.watchlater_playlist
HISTORY_PLAYLIST = users.history_playlist
del users


def invoke(context, playlist_id, page_token='', mine=False):
    xbmcplugin.setContent(context.handle, 'videos')

    if not mine and playlist_id in [WATCH_LATER_PLAYLIST, HISTORY_PLAYLIST]:
        mine = True

    payload = context.api.playlist_items(
        playlist_id,
        page_token=page_token,
        fields='items(kind,id,snippet(playlistId,resourceId/videoId))'
    )
    items = list(video_generator(context, payload.get('items', []), mine=mine))

    page_token = payload.get('nextPageToken')
    if page_token:
        directory = NextPage(
            label=context.i18n('Next Page'),
            path=create_addon_path({
                'mode': str(MODES.PLAYLIST),
                'playlist_id': playlist_id,
                'page_token': page_token
            })
        )
        items.append(tuple(directory))

    if items:
        xbmcplugin.addDirectoryItems(context.handle, items, len(items))

        set_video_sort_methods(context)

        xbmcplugin.endOfDirectory(context.handle, True)

    else:
        xbmcgui.Dialog().notification(context.addon.getAddonInfo('name'),
                                      context.i18n('No entries found'),
                                      context.addon.getAddonInfo('icon'),
                                      sound=False)
        xbmcplugin.endOfDirectory(context.handle, False)
