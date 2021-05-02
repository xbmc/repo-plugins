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
from .common import get_fanart_image
from .common import get_thumb_image
from .gui import create_gui_item


def create_album_item(context, item):
    info_labels = {
        'album': encode_utf8(item.data.get('title', '')),
        'year': int(item.data.get('year', 0)),
        'artist': encode_utf8(item.tree.get('parentTitle', item.data.get('parentTitle', ''))),
        'mediatype': 'album'
    }

    info_labels['title'] = info_labels['album']
    if 'recentlyAdded' in item.url:
        info_labels['title'] = '%s - %s' % (info_labels['artist'], info_labels['title'])

    extra_data = {
        'type': 'Music',
        'thumb': get_thumb_image(context, item.server, item.data),
        'fanart_image': get_fanart_image(context, item.server, item.data),
        'key': item.data.get('key', ''),
        'mode': MODES.TRACKS,
        'plot': item.data.get('summary', '')
    }

    if extra_data['fanart_image'] == '':
        extra_data['fanart_image'] = get_fanart_image(context, item.server, item.tree)

    url = '%s%s' % (item.server.get_url_location(), extra_data['key'])

    gui_item = GUIItem(url, info_labels, extra_data)
    return create_gui_item(context, gui_item)
