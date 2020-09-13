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

menu = {
    'telequebec': {
        'resolver': '/resources/lib/channels/ca/telequebec:get_live_url',
        'label': 'Télé-Québec',
        'thumb': 'channels/ca/telequebec.png',
        'fanart': 'channels/ca/telequebec_fanart.jpg',
        'enabled': True,
        'order': 4
    },
    'tva': {
        'resolver': '/resources/lib/channels/ca/tva:get_live_url',
        'label': 'TVA',
        'thumb': 'channels/ca/tva.png',
        'fanart': 'channels/ca/tva_fanart.jpg',
        'enabled': True,
        'order': 5
    },
    'icitele': {
        'resolver': '/resources/lib/channels/ca/icitele:get_live_url',
        'label': 'ICI Télé (' + utils.ensure_unicode(Script.setting['icitele.language']) + ')',
        'thumb': 'channels/ca/icitele.png',
        'fanart': 'channels/ca/icitele_fanart.jpg',
        'available_languages': [
            'Vancouver', 'Regina', 'Toronto', 'Edmonton', 'Rimouski',
            'Québec', 'Winnipeg', 'Moncton', 'Ottawa',
            'Montréal'
        ],
        'enabled': True,
        'order': 6
    },
    'ntvca': {
        'resolver': '/resources/lib/channels/ca/ntvca:get_live_url',
        'label': 'NTV',
        'thumb': 'channels/ca/ntvca.png',
        'fanart': 'channels/ca/ntvca_fanart.jpg',
        'enabled': True,
        'order': 7
    },
    'telemag': {
        'resolver': '/resources/lib/channels/ca/telemag:get_live_url',
        'label': 'Télé-Mag',
        'thumb': 'channels/ca/telemag.png',
        'fanart': 'channels/ca/telemag_fanart.jpg',
        'enabled': True,
        'order': 9
    },
    'vtele': {
        'resolver': '/resources/lib/channels/ca/noovo:get_live_url',
        'label': 'V Télé',
        'thumb': 'channels/ca/vtele.png',
        'fanart': 'channels/ca/vtele_fanart.jpg',
        'enabled': True,
        'order': 10
    },
    'cbc': {
        'resolver': '/resources/lib/channels/ca/cbc:get_live_url',
        'label': 'CBC (' + utils.ensure_unicode(Script.setting['cbc.language']) + ')',
        'thumb': 'channels/ca/cbc.png',
        'fanart': 'channels/ca/cbc_fanart.jpg',
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
        'resolver': '/resources/lib/channels/ca/tva:get_live_url',
        'label': 'LCN',
        'thumb': 'channels/ca/lcn.png',
        'fanart': 'channels/ca/lcn_fanart.jpg',
        'enabled': False,
        'order': 12
    },
    'yoopa': {
        'resolver': '/resources/lib/channels/ca/tva:get_live_url',
        'label': 'Yoopa',
        'thumb': 'channels/ca/yoopa.png',
        'fanart': 'channels/ca/yoopa_fanart.jpg',
        'enabled': False,
        'order': 13
    }
}
