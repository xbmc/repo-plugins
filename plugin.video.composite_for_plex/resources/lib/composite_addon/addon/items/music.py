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
from ..logger import Logger
from ..strings import encode_utf8
from ..strings import i18n
from .common import get_fanart_image
from .common import get_link_url
from .common import get_thumb_image
from .gui import create_gui_item

LOG = Logger()


def create_music_item(context, item):
    info_labels = {
        'genre': encode_utf8(item.data.get('genre', '')),
        'artist': encode_utf8(item.data.get('artist', '')),
        'year': int(item.data.get('year', 0)),
        'album': encode_utf8(item.data.get('album', '')),
        'tracknumber': int(item.data.get('index', 0)),
        'title': i18n('Unknown')
    }

    extra_data = {
        'type': 'Music',
        'thumb': get_thumb_image(context, item.server, item.data),
        'fanart_image': get_fanart_image(context, item.server, item.data)
    }

    if extra_data['fanart_image'] == '':
        extra_data['fanart_image'] = get_fanart_image(context, item.server, item.tree)

    item_url = get_link_url(item.server, item.url, item.data)

    if item.data.tag == 'Track':
        LOG.debug('Track Tag')
        info_labels['mediatype'] = 'song'
        info_labels['title'] = item.data.get('track',
                                             encode_utf8(item.data.get('title', i18n('Unknown'))))
        info_labels['duration'] = int(int(item.data.get('total_time', 0)) / 1000)

        extra_data['mode'] = MODES.BASICPLAY

        gui_item = GUIItem(item_url, info_labels, extra_data)
        gui_item.is_folder = False
        return create_gui_item(context, gui_item)

    info_labels['mediatype'] = 'artist'

    if item.data.tag == 'Artist':
        LOG.debug('Artist Tag')
        info_labels['mediatype'] = 'artist'
        info_labels['title'] = encode_utf8(item.data.get('artist', i18n('Unknown')))

    elif item.data.tag == 'Album':
        LOG.debug('Album Tag')
        info_labels['mediatype'] = 'album'
        info_labels['title'] = encode_utf8(item.data.get('album', i18n('Unknown')))

    elif item.data.tag == 'Genre':
        info_labels['title'] = encode_utf8(item.data.get('genre', i18n('Unknown')))

    else:
        LOG.debug('Generic Tag: %s' % item.data.tag)
        info_labels['title'] = encode_utf8(item.data.get('title', i18n('Unknown')))

    extra_data['mode'] = MODES.MUSIC

    gui_item = GUIItem(item_url, info_labels, extra_data)
    return create_gui_item(context, gui_item)
