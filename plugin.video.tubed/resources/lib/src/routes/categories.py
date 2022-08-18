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
from ..generators.category import category_generator
from ..items.next_page import NextPage
from ..lib.url_utils import create_addon_path


def invoke(context, page_token=''):
    payload = context.api.video_categories(page_token=page_token)
    items = list(category_generator(payload.get('items', [])))

    page_token = payload.get('nextPageToken')
    if page_token:
        directory = NextPage(
            label=context.i18n('Next Page'),
            path=create_addon_path({
                'mode': str(MODES.CATEGORIES),
                'page_token': page_token
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
