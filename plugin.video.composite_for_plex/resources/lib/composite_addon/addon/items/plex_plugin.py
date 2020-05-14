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
from .common import get_fanart_image
from .common import get_link_url
from .common import get_thumb_image
from .gui import create_gui_item


def create_plex_plugin_item(context, item):
    if not item.data.get('title'):
        return None

    info_labels = {
        'title': encode_utf8(item.data.get('title'))
    }

    if info_labels['title']:
        info_labels['title'] = encode_utf8(item.data.get('name', i18n('Unknown')))

    if item.data.get('summary'):
        info_labels['plot'] = item.data.get('summary')

    extra_data = {
        'thumb': get_thumb_image(context, item.server, item.data),
        'fanart_image': get_fanart_image(context, item.server, item.data),
        'identifier': item.tree.get('identifier', ''),
        'type': 'Video',
        'key': item.data.get('key', '')
    }

    if ((item.tree.get('identifier') != 'com.plexapp.plugins.myplex') and
            ('node.plexapp.com' in item.url)):
        extra_data['key'] = extra_data['key'].replace('node.plexapp.com:32400',
                                                      item.server.get_location())

    if extra_data['fanart_image'] == '':
        extra_data['fanart_image'] = get_fanart_image(context, item.server, item.tree)

    item_url = get_link_url(item.server, item.url, extra_data)

    if item.data.tag in ['Directory', 'Podcast']:
        gui_item = GUIItem(item_url, info_labels, extra_data)
        return get_directory_item(context, item.data, gui_item)

    if item.data.tag == 'Setting':
        gui_item = GUIItem(item.url, info_labels, extra_data)
        return get_setting_item(context, item.data, gui_item)

    if item.data.tag == 'Video':
        gui_item = GUIItem(item_url, info_labels, extra_data)
        return get_video_item(context, item.data, gui_item)

    return None


def get_directory_item(context, data, item):
    item.extra['mode'] = MODES.PLEXPLUGINS
    if data.get('search') == '1':
        item.extra['mode'] = MODES.CHANNELSEARCH
        item.extra['parameters'] = {
            'prompt': encode_utf8(data.get('prompt', i18n('Enter search term')))
        }

    gui_item = GUIItem(item.url, item.info_labels, item.extra)
    return create_gui_item(context, gui_item)


def get_setting_item(context, data, item):
    value = data.get('value')
    if data.get('option') == 'hidden':
        value = '********'
    elif data.get('type') == 'text':
        value = data.get('value')
    elif data.get('type') == 'enum':
        value = data.get('values').split('|')[int(data.get('value', 0))]

    item.info_labels['title'] = '%s - [%s]' % \
                                (encode_utf8(data.get('label', i18n('Unknown'))), value)
    item.extra['mode'] = MODES.CHANNELPREFS
    item.extra['parameters'] = {
        'id': data.get('id')
    }

    gui_item = GUIItem(item.url, item.info_labels, item.extra)
    return create_gui_item(context, gui_item)


def get_video_item(context, data, item):
    item.extra['mode'] = MODES.VIDEOPLUGINPLAY

    for child in data:
        if child.tag == 'Media':
            item.extra['parameters'] = {
                'indirect': child.get('indirect', '0')
            }

    gui_item = GUIItem(item.url, item.info_labels, item.extra)
    gui_item.is_folder = False
    return create_gui_item(context, gui_item)
