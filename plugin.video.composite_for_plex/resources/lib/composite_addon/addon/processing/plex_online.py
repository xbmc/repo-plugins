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
from ..items.plex_online import create_plex_online_item
from ..utils import get_xml


def process_plex_online(context, url):
    xbmcplugin.setContent(get_handle(), 'files')

    server = context.plex_network.get_server_from_url(url)

    tree = get_xml(context, url)
    if tree is None:
        return

    items = []
    append_item = items.append
    if PY3:
        plugins = tree.iter()
    else:
        plugins = tree.getiterator()

    for plugin in plugins:
        item = Item(server, url, tree, plugin)
        item = create_plex_online_item(context, item)
        if item:
            append_item(item)

    if items:
        xbmcplugin.addDirectoryItems(get_handle(), items, len(items))

    xbmcplugin.endOfDirectory(get_handle(), cacheToDisc=context.settings.cache_directory())
