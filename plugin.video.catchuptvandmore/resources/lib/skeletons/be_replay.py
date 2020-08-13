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
    'brf': {
        'route': '/resources/lib/channels/be/brf:list_categories',
        'label': 'BRF Mediathek',
        'thumb': 'channels/be/brf.png',
        'fanart': 'channels/be/brf_fanart.jpg',
        'enabled': True,
        'order': 1
    },
    'rtlplay': {
        'route': '/resources/lib/channels/be/rtlplaybe:rtlplay_root',
        'label': 'RTLplay',
        'thumb': 'channels/be/rtlplay.png',
        'fanart': 'channels/be/rtlplay_fanart.jpg',
        'enabled': True,
        'order': 2
    },
    'vrt': {
        'route': '/resources/lib/channels/be/vrt:list_root',
        'label': 'VRT NU',
        'thumb': 'channels/be/vrt.png',
        'fanart': 'channels/be/vrt_fanart.jpg',
        'enabled': True,
        'order': 5
    },
    'telemb': {
        'route': '/resources/lib/channels/be/telemb:list_programs',
        'label': 'Télé MB',
        'thumb': 'channels/be/telemb.png',
        'fanart': 'channels/be/telemb_fanart.jpg',
        'enabled': True,
        'order': 6
    },
    'rtc': {
        'route': '/resources/lib/channels/be/rtc:list_categories',
        'label': 'RTC Télé Liège',
        'thumb': 'channels/be/rtc.png',
        'fanart': 'channels/be/rtc_fanart.jpg',
        'enabled': True,
        'order': 7
    },
    'auvio': {
        'route': '/resources/lib/channels/be/rtbf:list_categories',
        'label': 'RTBF Auvio',
        'thumb': 'channels/be/auvio.png',
        'fanart': 'channels/be/auvio_fanart.jpg',
        'enabled': True,
        'order': 8
    },
    'tvlux': {
        'route': '/resources/lib/channels/be/tvlux:list_categories',
        'label': 'TV Lux',
        'thumb': 'channels/be/tvlux.png',
        'fanart': 'channels/be/tvlux_fanart.jpg',
        'enabled': True,
        'order': 9
    },
    'bx1': {
        'route': '/resources/lib/channels/be/bx1:list_programs',
        'label': 'BX1',
        'thumb': 'channels/be/bx1.png',
        'fanart': 'channels/be/bx1_fanart.jpg',
        'enabled': True,
        'order': 13
    },
    'nrjhitstvbe': {
        'route': '/resources/lib/channels/be/nrjhitstvbe:list_videos',
        'label': 'NRJ Hits TV',
        'thumb': 'channels/be/nrjhitstvbe.png',
        'fanart': 'channels/be/nrjhitstvbe_fanart.jpg',
        'enabled': True,
        'order': 17
    },
    'tvcom': {
        'route': '/resources/lib/channels/be/tvcom:list_categories',
        'label': 'TV Com',
        'thumb': 'channels/be/tvcom.png',
        'fanart': 'channels/be/tvcom_fanart.jpg',
        'enabled': True,
        'order': 19
    },
    'canalc': {
        'route': '/resources/lib/channels/be/canalc:list_programs',
        'label': 'Canal C',
        'thumb': 'channels/be/canalc.png',
        'fanart': 'channels/be/canalc_fanart.jpg',
        'enabled': True,
        'order': 20
    }
}
