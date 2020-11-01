# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from kodi_six import xbmcplugin  # pylint: disable=import-error

from ..common import get_handle
from ..constants import MODES
from ..containers import GUIItem
from ..containers import Item
from ..items.common import get_fanart_image
from ..items.common import get_link_url
from ..items.common import get_thumb_image
from ..items.episode import create_episode_item
from ..items.gui import create_gui_item
from ..items.movie import create_movie_item
from ..items.playlist import create_playlist_item
from ..items.track import create_track_item
from ..strings import encode_utf8
from ..strings import i18n
from ..utils import get_xml


def process_xml(context, url, tree=None):
    """
        Main function to parse plugin XML from PMS
        Will create dir or item links depending on what the
        main tag is.
        @input: plugin page URL
        @return: nothing, creates Kodi GUI listing
    """

    server = context.plex_network.get_server_from_url(url)
    tree = get_xml(context, url, tree)

    if tree is None:
        return

    content_type = 'files'

    items = []
    append_item = items.append

    # .iter includes itself, this is unwanted
    branches = [elem for elem in tree.iter() if elem is not tree]
    for branch in branches:
        details = {}
        if branch.get('title'):
            details['title'] = encode_utf8(branch.get('title'))

        if not details.get('title'):
            details['title'] = encode_utf8(branch.get('name', i18n('Unknown')))

        extra_data = {
            'thumb': get_thumb_image(context, server, branch),
            'fanart_image': get_fanart_image(context, server, branch),
            'identifier': tree.get('identifier', ''),
            'type': 'Video'
        }

        if extra_data['fanart_image'] == '':
            extra_data['fanart_image'] = get_fanart_image(context, server, tree)

        _url = get_link_url(server, url, branch)

        if branch.tag in ['Directory', 'Podcast']:
            extra_data['mode'] = MODES.PROCESSXML
            gui_item = GUIItem(_url, details, extra_data)
            append_item(create_gui_item(context, gui_item))

        elif branch.tag == 'Track':
            content_type = 'songs'
            item = Item(server, url, tree, branch)
            append_item(create_track_item(context, item))

        elif branch.tag == 'Playlist':
            item = Item(server, url, tree, branch)
            append_item(create_playlist_item(context, item))

        elif branch.tag == 'Video':
            item = Item(server, url, tree, branch)

            if tree.get('viewGroup') == 'movie':
                content_type = 'movies'
                append_item(create_movie_item(context, item))
                continue

            if tree.get('viewGroup') == 'episode':
                content_type = 'episodes'
                append_item(create_episode_item(context, item))
                continue

            content_type = 'videos'
            append_item(create_movie_item(context, item))

    if items:
        _set_content(content_type)
        xbmcplugin.addDirectoryItems(get_handle(), items, len(items))

    xbmcplugin.endOfDirectory(get_handle(), cacheToDisc=context.settings.cache_directory())


def _set_content(content_type):
    if content_type == 'files':
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_UNSORTED)

    elif content_type == 'songs':
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_DURATION)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_SONG_RATING)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_TRACKNUM)

    elif content_type in ['movies', 'videos']:
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE_IGNORE_THE)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_DATEADDED)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_VIDEO_RATING)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_VIDEO_YEAR)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
        if content_type != 'videos':
            xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_MPAA_RATING)

    elif content_type == 'episodes':
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE_IGNORE_THE)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_DATEADDED)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_VIDEO_RATING)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_VIDEO_YEAR)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
        xbmcplugin.addSortMethod(get_handle(), xbmcplugin.SORT_METHOD_MPAA_RATING)

    xbmcplugin.setContent(get_handle(), content_type)
