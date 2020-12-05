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
from ..items.directory import Directory
from ..lib.url_utils import create_addon_path


def invoke(context):
    payload = context.api.regions()

    regions = [(item['snippet']['name'], item['snippet']['gl'])
               for item in payload.get('items', [])]

    if not regions:
        xbmcplugin.endOfDirectory(context.handle, False)
        return

    regions = sorted(regions, key=lambda region: region[0])

    items = []
    for region_label, region_code in regions:
        directory = Directory(
            label=region_label,
            path=create_addon_path(parameters={
                'mode': str(MODES.MOST_POPULAR),
                'region_code': region_code
            })
        )
        directory.ListItem.setArt({
            'icon': 'DefaultCountry.png',
            'thumb': 'DefaultCountry.png'
        })
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
