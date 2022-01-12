# -*- coding: utf-8 -*-
"""

    Copyright (C) 2019-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from kodi_six import xbmcplugin  # pylint: disable=import-error
from six import PY3

from ..addon.common import get_handle
from ..addon.containers import Item
from ..addon.items.episode import create_episode_item
from ..addon.items.movie import create_movie_item
from ..addon.logger import Logger
from ..plex import plex

LOG = Logger()


def run(context):
    context.plex_network = plex.Plex(context.settings, load=True)
    content_type = context.params.get('content_type')
    server_list = context.plex_network.get_server_list()

    items = []
    LOG.debug('Using list of %s servers: %s' % (len(server_list), server_list))
    for server in server_list:
        sections = server.get_sections()
        for section in sections:
            if section.content_type() == content_type:
                items += _list_content(context, server, int(section.get_key()))

    if items:
        xbmcplugin.setContent(get_handle(), content_type)
        xbmcplugin.addDirectoryItems(get_handle(), items, len(items))

    xbmcplugin.endOfDirectory(get_handle(), cacheToDisc=False)


def _list_content(context, server, section):
    _size = context.settings.recently_added_item_count()
    _hide_watched = not context.settings.recently_added_include_watched()

    tree = server.get_recently_added(section=section, size=_size, hide_watched=_hide_watched)
    if tree is None:
        return []

    if PY3:
        branches = tree.iter('Video')
    else:
        branches = tree.getiterator('Video')

    if not branches:
        return []

    items = []
    append_item = items.append

    for content in branches:
        item = Item(server, server.get_url_location(), tree, content)
        if content.get('type') == 'episode':
            append_item(create_episode_item(context, item))
        elif content.get('type') == 'movie':
            append_item(create_movie_item(context, item))

    return items
