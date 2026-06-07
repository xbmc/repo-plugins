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
from ..items.plex_plugin import create_plex_plugin_item
from ..logger import Logger
from ..utils import get_master_server
from ..utils import get_xml

LOG = Logger()


def process_plex_plugins(context, url, tree=None):
    """
        Main function to parse plugin XML from PMS
        Will create dir or item links depending on what the
        main tag is.
        @input: plugin page URL
        @return: nothing, creates Kodi GUI listing
    """
    xbmcplugin.setContent(get_handle(), 'files')

    server = context.plex_network.get_server_from_url(url)
    tree = get_xml(context, url, tree)
    if tree is None:
        return

    if (tree.get('identifier') != 'com.plexapp.plugins.myplex') and ('node.plexapp.com' in url):
        LOG.debug('This is a myPlex URL, attempting to locate master server')
        server = get_master_server(context)

    items = []
    append_item = items.append
    if PY3:
        plugins = tree.iter()
    else:
        plugins = tree.getiterator()

    for plugin in plugins:
        item = Item(server, tree, url, plugin)
        item = create_plex_plugin_item(context, item)
        if item:
            append_item(item)

    if items:
        xbmcplugin.addDirectoryItems(get_handle(), items, len(items))

    xbmcplugin.endOfDirectory(get_handle(), cacheToDisc=context.settings.cache_directory())
