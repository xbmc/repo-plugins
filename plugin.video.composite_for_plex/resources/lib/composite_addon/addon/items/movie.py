# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import datetime
import json

from ..constants import COMBINED_SECTIONS
from ..constants import CONFIG
from ..constants import MODES
from ..containers import GUIItem
from ..logger import Logger
from ..strings import encode_utf8
from ..strings import i18n
from .common import get_fanart_image
from .common import get_media_data
from .common import get_metadata
from .common import get_thumb_image
from .context_menu import ContextMenu
from .gui import create_gui_item

LOG = Logger()


def create_movie_item(context, item, library=False):
    metadata = get_metadata(context, item.data)
    LOG.debug('Media attributes are %s' % json.dumps(metadata['attributes'], indent=4))
    # Required listItem entries for Kodi

    try:
        date_added = str(datetime.datetime.fromtimestamp(int(item.data.get('addedAt', 86400))))
    except ValueError:
        # ValueError: timestamp out of range for platform localtime()/gmtime() function
        date_added = str(datetime.datetime.fromtimestamp(86400))

    info_labels = {
        'plot': encode_utf8(item.data.get('summary', '')),
        'title': encode_utf8(item.data.get('title', i18n('Unknown'))),
        'sorttitle': encode_utf8(item.data.get('titleSort',
                                               item.data.get('title', i18n('Unknown')))),
        'rating': float(item.data.get('rating', 0)),
        'studio': encode_utf8(item.data.get('studio', '')),
        'mpaa': encode_utf8(item.data.get('contentRating', '')),
        'year': int(item.data.get('year', 0)),
        'date': item.data.get('originallyAvailableAt', '1970-01-01'),
        'premiered': item.data.get('originallyAvailableAt', '1970-01-01'),
        'tagline': item.data.get('tagline', ''),
        'dateAdded': date_added,
        'mediatype': 'movie',
        'playcount': int(int(item.data.get('viewCount', 0)) > 0),
        'cast': metadata['cast'],
        'director': ' / '.join(metadata['director']),
        'genre': ' / '.join(metadata['genre']),
        'set': ' / '.join(metadata['collections']),
        'writer': ' / '.join(metadata['writer']),
    }

    prefix_server = (context.params.get('mode') in COMBINED_SECTIONS and
                     context.settings.prefix_server_in_combined())

    if prefix_server:
        info_labels['title'] = '%s: %s' % (item.server.get_name(), info_labels['title'])

    if item.data.get('primaryExtraKey') is not None:
        info_labels['trailer'] = 'plugin://' + CONFIG['id'] + '/?url=%s%s?mode=%s' % \
                                 (item.server.get_url_location(),
                                  item.data.get('primaryExtraKey', ''),
                                  MODES.PLAYLIBRARY)
        LOG.debug('Trailer plugin url added: %s' % info_labels['trailer'])

    # Gather some data
    view_offset = item.data.get('viewOffset', 0)
    duration = int(metadata['attributes'].get('duration', item.data.get('duration', 0))) / 1000

    # Extra data required to manage other properties
    extra_data = {
        'type': 'Video',
        'source': 'movies',
        'thumb': get_thumb_image(context, item.server, item.data),
        'fanart_image': get_fanart_image(context, item.server, item.data),
        'key': item.data.get('key', ''),
        'ratingKey': str(item.data.get('ratingKey', 0)),
        'duration': duration,
        'resume': int(int(view_offset) / 1000)
    }

    if item.up_next is False:
        extra_data['parameters'] = {
            'up_next': str(item.up_next).lower()
        }

    if item.tree.get('playlistType'):
        playlist_key = str(item.tree.get('ratingKey', 0))
        if item.data.get('playlistItemID') and playlist_key:
            extra_data.update({
                'playlist_item_id': item.data.get('playlistItemID'),
                'playlist_title': item.tree.get('title'),
                'playlist_url': '/playlists/%s/items' % playlist_key
            })

    if item.tree.tag == 'MediaContainer':
        extra_data.update({
            'library_section_uuid': item.tree.get('librarySectionUUID')
        })

    # Add extra media flag data
    if not context.settings.skip_flags():
        extra_data.update(get_media_data(metadata['attributes']))

    # Build any specific context menu entries
    context_menu = None
    if not context.settings.skip_context_menus():
        context_menu = ContextMenu(context, item.server, item.url, extra_data).menu

    # http:// <server> <path> &mode=<mode>
    extra_data['mode'] = MODES.PLAYLIBRARY
    if library:
        extra_data['path_mode'] = MODES.TXT_MOVIES_LIBRARY

    item_url = item.server.join_url(item.server.get_url_location(), extra_data['key'])

    gui_item = GUIItem(item_url, info_labels, extra_data, context_menu)
    gui_item.is_folder = False
    return create_gui_item(context, gui_item)
