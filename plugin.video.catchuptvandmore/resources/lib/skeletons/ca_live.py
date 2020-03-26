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
    'telequebec': {
        'callback': 'live_bridge',
        'thumb': 'channels/ca/telequebec.png',
        'fanart': 'channels/ca/telequebec_fanart.jpg',
        'module': 'resources.lib.channels.ca.telequebec',
        'enabled': True,
        'order': 4
    },
    'tva': {
        'callback': 'live_bridge',
        'thumb': 'channels/ca/tva.png',
        'fanart': 'channels/ca/tva_fanart.jpg',
        'module': 'resources.lib.channels.ca.tva',
        'enabled': True,
        'order': 5
    },
    'icitele': {
        'callback': 'live_bridge',
        'thumb': 'channels/ca/icitele.png',
        'fanart': 'channels/ca/icitele_fanart.jpg',
        'module': 'resources.lib.channels.ca.icitele',
        'available_languages': [
            'Vancouver', 'Regina', 'Toronto', 'Edmonton', 'Rimouski',
            'Québec', 'Winnipeg', 'Moncton', 'Ottawa',
            'Montréal'
        ],
        'enabled': True,
        'order': 6
    },
    'ntvca': {
        'callback': 'live_bridge',
        'thumb': 'channels/ca/ntvca.png',
        'fanart': 'channels/ca/ntvca_fanart.jpg',
        'module': 'resources.lib.channels.ca.ntvca',
        'enabled': True,
        'order': 7
    },
    'telemag': {
        'callback': 'live_bridge',
        'thumb': 'channels/ca/telemag.png',
        'fanart': 'channels/ca/telemag_fanart.jpg',
        'module': 'resources.lib.channels.ca.telemag',
        'enabled': True,
        'order': 9
    },
    'vtele': {
        'callback': 'live_bridge',
        'thumb': 'channels/ca/vtele.png',
        'fanart': 'channels/ca/vtele_fanart.jpg',
        'module': 'resources.lib.channels.ca.noovo',
        'enabled': True,
        'order': 10
    },
    'cbc': {
        'callback': 'live_bridge',
        'thumb': 'channels/ca/cbc.png',
        'fanart': 'channels/ca/cbc_fanart.jpg',
        'module': 'resources.lib.channels.ca.cbc',
        'available_languages': [
            'Ottawa', 'Montreal', 'Charlottetown', 'Fredericton',
            'Halifax', 'Windsor', 'Yellowknife', 'Winnipeg',
            'Regina', 'Calgary', 'Edmonton', 'Vancouver',
            'Toronto', 'St. John\'s'
        ],
        'enabled': True,
        'order': 11
    },
    'lcn': {
        'callback': 'live_bridge',
        'thumb': 'channels/ca/lcn.png',
        'fanart': 'channels/ca/lcn_fanart.jpg',
        'module': 'resources.lib.channels.ca.tva',
        'enabled': True,
        'order': 12
    },
    'yoopa': {
        'callback': 'live_bridge',
        'thumb': 'channels/ca/yoopa.png',
        'fanart': 'channels/ca/yoopa_fanart.jpg',
        'module': 'resources.lib.channels.ca.tva',
        'enabled': True,
        'order': 13
    }
}
