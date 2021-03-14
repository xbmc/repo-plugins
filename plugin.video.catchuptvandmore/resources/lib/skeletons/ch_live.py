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

root = 'live_tv'

menu = {
    'rougetv': {
        'resolver': '/resources/lib/channels/ch/rougetv:get_live_url',
        'label': 'Rouge TV',
        'thumb': 'channels/ch/rougetv.png',
        'fanart': 'channels/ch/rougetv_fanart.jpg',
        'enabled': True,
        'order': 6
    },
    'tvm3': {
        'resolver': '/resources/lib/channels/ch/tvm3:get_live_url',
        'label': 'TVM3',
        'thumb': 'channels/ch/tvm3.png',
        'fanart': 'channels/ch/tvm3_fanart.jpg',
        'enabled': True,
        'order': 7
    },
    'rtsun': {
        'resolver': '/resources/lib/channels/ch/srgssr:get_live_url',
        'label': 'RTS Un',
        'thumb': 'channels/ch/rtsun.png',
        'fanart': 'channels/ch/rtsun_fanart.jpg',
        'enabled': True,
        'order': 9
    },
    'rtsdeux': {
        'resolver': '/resources/lib/channels/ch/srgssr:get_live_url',
        'label': 'RTS Deux',
        'thumb': 'channels/ch/rtsdeux.png',
        'fanart': 'channels/ch/rtsdeux_fanart.jpg',
        'enabled': True,
        'order': 10
    },
    'rtsinfo': {
        'resolver': '/resources/lib/channels/ch/srgssr:get_live_url',
        'label': 'RTS Info',
        'thumb': 'channels/ch/rtsinfo.png',
        'fanart': 'channels/ch/rtsinfo_fanart.jpg',
        'enabled': True,
        'order': 11
    },
    'rtscouleur3': {
        'resolver': '/resources/lib/channels/ch/srgssr:get_live_url',
        'label': 'RTS Couleur 3',
        'thumb': 'channels/ch/rtscouleur3.png',
        'fanart': 'channels/ch/rtscouleur3_fanart.jpg',
        'enabled': True,
        'order': 12
    },
    'rsila1': {
        'resolver': '/resources/lib/channels/ch/srgssr:get_live_url',
        'label': 'RSI La 1',
        'thumb': 'channels/ch/rsila1.png',
        'fanart': 'channels/ch/rsila1_fanart.jpg',
        'enabled': True,
        'order': 13
    },
    'rsila2': {
        'resolver': '/resources/lib/channels/ch/srgssr:get_live_url',
        'label': 'RSI La 2',
        'thumb': 'channels/ch/rsila2.png',
        'fanart': 'channels/ch/rsila2_fanart.jpg',
        'enabled': True,
        'order': 14
    },
    'srf1': {
        'resolver': '/resources/lib/channels/ch/srgssr:get_live_url',
        'label': 'SRF 1',
        'thumb': 'channels/ch/srf1.png',
        'fanart': 'channels/ch/srf1_fanart.jpg',
        'enabled': True,
        'order': 15
    },
    'srfinfo': {
        'resolver': '/resources/lib/channels/ch/srgssr:get_live_url',
        'label': 'SRF Info',
        'thumb': 'channels/ch/srfinfo.png',
        'fanart': 'channels/ch/srfinfo_fanart.jpg',
        'enabled': True,
        'order': 16
    },
    'srfzwei': {
        'resolver': '/resources/lib/channels/ch/srgssr:get_live_url',
        'label': 'SRF Zwei',
        'thumb': 'channels/ch/srfzwei.png',
        'fanart': 'channels/ch/srfzwei_fanart.jpg',
        'enabled': True,
        'order': 17
    },
    'rtraufsrf1': {
        'resolver': '/resources/lib/channels/ch/srgssr:get_live_url',
        'label': 'RTR auf SRF 1',
        'thumb': 'channels/ch/rtraufsrf1.png',
        'fanart': 'channels/ch/rtraufsrf1_fanart.jpg',
        'enabled': True,
        'order': 18
    },
    'rtraufsrfinfo': {
        'resolver': '/resources/lib/channels/ch/srgssr:get_live_url',
        'label': 'RTR auf SRF Info',
        'thumb': 'channels/ch/rtraufsrfinfo.png',
        'fanart': 'channels/ch/rtraufsrfinfo_fanart.jpg',
        'enabled': True,
        'order': 19
    },
    'rtraufsrf2': {
        'resolver': '/resources/lib/channels/ch/srgssr:get_live_url',
        'label': 'RTR auf SRF 2',
        'thumb': 'channels/ch/rtraufsrf2.png',
        'fanart': 'channels/ch/rtraufsrf2_fanart.jpg',
        'enabled': True,
        'order': 20
    },
    'teleticino': {
        'resolver': '/resources/lib/channels/ch/teleticino:get_live_url',
        'label': 'Teleticino',
        'thumb': 'channels/ch/teleticino.png',
        'fanart': 'channels/ch/teleticino_fanart.jpg',
        'enabled': True,
        'order': 21
    },
    'lemanbleu': {
        'resolver': '/resources/lib/channels/ch/lemanbleu:get_live_url',
        'label': 'Léman Bleu',
        'thumb': 'channels/ch/lemanbleu.png',
        'fanart': 'channels/ch/lemanbleu_fanart.jpg',
        'enabled': True,
        'order': 22
    },
    'telem1': {
        'resolver': '/resources/lib/channels/ch/telem1:get_live_url',
        'label': 'Tele M1',
        'thumb': 'channels/ch/telem1.png',
        'fanart': 'channels/ch/telem1_fanart.jpg',
        'enabled': True,
        'order': 23
    }
}
