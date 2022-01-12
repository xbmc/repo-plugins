# -*- coding: utf-8 -*-
"""

    Copyright (C) 2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from kodi_six import xbmcplugin  # pylint: disable=import-error
from six import PY3

from ..addon.common import get_handle
from ..addon.constants import MODES
from ..addon.containers import Item
from ..addon.items.artist import create_artist_item
from ..addon.items.movie import create_movie_item
from ..addon.items.photo import create_photo_item
from ..addon.items.show import create_show_item
from ..addon.logger import Logger
from ..plex import plex

LOG = Logger()


def run(context):
    context.plex_network = plex.Plex(context.settings, load=True)

    section_type = get_section_type(context)
    all_sections = context.plex_network.all_sections()

    content_type = None
    items = []

    LOG.debug('Using list of %s sections: %s' % (len(all_sections), all_sections))

    for section in all_sections:

        if section.get_type() == section_type:
            if content_type is None:
                content_type = get_content_type(section)

            items += _list_content(
                context,
                context.plex_network.get_server_from_uuid(section.get_server_uuid()),
                section.get_path()
            )

    if items:
        add_sort_methods(content_type)
        xbmcplugin.setContent(get_handle(), content_type)
        xbmcplugin.addDirectoryItems(get_handle(), items, len(items))

    xbmcplugin.endOfDirectory(get_handle(), cacheToDisc=False)


def add_sort_methods(content_type):
    if content_type == 'movies':
        xbmcplugin.addSortMethod(get_handle(),
                                 xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE_IGNORE_THE)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_DATEADDED)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_VIDEO_YEAR)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_VIDEO_RATING)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_MPAA_RATING)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_UNSORTED)
    elif content_type == 'tvshows':
        xbmcplugin.addSortMethod(get_handle(),
                                 xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE_IGNORE_THE)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_VIDEO_YEAR)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_VIDEO_RATING)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_MPAA_RATING)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_UNSORTED)
    elif content_type == 'artists':
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_ARTIST_IGNORE_THE)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_LASTPLAYED)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_VIDEO_YEAR)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_UNSORTED)
    else:
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_VIDEO_YEAR)


def get_section_type(context):
    mode = int(context.params.get('mode', -1))

    if mode == MODES.MOVIES_ALL:
        return 'movie'

    if mode == MODES.TVSHOWS_ALL:
        return 'show'

    if mode == MODES.ARTISTS_ALL:
        return 'artist'

    if mode == MODES.PHOTOS_ALL:
        return 'photo'

    return ''


def get_content_type(section):
    if section.get_type() == 'show':
        return 'tvshows'

    if section.get_type() == 'movie':
        return 'movies'

    if section.get_type() == 'artist':
        return 'artists'

    if section.get_type() == 'photo':
        return 'images'

    return 'files'


def _list_content(context, server, section):
    section_id = [int(part) for part in section.split('/') if part.isdigit()][0]

    tree = server.get_section_all(section=section_id)
    if tree is None:
        return []

    iter_type = 'Video' if get_section_type(context) == 'movie' else 'Directory'
    if PY3:
        branches = tree.iter(iter_type)
    else:
        branches = tree.getiterator(iter_type)

    if not branches:
        return []

    items = []
    for content in branches:

        item = Item(server, server.get_url_location(), tree, content)
        if content.get('type') == 'show':
            items.append(create_show_item(context, item))
        elif content.get('type') == 'movie':
            items.append(create_movie_item(context, item))
        elif content.get('type') == 'artist':
            items.append(create_artist_item(context, item))
        elif content.get('type') == 'photo':
            items.append(create_photo_item(context, item))

    return items
