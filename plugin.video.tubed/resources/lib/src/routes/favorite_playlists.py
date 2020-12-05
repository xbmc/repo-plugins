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
from ..generators.favorite_playlists import favorite_playlists_generator
from ..items.next_page import NextPage
from ..lib.url_utils import create_addon_path
from ..storage.favorite_playlists import FavoritePlaylists
from ..storage.users import UserStorage


def invoke(context, page=1):
    try:
        page = int(page)
    except ValueError:
        page = 1

    if page < 1:
        return

    max_playlists = 50

    favorite_playlists = FavoritePlaylists(UserStorage().uuid,
                                           context.settings.favorite_playlist_maximum)

    playlists = favorite_playlists.list((page - 1) * max_playlists, max_playlists)
    playlist_ids = [channel_id for channel_id, _ in playlists]

    items = list(favorite_playlists_generator(context, playlist_ids))

    if favorite_playlists.list(page * max_playlists, 1):
        directory = NextPage(
            label=context.i18n('Next Page'),
            path=create_addon_path({
                'mode': str(MODES.FAVORITE_PLAYLISTS),
                'page': page + 1
            })
        )
        items.append(tuple(directory))

    if items:
        xbmcplugin.addDirectoryItems(context.handle, items, len(items))

        xbmcplugin.endOfDirectory(context.handle, True)

    else:
        xbmcgui.Dialog().notification(context.addon.getAddonInfo('name'),
                                      context.i18n('No entries found'),
                                      context.addon.getAddonInfo('icon'),
                                      sound=False)
        xbmcplugin.endOfDirectory(context.handle, False)
