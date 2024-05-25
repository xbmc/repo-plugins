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

root = 'root'

menu = {
    'wo_replay': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30053,
        'thumb': 'channels/wo.png',
        'enabled': True,
        'order': 1
    },
    'fr_replay': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30050,
        'thumb': 'channels/fr.png',
        'enabled': True,
        'order': 2
    },
    'ch_replay': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30051,
        'thumb': 'channels/ch.png',
        'enabled': True,
        'order': 3
    },
    'uk_replay': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30052,
        'thumb': 'channels/uk.png',
        'enabled': True,
        'order': 4
    },
    'be_replay': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30054,
        'thumb': 'channels/be.png',
        'enabled': True,
        'order': 5
    },
    'pl_replay': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30058,
        'thumb': 'channels/pl.png',
        'enabled': True,
        'order': 6
    },
    'es_replay': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30059,
        'thumb': 'channels/es.png',
        'enabled': False,
        'order': 7
    },
    'it_replay': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30061,
        'thumb': 'channels/it.png',
        'enabled': True,
        'order': 8
    },
    'nl_replay': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30062,
        'thumb': 'channels/nl.png',
        'enabled': True,
        'order': 9
    },
    'ca_replay': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30056,
        'thumb': 'channels/ca.png',
        'enabled': True,
        'order': 10
    },
    'us_replay': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30057,
        'thumb': 'channels/us.png',
        'enabled': True,
        'order': 11
    },
    'jp_replay': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30055,
        'thumb': 'channels/jp.png',
        'enabled': True,
        'order': 12
    },
    'cn_replay': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30063,
        'thumb': 'channels/nl.png',
        'enabled': False,
        'order': 13
    },
    'tn_replay': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30060,
        'thumb': 'channels/tn.png',
        'enabled': True,
        'order': 14
    },
    'cm_replay': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30064,
        'thumb': 'channels/cm.png',
        'enabled': False,
        'order': 15
    }
}
