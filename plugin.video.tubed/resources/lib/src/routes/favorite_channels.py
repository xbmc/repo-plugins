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
from ..generators.favorite_channels import favorite_channels_generator
from ..items.next_page import NextPage
from ..lib.url_utils import create_addon_path
from ..storage.favorite_channels import FavoriteChannels
from ..storage.users import UserStorage


def invoke(context, page=1):
    try:
        page = int(page)
    except ValueError:
        page = 1

    if page < 1:
        return

    max_channels = 50

    favorite_channels = FavoriteChannels(UserStorage().uuid,
                                         context.settings.favorite_channel_maximum)

    channels = favorite_channels.list((page - 1) * max_channels, max_channels)
    channel_ids = [channel_id for channel_id, _ in channels]

    items = list(favorite_channels_generator(context, channel_ids))

    if favorite_channels.list(page * max_channels, 1):
        directory = NextPage(
            label=context.i18n('Next Page'),
            path=create_addon_path({
                'mode': str(MODES.FAVORITE_CHANNELS),
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
