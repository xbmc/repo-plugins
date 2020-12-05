# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import arrow
import xbmcgui  # pylint: disable=import-error
import xbmcplugin  # pylint: disable=import-error

from ..constants import MODES
from ..generators.video import video_generator
from ..items.directory import Directory
from ..items.next_page import NextPage
from ..lib.sorting import set_video_sort_methods
from ..lib.txt_fmt import bold
from ..lib.url_utils import create_addon_path
from .utils import get_sort_order

DEFAULT_ORDER = 'relevance'


def invoke(context, page_token='', event_type='live', order=DEFAULT_ORDER):
    event_type = event_type.lower()
    if event_type not in ['live', 'completed', 'upcoming']:
        return

    if order == 'prompt':
        order = get_sort_order(context)
        order = order or DEFAULT_ORDER
        if order != DEFAULT_ORDER:
            page_token = ''

    if event_type != 'upcoming':
        xbmcplugin.setContent(context.handle, 'videos')

    items = []

    if not page_token and event_type == 'live':

        directory = Directory(
            label=bold(context.i18n('Upcoming')),
            path=create_addon_path(parameters={
                'mode': str(MODES.LIVE),
                'event_type': 'upcoming'
            })
        )

        items.append(tuple(directory))

        directory = Directory(
            label=bold(context.i18n('Completed')),
            path=create_addon_path(parameters={
                'mode': str(MODES.LIVE),
                'event_type': 'completed'
            })
        )

        items.append(tuple(directory))

    api_arguments = {
        'event_type': event_type,
        'order': order,
        'page_token': page_token,
        'fields': 'items(kind,id(videoId))',
    }
    if event_type == 'upcoming':
        published_after = arrow.utcnow()
        published_after = published_after.shift(months=-6)
        api_arguments['published_after'] = published_after

    payload = context.api.live_events(**api_arguments)
    items += list(video_generator(context, payload.get('items', [])))

    page_token = payload.get('nextPageToken')
    if page_token:
        query = {
            'mode': str(MODES.LIVE),
            'page_token': page_token,
            'event_type': event_type
        }
        if order != DEFAULT_ORDER:
            query['order'] = order

        directory = NextPage(
            label=context.i18n('Next Page'),
            path=create_addon_path(query)
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
