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
from codequick import Script
"""
The following dictionaries describe
the addon's tree architecture.
* Key: item id
* Value: item infos
    - route (folder)/resolver (playable URL): Callback function to run once this item is selected
    - thumb: Item thumb path relative to "media" folder
    - fanart: Item fanart path relative to "meia" folder
"""

menu = {
    'rts': {
        'route': '/resources/lib/channels/ch/srgssr:list_categories',
        'label': 'RTS',
        'thumb': 'channels/ch/rts.png',
        'fanart': 'channels/ch/rts_fanart.jpg',
        'enabled': True,
        'order': 1
    },
    'rsi': {
        'route': '/resources/lib/channels/ch/srgssr:list_categories',
        'label': 'RSI',
        'thumb': 'channels/ch/rsi.png',
        'fanart': 'channels/ch/rsi_fanart.jpg',
        'enabled': True,
        'order': 2
    },
    'srf': {
        'route': '/resources/lib/channels/ch/srgssr:list_categories',
        'label': 'SRF',
        'thumb': 'channels/ch/srf.png',
        'fanart': 'channels/ch/srf_fanart.jpg',
        'enabled': True,
        'order': 3
    },
    'rtr': {
        'route': '/resources/lib/channels/ch/srgssr:list_categories',
        'label': 'RTR',
        'thumb': 'channels/ch/rtr.png',
        'fanart': 'channels/ch/rtr_fanart.jpg',
        'enabled': True,
        'order': 4
    },
    'swissinfo': {
        'route': '/resources/lib/channels/ch/srgssr:list_categories',
        'label': 'SWISSINFO',
        'thumb': 'channels/ch/swissinfo.png',
        'fanart': 'channels/ch/swissinfo_fanart.jpg',
        'enabled': True,
        'order': 5
    },
    'tvm3': {
        'route': '/resources/lib/channels/ch/tvm3:list_programs',
        'label': 'TVM3',
        'thumb': 'channels/ch/tvm3.png',
        'fanart': 'channels/ch/tvm3_fanart.jpg',
        'enabled': True,
        'order': 7
    },
    'becurioustv': {
        'route': '/resources/lib/channels/ch/becurioustv:list_categories',
        'label': 'BeCurious TV',
        'thumb': 'channels/ch/becurioustv.png',
        'fanart': 'channels/ch/becurioustv_fanart.jpg',
        'enabled': True,
        'order': 8
    },
    'lemanbleu': {
        'route': '/resources/lib/channels/ch/lemanbleu:list_programs',
        'label': 'Léman Bleu',
        'thumb': 'channels/ch/lemanbleu.png',
        'fanart': 'channels/ch/lemanbleu_fanart.jpg',
        'enabled': True,
        'order': 22
    }
}
