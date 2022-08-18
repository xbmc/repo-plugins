# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

from urllib.parse import quote

import xbmc  # pylint: disable=import-error
import xbmcgui  # pylint: disable=import-error
import xbmcplugin  # pylint: disable=import-error

from ..constants import MODES
from ..generators.channel import channel_generator
from ..generators.playlist import playlist_generator
from ..generators.video import video_generator
from ..items.next_page import NextPage
from ..items.search_query import SearchQuery
from ..lib.sorting import set_video_sort_methods
from ..lib.txt_fmt import bold
from ..lib.url_utils import create_addon_path
from ..lib.url_utils import unquote
from ..storage.search_cache import SearchCache
from ..storage.search_history import SearchHistory
from ..storage.users import UserStorage
from .utils import get_sort_order

DEFAULT_ORDER = 'relevance'


def invoke(context, query='', page_token='', search_type='video',  # pylint: disable=too-many-branches
           order=DEFAULT_ORDER, channel_id=None):
    if search_type not in ['video', 'channel', 'playlist']:
        return

    uuid = UserStorage().uuid
    search_cache = SearchCache(uuid)
    search_history = SearchHistory(uuid, context.settings.search_history_maximum)

    if order == 'prompt':
        order = get_sort_order(context)
        order = order or DEFAULT_ORDER
        if order != DEFAULT_ORDER:
            page_token = ''

    if (not query and
            'mode=%s' % str(MODES.SEARCH_QUERY) in xbmc.getInfoLabel('Container.FolderPath')):
        query = search_cache.item

    if query and '%' in query:
        query = unquote(query)

    if not query:
        keyboard = xbmc.Keyboard()
        keyboard.setHeading(context.i18n('Enter your search term'))
        keyboard.doModal()
        if keyboard.isConfirmed():
            query = keyboard.getText()
            query = query.strip()

    if not query:
        xbmcplugin.endOfDirectory(context.handle, False)
        return

    items = []
    quoted_query = quote(query)

    if not page_token and search_type == 'video' and not channel_id:

        directory = SearchQuery(
            label=bold(context.i18n('Channels')),
            path=create_addon_path(parameters={
                'mode': str(MODES.SEARCH_QUERY),
                'query': quoted_query,
                'search_type': 'channel'
            })
        )

        items.append(tuple(directory))

        directory = SearchQuery(
            label=bold(context.i18n('Playlists')),
            path=create_addon_path(parameters={
                'mode': str(MODES.SEARCH_QUERY),
                'query': quoted_query,
                'search_type': 'playlist'
            })
        )

        items.append(tuple(directory))

    addon_query = {
        'mode': str(MODES.SEARCH_QUERY),
        'query': quoted_query,
        'search_type': search_type
    }

    payload = {}
    request_arguments = {
        'query': query,
        'page_token': page_token,
        'search_type': search_type
    }

    if search_type == 'video':
        xbmcplugin.setContent(context.handle, 'videos')
        request_arguments['fields'] = 'items(kind,id(videoId))'

        if channel_id:
            request_arguments['channel_id'] = channel_id

        payload = context.api.search(**request_arguments)

        items += list(video_generator(context, payload.get('items', [])))
        del addon_query['search_type']

    elif search_type == 'channel':
        request_arguments['fields'] = 'items(kind,id(channelId))'
        payload = context.api.search(**request_arguments)

        items += list(channel_generator(context, payload.get('items', [])))

    elif search_type == 'playlist':
        request_arguments['fields'] = 'items(kind,id(playlistId),snippet(title))'
        payload = context.api.search(**request_arguments)

        items += list(playlist_generator(context, payload.get('items', [])))

    if not payload:
        return

    page_token = payload.get('nextPageToken')
    if page_token:
        if order != DEFAULT_ORDER:
            addon_query['order'] = order

        addon_query['page_token'] = page_token

        directory = NextPage(
            label=context.i18n('Next Page'),
            path=create_addon_path(addon_query)
        )
        items.append(tuple(directory))

    if not items:
        xbmcplugin.endOfDirectory(context.handle, False)
        return

    search_cache.item = quoted_query

    if not channel_id:
        search_history.update(query)

    if items:
        xbmcplugin.addDirectoryItems(context.handle, items, len(items))

        if search_type == 'video':
            set_video_sort_methods(context)

        xbmcplugin.endOfDirectory(context.handle, True)

    else:
        xbmcgui.Dialog().notification(context.addon.getAddonInfo('name'),
                                      context.i18n('No entries found'),
                                      context.addon.getAddonInfo('icon'),
                                      sound=False)
        xbmcplugin.endOfDirectory(context.handle, False)
