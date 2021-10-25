# -*- coding: utf-8 -*-
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

# The following dictionaries describe
# the addon's tree architecture.
# * Key: item id
# * Value: item infos
#     - route (folder)/resolver (playable URL): Callback function to run once this item is selected
#     - thumb: Item thumb path relative to "media" folder
#     - fanart: Item fanart path relative to "media" folder

root = 'live_tv'

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
        'label': 'ICI Télé',
        'thumb': 'channels/ca/icitele.png',
        'fanart': 'channels/ca/icitele_fanart.jpg',
        'available_languages': {
            'Vancouver': {}, 'Regina': {}, 'Toronto': {}, 'Edmonton': {}, 'Rimouski': {},
            'Québec': {}, 'Winnipeg': {}, 'Moncton': {}, 'Ottawa': {}, 'Sherbrooke': {}, 'Trois-Rivières': {},
            'Montréal': {}
        },
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
    'noovo': {
        'resolver': '/resources/lib/channels/ca/noovo:get_live_url',
        'label': 'Noovo',
        'thumb': 'channels/ca/noovo.png',
        'fanart': 'channels/ca/noovo_fanart.jpg',
        'enabled': True,
        'order': 10
    },
    'cbc': {
        'resolver': '/resources/lib/channels/ca/cbc:get_live_url',
        'label': 'CBC',
        'thumb': 'channels/ca/cbc.png',
        'fanart': 'channels/ca/cbc_fanart.jpg',
        'available_languages': {
            'Ottawa': {}, 'Montreal': {}, 'Charlottetown': {}, 'Fredericton': {},
            'Halifax': {}, 'Windsor': {}, 'Yellowknife': {}, 'Winnipeg': {},
            'Regina': {}, 'Calgary': {}, 'Edmonton': {}, 'Vancouver': {},
            'Toronto': {}, 'St. John\'s': {}
        },
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
