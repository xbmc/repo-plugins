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
    - callback: Callback function to run once this item is selected
    - thumb: Item thumb path relative to "media" folder
    - fanart: Item fanart path relative to "meia" folder
    - module: Item module to load in order to work (like 6play.py)
"""

menu = {
    'telecinco': {
        'callback': 'live_bridge',
        'thumb': 'channels/es/telecinco.png',
        'fanart': 'channels/es/telecinco_fanart.jpg',
        'module': 'resources.lib.channels.es.mitele',
        'enabled': True,
        'order': 1
    },
    'cuatro': {
        'callback': 'live_bridge',
        'thumb': 'channels/es/cuatro.png',
        'fanart': 'channels/es/cuatro_fanart.jpg',
        'module': 'resources.lib.channels.es.mitele',
        'enabled': True,
        'order': 2
    },
    'fdf': {
        'callback': 'live_bridge',
        'thumb': 'channels/es/fdf.png',
        'fanart': 'channels/es/fdf_fanart.jpg',
        'module': 'resources.lib.channels.es.mitele',
        'enabled': True,
        'order': 3
    },
    'boing': {
        'callback': 'live_bridge',
        'thumb': 'channels/es/boing.png',
        'fanart': 'channels/es/boing_fanart.jpg',
        'module': 'resources.lib.channels.es.mitele',
        'enabled': True,
        'order': 4
    },
    'energy': {
        'callback': 'live_bridge',
        'thumb': 'channels/es/energy.png',
        'fanart': 'channels/es/energy_fanart.jpg',
        'module': 'resources.lib.channels.es.mitele',
        'enabled': True,
        'order': 5
    },
    'divinity': {
        'callback': 'live_bridge',
        'thumb': 'channels/es/divinity.png',
        'fanart': 'channels/es/divinity_fanart.jpg',
        'module': 'resources.lib.channels.es.mitele',
        'enabled': True,
        'order': 6
    },
    'bemad': {
        'callback': 'live_bridge',
        'thumb': 'channels/es/bemad.png',
        'fanart': 'channels/es/bemad_fanart.jpg',
        'module': 'resources.lib.channels.es.mitele',
        'enabled': True,
        'order': 7
    },
    'realmadridtv': {
        'callback': 'live_bridge',
        'thumb': 'channels/es/realmadridtv.png',
        'fanart': 'channels/es/realmadridtv_fanart.jpg',
        'module': 'resources.lib.channels.es.realmadridtv',
        'available_languages': ['EN', 'ES'],
        'enabled': True,
        'order': 8
    },
    'paramountchannel_es': {
        'callback': 'live_bridge',
        'thumb': 'channels/es/paramountchannel_es.png',
        'fanart': 'channels/es/paramountchannel_es_fanart.jpg',
        'module': 'resources.lib.channels.es.paramountchannel_es',
        'enabled': True,
        'order': 16
    }
}
