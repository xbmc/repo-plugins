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
from .common import get_fanart_image
from .common import get_thumb_image
from .gui import create_gui_item


def create_artist_item(context, item):
    info_labels = {
        'artist': encode_utf8(item.data.get('title', ''))
    }

    info_labels['title'] = info_labels['artist']

    prefix_server = (context.params.get('mode') in COMBINED_SECTIONS and
                     context.settings.prefix_server_in_combined())

    if prefix_server:
        info_labels['title'] = '%s: %s' % (item.server.get_name(), info_labels['title'])

    extra_data = {
        'type': 'Music',
        'thumb': get_thumb_image(context, item.server, item.data),
        'fanart_image': get_fanart_image(context, item.server, item.data),
        'ratingKey': item.data.get('title', ''),
        'key': item.data.get('key', ''),
        'mode': MODES.ALBUMS,
        'plot': item.data.get('summary', ''),
        'mediatype': 'artist'
    }

    url = item.server.join_url(item.server.get_url_location(), extra_data['key'])

    gui_item = GUIItem(url, info_labels, extra_data)
    return create_gui_item(context, gui_item)
