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
from ..items.movie import create_movie_item
from ..items.photo import create_photo_item
from ..items.track import create_track_item
from ..utils import get_xml


def process_photos(context, url, tree=None):
    server = context.plex_network.get_server_from_url(url)

    tree = get_xml(context, url, tree)
    if tree is None:
        return

    content_counter = {
        'photo': 0,
        'track': 0,
        'video': 0,
    }
    items = []
    append_item = items.append

    if PY3:
        branches = tree.iter()
    else:
        branches = tree.getiterator()

    for branch in branches:
        item = Item(server, url, tree, branch)
        tag = branch.tag.lower()
        if tag == 'photo':
            append_item(create_photo_item(context, item))
        elif tag == 'directory':
            append_item(create_directory_item(context, item))
        elif tag == 'track':  # mixed content photo playlist
            append_item(create_track_item(context, item))
        elif tag == 'video':  # mixed content photo playlist
            append_item(create_movie_item(context, item))

        if isinstance(content_counter.get(tag), int):
            content_counter[tag] += 1

    if items:
        content_type = 'images'
        if context.settings.mixed_content_type() == 'majority':
            majority = max(content_counter, key=content_counter.get)
            if majority == 'track':
                content_type = 'songs'
            elif majority == 'video':
                content_type = 'movies'

        xbmcplugin.setContent(get_handle(), content_type)
        xbmcplugin.addDirectoryItems(get_handle(), items, len(items))

    xbmcplugin.endOfDirectory(get_handle(), cacheToDisc=context.settings.cache_directory())
