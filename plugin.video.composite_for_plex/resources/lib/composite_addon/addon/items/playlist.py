# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from ..constants import MODES
from ..containers import GUIItem
from ..strings import encode_utf8
from ..strings import i18n
from .common import get_link_url
from .common import get_thumb_image
from .context_menu import ContextMenu
from .gui import create_gui_item


def create_playlist_item(context, item, listing=True):
    info_labels = {
        'title': encode_utf8(item.data.get('title', i18n('Unknown'))),
        'duration': int(item.data.get('duration', 0)) / 1000
    }

    extra_data = {
        'playlist': True,
        'ratingKey': item.data.get('ratingKey'),
        'type': item.data.get('playlistType', ''),
        'thumb': get_thumb_image(context, item.server, {
            'thumb': item.data.get('composite', '')
        }),
        'mode': MODES.GETCONTENT
    }

    if extra_data['type'] == 'video':
        extra_data['mode'] = MODES.MOVIES
    elif extra_data['type'] == 'audio':
        extra_data['mode'] = MODES.TRACKS
    elif extra_data['type'] == 'photo':
        extra_data['mode'] = MODES.PHOTOS

    item_url = get_link_url(item.server, item.url, item.data)

    context_menu = None
    if not context.settings.skip_context_menus():
        context_menu = ContextMenu(context, item.server, item_url, extra_data).menu

    if listing:
        gui_item = GUIItem(item_url, info_labels, extra_data, context_menu)
        return create_gui_item(context, gui_item)

    return item.url, info_labels
