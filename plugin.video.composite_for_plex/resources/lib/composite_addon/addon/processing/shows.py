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
from ..items.show import create_show_item
from ..utils import get_xml


def process_shows(context, url, tree=None):
    xbmcplugin.setContent(get_handle(), 'tvshows')

    xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE_IGNORE_THE)
    xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_VIDEO_RATING)
    xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_MPAA_RATING)

    # Get the URL and server name.  Get the XML and parse
    tree = get_xml(context, url, tree)
    if tree is None:
        return

    server = context.plex_network.get_server_from_url(url)

    items = []
    append_item = items.append
    # For each directory tag we find
    if PY3:
        shows = tree.iter('Directory')
    else:
        shows = tree.getiterator('Directory')

    for show in shows:
        item = Item(server, url, tree, show)
        append_item(create_show_item(context, item))

    if items:
        xbmcplugin.addDirectoryItems(get_handle(), items, len(items))

    xbmcplugin.endOfDirectory(get_handle(), cacheToDisc=context.settings.cache_directory())
