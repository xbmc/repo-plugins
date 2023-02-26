# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

from html import unescape

from infotagger.listitem import ListItemInfoTag  # pylint: disable=import-error

from ..constants import MODES
from ..items.directory import Directory
from ..lib.url_utils import create_addon_path


def category_generator(items):
    for item in items:
        kind = item.get('kind', '')
        snippet = item.get('snippet', {})
        category_id = item.get('id', '')

        if not kind or kind != 'youtube#videoCategory':
            continue

        if not snippet:
            continue

        if not category_id:
            continue

        if not snippet.get('assignable'):
            continue

        payload = Directory(
            label=unescape(snippet.get('title', '')),
            path=create_addon_path({
                'mode': str(MODES.CATEGORY),
                'category_id': category_id
            })
        )

        info_labels = {
            'originaltitle': unescape(snippet.get('title', '')),
            'sorttitle': unescape(snippet.get('title', '')),
        }

        info_tag = ListItemInfoTag(payload.ListItem, 'video')
        info_tag.set_info(info_labels)

        payload.ListItem.setArt({
            'icon': 'DefaultGenre.png',
            'thumb': 'DefaultGenre.png',
        })

        yield tuple(payload)
