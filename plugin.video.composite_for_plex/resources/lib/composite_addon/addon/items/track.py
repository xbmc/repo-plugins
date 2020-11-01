# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import json

from ..constants import COMBINED_SECTIONS
from ..constants import MODES
from ..containers import GUIItem
from ..logger import Logger
from ..strings import encode_utf8
from ..strings import i18n
from .common import get_fanart_image
from .common import get_thumb_image
from .context_menu import ContextMenu
from .gui import create_gui_item

LOG = Logger()


def create_track_item(context, item, listing=True):
    part_info_labels = ()

    for child in item.data:
        for babies in child:
            if babies.tag == 'Part':
                part_info_labels = (dict(babies.items()))

    LOG.debug('Part: %s' % json.dumps(part_info_labels, indent=4))

    info_labels = {
        'TrackNumber': int(item.data.get('index', 0)),
        'discnumber': int(item.data.get('parentIndex', 0)),
        'title': str(item.data.get('index', 0)).zfill(2) + '. ' +
                 (item.data.get('title', i18n('Unknown'))),
        'rating': float(item.data.get('rating', 0)),
        'album': encode_utf8(item.data.get('parentTitle', item.tree.get('parentTitle', ''))),
        'artist': encode_utf8(item.data.get('grandparentTitle',
                                            item.tree.get('grandparentTitle', ''))),
        'duration': int(item.data.get('duration', 0)) / 1000,
        'mediatype': 'song'
    }

    prefix_server = (context.params.get('mode') in COMBINED_SECTIONS and
                     context.settings.prefix_server_in_combined())

    if prefix_server:
        info_labels['title'] = '%s: %s' % (item.server.get_name(), info_labels['title'])

    section_art = get_fanart_image(context, item.server, item.tree)
    if item.data.get('thumb'):
        section_thumb = get_thumb_image(context, item.server, item.data)
    else:
        section_thumb = get_thumb_image(context, item.server, item.tree)

    extra_data = {
        'type': 'music',
        'fanart_image': section_art,
        'thumb': section_thumb,
        'key': item.data.get('key', ''),
        'ratingKey': str(item.data.get('ratingKey', 0)),
        'mode': MODES.PLAYLIBRARY
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

    # If we are streaming, then get the virtual location
    item_url = item.server.join_url(item.server.get_url_location(), extra_data['key'])

    # Build any specific context menu entries
    context_menu = None
    if not context.settings.skip_context_menus():
        context_menu = ContextMenu(context, item.server, item_url, extra_data).menu

    if listing:
        gui_item = GUIItem(item_url, info_labels, extra_data, context_menu)
        gui_item.is_folder = False
        return create_gui_item(context, gui_item)

    return item_url, info_labels
