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
from ..items.artist import create_artist_item
from ..utils import get_xml


def process_artists(context, url, tree=None):
    """
        Process artist XML and display data
        @input: url of XML page, or existing tree of XML page
        @return: nothing
    """
    xbmcplugin.setContent(get_handle(), 'artists')

    xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_ARTIST_IGNORE_THE)
    xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_LASTPLAYED)
    xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_VIDEO_YEAR)

    # Get the URL and server name.  Get the XML and parse
    tree = get_xml(context, url, tree)
    if tree is None:
        return

    server = context.plex_network.get_server_from_url(url)

    items = []
    append_item = items.append
    if PY3:
        artists = tree.iter('Directory')
    else:
        artists = tree.getiterator('Directory')

    for artist in artists:
        item = Item(server, url, tree, artist)
        append_item(create_artist_item(context, item))

    if items:
        xbmcplugin.addDirectoryItems(get_handle(), items, len(items))

    xbmcplugin.endOfDirectory(get_handle(), cacheToDisc=context.settings.cache_directory())
