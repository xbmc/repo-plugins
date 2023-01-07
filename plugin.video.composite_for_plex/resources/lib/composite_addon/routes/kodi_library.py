# -*- coding: utf-8 -*-
"""

    Copyright (C) 2019-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from kodi_six import xbmcgui  # pylint: disable=import-error
from kodi_six import xbmcplugin  # pylint: disable=import-error
from six import PY3

from ..addon.common import get_handle
from ..addon.containers import Item
from ..addon.items.movie import create_movie_item
from ..addon.items.show import create_show_item
from ..addon.library_sections import LibrarySectionsStore
from ..addon.logger import Logger
from ..plex import plex

LOG = Logger()


def run(context):
    section_storage = LibrarySectionsStore()
    content_type = _get_content_type(context.params.get('path_mode'))
    kodi_action = context.params.get('kodi_action')

    if kodi_action == 'check_exists' and context.params.get('url'):
        exists = False
        context.plex_network = plex.Plex(context.settings, load=True)
        server = context.plex_network.get_server_from_url(context.params.get('url'))
        if server:
            tree = server.processed_xml(context.params.get('url'))
            exists = tree is not None and not tree.get('message') and tree.get('size', '0') != '0'
        LOG.debug('check_exists for %s -> %s' % (context.params.get('url'), exists))
        xbmcplugin.setResolvedUrl(get_handle(), exists, xbmcgui.ListItem())

    elif kodi_action == 'check_exists':
        exists = True
        LOG.debug('check_exists for %s -> %s' % (content_type, exists))
        xbmcplugin.setResolvedUrl(get_handle(), exists, xbmcgui.ListItem())

    elif kodi_action == 'refresh_info' and context.params.get('url'):
        LOG.debug('refresh info for %s' % context.params.get('url'))
        context.plex_network = plex.Plex(context.settings, load=True)
        server = context.plex_network.get_server_from_url(context.params.get('url'))
        _list_content(context, server, context.params.get('url'), content_type)
        xbmcplugin.endOfDirectory(get_handle(), cacheToDisc=False)

    else:
        context.plex_network = plex.Plex(context.settings, load=True)
        server_list = context.plex_network.get_server_list()
        LOG.debug('Using list of %s servers: %s' % (len(server_list), server_list))
        set_content = xbmcplugin.setContent
        for server in server_list:
            sections = server.get_sections()
            for section in sections:
                selected_sections = []
                if section.is_movie():
                    selected_sections = section_storage.get_movie_sections(server.get_uuid())

                elif section.is_show():
                    selected_sections = section_storage.get_tvshow_sections(server.get_uuid())

                if not selected_sections:
                    selected_sections = [] if section_storage.exists() else None

                if (selected_sections == [] or
                        (selected_sections and section.get_uuid() not in selected_sections)):
                    continue

                if section.get_type() in content_type:
                    if content_type in ['movies', 'tvshows']:
                        set_content(get_handle(), content_type)
                        _list_content(context, server,
                                      server.join_url(server.get_url_location(),
                                                      section.get_path(), 'all'),
                                      content_type)

        xbmcplugin.endOfDirectory(get_handle(), cacheToDisc=False)


def _get_content_type(path_mode):
    content_type = None
    if path_mode:
        if path_mode.endswith('movies'):
            content_type = 'movies'
        elif path_mode.endswith('tvshows'):
            content_type = 'tvshows'
    return content_type


def _list_content(context, server, url, content_type):
    tree = server.processed_xml(url)
    if tree is None:
        return

    items = []
    append_item = items.append
    content_iter = 'Video'

    if 'movies' in content_type:
        content_iter = 'Video'
    if 'tvshows' in content_type:
        content_iter = 'Directory'

    if PY3:
        branches = tree.iter(content_iter)
    else:
        branches = tree.getiterator(content_iter)

    for content in branches:
        item = Item(server, url, tree, content)
        if content.get('type') == 'show':
            append_item(create_show_item(context, item, library=True))
        elif content.get('type') == 'movie':
            append_item(create_movie_item(context, item, library=True))

    if items:
        xbmcplugin.addDirectoryItems(get_handle(), items, len(items))
