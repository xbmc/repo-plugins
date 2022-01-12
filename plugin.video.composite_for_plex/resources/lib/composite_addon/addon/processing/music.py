# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from kodi_six import xbmcplugin  # pylint: disable=import-error
from six import PY3

from ..common import get_handle
from ..containers import Item
from ..items.music import create_music_item
from ..utils import get_xml


def process_music(context, url, tree=None):
    server = context.plex_network.get_server_from_url(url)

    tree = get_xml(context, url, tree)
    if tree is None:
        return

    items = []
    append_item = items.append
    if PY3:
        branches = tree.iter()
    else:
        branches = tree.getiterator()

    for music in branches:

        if music.get('key') is None:
            continue

        item = Item(server, url, tree, music)
        append_item(create_music_item(context, item))

    if items:
        content_type = items[-1][1].getProperty('content_type')
        if not content_type:
            content_type = 'artists'
        xbmcplugin.setContent(get_handle(), content_type)

        xbmcplugin.addDirectoryItems(get_handle(), items, len(items))

    xbmcplugin.endOfDirectory(get_handle(), cacheToDisc=context.settings.cache_directory())
