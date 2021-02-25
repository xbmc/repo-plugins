# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2016  SylvainCecchetto

    This file is part of Catch-up TV & More.

    Catch-up TV & More is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Catch-up TV & More is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with Catch-up TV & More; if not, write to the Free Software Foundation,
    Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals
from codequick import Script, utils
"""
The following dictionaries describe
the addon's tree architecture.
* Key: item id
* Value: item infos
    - route (folder)/resolver (playable URL): Callback function to run once this item is selected
    - thumb: Item thumb path relative to "media" folder
    - fanart: Item fanart path relative to "meia" folder
"""

root = 'live_tv'

menu = {
    'telecinco': {
        'resolver': '/resources/lib/channels/es/mitele:get_live_url',
        'label': 'Telecinco',
        'thumb': 'channels/es/telecinco.png',
        'fanart': 'channels/es/telecinco_fanart.jpg',
        'enabled': False,
        'order': 1
    },
    'cuatro': {
        'resolver': '/resources/lib/channels/es/mitele:get_live_url',
        'label': 'Cuatro',
        'thumb': 'channels/es/cuatro.png',
        'fanart': 'channels/es/cuatro_fanart.jpg',
        'enabled': False,
        'order': 2
    },
    'fdf': {
        'resolver': '/resources/lib/channels/es/mitele:get_live_url',
        'label': 'Factoria de Ficcion',
        'thumb': 'channels/es/fdf.png',
        'fanart': 'channels/es/fdf_fanart.jpg',
        'enabled': False,
        'order': 3
    },
    'boing': {
        'resolver': '/resources/lib/channels/es/mitele:get_live_url',
        'label': 'Boing',
        'thumb': 'channels/es/boing.png',
        'fanart': 'channels/es/boing_fanart.jpg',
        'enabled': False,
        'order': 4
    },
    'energy': {
        'resolver': '/resources/lib/channels/es/mitele:get_live_url',
        'label': 'Energy TV',
        'thumb': 'channels/es/energy.png',
        'fanart': 'channels/es/energy_fanart.jpg',
        'enabled': False,
        'order': 5
    },
    'divinity': {
        'resolver': '/resources/lib/channels/es/mitele:get_live_url',
        'label': 'Divinity',
        'thumb': 'channels/es/divinity.png',
        'fanart': 'channels/es/divinity_fanart.jpg',
        'enabled': False,
        'order': 6
    },
    'bemad': {
        'resolver': '/resources/lib/channels/es/mitele:get_live_url',
        'label': 'Be Mad',
        'thumb': 'channels/es/bemad.png',
        'fanart': 'channels/es/bemad_fanart.jpg',
        'enabled': False,
        'order': 7
    },
    'realmadridtv': {
        'resolver': '/resources/lib/channels/es/realmadridtv:get_live_url',
        'label': 'Realmadrid TV (' + utils.ensure_unicode(Script.setting['realmadridtv.language']) + ')',
        'thumb': 'channels/es/realmadridtv.png',
        'fanart': 'channels/es/realmadridtv_fanart.jpg',
        'available_languages': ['EN', 'ES'],
        'enabled': True,
        'order': 8
    },
    'paramountchannel_es': {
        'resolver': '/resources/lib/channels/es/paramountchannel_es:get_live_url',
        'label': 'Paramount Channel (ES)',
        'thumb': 'channels/es/paramountchannel_es.png',
        'fanart': 'channels/es/paramountchannel_es_fanart.jpg',
        'enabled': True,
        'order': 16
    },
    'la1': {
        'resolver': '/resources/lib/channels/es/rtve:get_live_url',
        'label': 'La 1',
        'thumb': 'channels/es/la1.png',
        'fanart': 'channels/es/la1_fanart.jpg',
        'enabled': True,
        'order': 17
    },
    'la2': {
        'resolver': '/resources/lib/channels/es/rtve:get_live_url',
        'label': 'La 2',
        'thumb': 'channels/es/la2.png',
        'fanart': 'channels/es/la2_fanart.jpg',
        'enabled': True,
        'order': 18
    },
    'tdp': {
        'resolver': '/resources/lib/channels/es/rtve:get_live_url',
        'label': 'Teledeporte',
        'thumb': 'channels/es/tdp.png',
        'fanart': 'channels/es/tdp_fanart.jpg',
        'enabled': True,
        'order': 19
    },
    '24h': {
        'resolver': '/resources/lib/channels/es/rtve:get_live_url',
        'label': 'Canal 24 horas',
        'thumb': 'channels/es/24h.png',
        'fanart': 'channels/es/24h_fanart.jpg',
        'enabled': True,
        'order': 20
    },
    'trece': {
        'resolver': '/resources/lib/channels/es/trece:get_live_url',
        'label': 'Trece',
        'thumb': 'channels/es/trece.png',
        'fanart': 'channels/es/trece_fanart.jpg',
        'enabled': True,
        'order': 20
    }
}
