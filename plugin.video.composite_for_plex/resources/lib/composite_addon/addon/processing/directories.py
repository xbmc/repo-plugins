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
from ..items.directory import create_directory_item
from ..logger import Logger

LOG = Logger()


def process_directories(context, url, tree=None):
    LOG.debug('Processing secondary menus')

    content_type = 'files'
    if '/collection' in url:
        content_type = 'sets'

    xbmcplugin.setContent(get_handle(), content_type)

    server = context.plex_network.get_server_from_url(url)

    items = []
    append_item = items.append
    if PY3:
        directories = tree.iter('Directory')
    else:
        directories = tree.getiterator('Directory')

    for directory in directories:
        item = Item(server, url, tree, directory)
        append_item(create_directory_item(context, item))

    if items:
        xbmcplugin.addDirectoryItems(get_handle(), items, len(items))

    xbmcplugin.endOfDirectory(get_handle(), cacheToDisc=context.settings.cache_directory())
