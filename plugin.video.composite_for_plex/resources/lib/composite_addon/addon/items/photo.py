# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from ..constants import COMBINED_SECTIONS
from ..constants import MODES
from ..containers import GUIItem
from ..strings import encode_utf8
from ..strings import i18n
from .common import get_fanart_image
from .common import get_link_url
from .common import get_thumb_image
from .context_menu import ContextMenu
from .gui import create_gui_item


def create_photo_item(context, item):
    info_labels = {
        'title': encode_utf8(item.data.get('title', item.data.get('name', i18n('Unknown'))))
    }

    if not info_labels['title']:
        info_labels['title'] = i18n('Unknown')

    prefix_server = (context.params.get('mode') in COMBINED_SECTIONS and
                     context.settings.prefix_server_in_combined())

    if prefix_server:
        info_labels['title'] = '%s: %s' % (item.server.get_name(), info_labels['title'])

    extra_data = {
        'thumb': get_thumb_image(context, item.server, item.data),
        'fanart_image': get_fanart_image(context, item.server, item.data),
        'type': 'image',
        'ratingKey': item.data.get('ratingKey'),
    }

    if extra_data['fanart_image'] == '':
        extra_data['fanart_image'] = get_fanart_image(context, item.server, item.tree)

    item_url = get_link_url(item.server, item.url, item.data)

    if item.data.tag == 'Directory':
        extra_data['mode'] = MODES.PHOTOS
        extra_data['type'] = 'folder'
        gui_item = GUIItem(item_url, info_labels, extra_data)
        return create_gui_item(context, gui_item)

    if item.data.tag == 'Photo' and (item.tree.get('viewGroup', '') == 'photo' or
                                     item.tree.get('playlistType') == 'photo'):
        get_formatted_url = item.server.get_formatted_url
        for pics in item.data:
            if pics.tag == 'Media':
                parts = [img for img in pics if img.tag == 'Part']
                for part in parts:
                    extra_data['key'] = get_formatted_url(part.get('key', ''))
                    info_labels['size'] = int(part.get('size', 0))
                    info_labels['picturepath'] = extra_data['key']
                    item_url = extra_data['key']

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

        context_menu = None
        if not context.settings.skip_context_menus():
            context_menu = ContextMenu(context, item.server, item_url, extra_data).menu

        gui_item = GUIItem(item_url, info_labels, extra_data, context_menu)
        gui_item.is_folder = False
        return create_gui_item(context, gui_item)

    return None
