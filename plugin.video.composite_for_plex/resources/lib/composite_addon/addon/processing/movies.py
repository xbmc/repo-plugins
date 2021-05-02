# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import time

from kodi_six import xbmcplugin  # pylint: disable=import-error

from ..common import get_handle
from ..containers import Item
from ..items.movie import create_movie_item
from ..items.photo import create_photo_item
from ..items.track import create_track_item
from ..logger import Logger
from ..utils import get_xml

LOG = Logger()


def process_movies(context, url, tree=None):
    xbmcplugin.setContent(get_handle(), 'movies')

    xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE_IGNORE_THE)
    xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_DATEADDED)
    xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_VIDEO_RATING)
    xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
    xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_MPAA_RATING)

    # get the server name from the URL, which was passed via the on screen listing..

    server = context.plex_network.get_server_from_url(url)

    tree = get_xml(context, url, tree)
    if tree is None:
        return

    # Find all the video tags, as they contain the data we need to link to a file.
    start_time = time.time()
    items = []
    append_item = items.append
    branches = tree.getiterator()
    for branch in branches:
        item = Item(server, url, tree, branch)
        if branch.tag.lower() == 'video':
            append_item(create_movie_item(context, item))
        elif branch.tag.lower() == 'track':  # mixed content video playlist
            append_item(create_track_item(context, item))
        elif branch.tag.lower() == 'photo':  # mixed content video playlist
            append_item(create_photo_item(context, item))

    if items:
        xbmcplugin.addDirectoryItems(get_handle(), items, len(items))
    LOG.debug('PROCESS: It took %s seconds to process %s items' %
              (time.time() - start_time, len(items)))

    xbmcplugin.endOfDirectory(get_handle(), cacheToDisc=context.settings.cache_directory())
