# -*- coding: utf-8 -*-
"""

    Copyright (C) 2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import xml.etree.ElementTree as ETree

from kodi_six import xbmc  # pylint: disable=import-error
from kodi_six import xbmcplugin  # pylint: disable=import-error
from six.moves.urllib_parse import quote

from ..addon.common import get_handle
from ..addon.containers import Item
from ..addon.items.episode import create_episode_item
from ..addon.items.movie import create_movie_item
from ..addon.logger import Logger
from ..addon.strings import decode_utf8
from ..addon.strings import i18n
from ..plex import plex

LOG = Logger()


def run(context):
    context.plex_network = plex.Plex(context.settings, load=True)

    params = context.params
    for param in ['video_type']:  # check for expected parameters
        if param not in params:
            return

    if not params.get('query'):
        params['query'] = _get_search_query()
    params['query'] = _quote(params['query'])

    context.params = params

    succeeded = False
    search_results = search(context)
    log_results = list(map(lambda x: decode_utf8(ETree.tostring(x[1])), search_results))
    LOG.debug('Found search results: %s' % '\n\n'.join(log_results))

    if search_results:
        LOG.debug('Found a server with the requested content %s' % params['query'])

        items = []
        append_item = items.append
        url = ''

        for server_uuid, tree, search_result in search_results:
            server = context.plex_network.get_server_from_uuid(server_uuid)
            if context.params.get('video_type') == 'movie':
                item = Item(server, url, tree, search_result)
                append_item(create_movie_item(context, item))

            elif context.params.get('video_type') == 'episode':
                item = Item(server, url, tree, search_result)
                append_item(create_episode_item(context, item))

        if items:
            xbmcplugin.addDirectoryItems(get_handle(), items, len(items))
            succeeded = True
            if context.params.get('video_type') == 'movie':
                xbmcplugin.setContent(get_handle(), 'movies')
            elif context.params.get('video_type') == 'episode':
                xbmcplugin.setContent(get_handle(), 'episodes')
    else:
        LOG.debug('Content not found on any server')

    xbmcplugin.endOfDirectory(get_handle(), succeeded=succeeded,
                              cacheToDisc=context.settings.cache_directory())


def search(context):
    results = []

    content_type = _get_content_type(context.params.get('video_type'))
    search_type = _get_search_type(context.params.get('video_type'))
    if not content_type or not search_type:
        return []

    server_list = context.plex_network.get_server_list()
    params = context.params

    for server in server_list:
        processed_xml = server.processed_xml

        sections = server.get_sections()
        for section in sections:

            if section.get_type() == content_type:
                query = params.get('query')
                url = '%s/search?type=%s&query=%s' % (section.get_path(), search_type, query)
                processed = processed_xml(url)

                if _is_not_none(processed):
                    results += _get_search_results(server, processed)

    return results


def _get_search_query():
    text = ''
    keyboard = xbmc.Keyboard('', i18n('Search...'))
    keyboard.setHeading(i18n('Enter search term'))
    keyboard.doModal()
    if keyboard.isConfirmed():
        text = keyboard.getText()
        if not text.strip():
            return ''
    LOG.debug('Search term input: %s' % text)
    return text.strip()


def _quote(query):
    if ' ' in query:
        if '%20' in query:
            query = query.replace('%20', ' ')
        return quote(query)
    return query


def _is_not_none(item):
    if item is not None and item.get('size', '0') == '0':
        item = None
    return item is not None


def _get_content_type(video_type):
    content_type = None

    if video_type == 'movie':
        content_type = 'movie'
    elif video_type == 'episode':
        content_type = 'show'

    return content_type


def _get_search_type(video_type):
    search_type = None

    if video_type == 'movie':
        search_type = '1'
    elif video_type == 'episode':
        search_type = '4'

    return search_type


def _get_search_results(server, processed):
    server_uuid = server.get_uuid()

    results = []

    if _is_not_none(processed):
        results = list(map(lambda x: (server_uuid, processed, x), processed))

    return results
