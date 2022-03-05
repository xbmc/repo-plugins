# -*- coding: utf-8 -*-
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from codequick import Script

# The following dictionaries describe
# the addon's tree architecture.
# * Key: item id
# * Value: item infos
#     - route (folder)/resolver (playable URL): Callback function to run once this item is selected
#     - thumb: Item thumb path relative to "media" folder
#     - fanart: Item fanart path relative to "media" folder

TV_GUIDE = Script.setting.get_boolean('tv_guide')

root = 'root'

menu = {
    'fr_live': {
        'route': '/resources/lib/main:tv_guide_menu'
        if TV_GUIDE else '/resources/lib/main:generic_menu',
        'label': 30050,
        'thumb': 'channels/fr.png',
        'enabled': True,
        'order': 1
    },
    'ch_live': {
        'route': '/resources/lib/main:tv_guide_menu'
        if TV_GUIDE else '/resources/lib/main:generic_menu',
        'label': 30051,
        'thumb': 'channels/ch.png',
        'enabled': True,
        'order': 2
    },
    'uk_live': {
        'route': '/resources/lib/main:tv_guide_menu'
        if TV_GUIDE else '/resources/lib/main:generic_menu',
        'label': 30052,
        'thumb': 'channels/uk.png',
        'enabled': True,
        'order': 3
    },
    'wo_live': {
        'route': '/resources/lib/main:tv_guide_menu'
        if TV_GUIDE else '/resources/lib/main:generic_menu',
        'label': 30053,
        'thumb': 'channels/wo.png',
        'enabled': True,
        'order': 4
    },
    'be_live': {
        'route': '/resources/lib/main:tv_guide_menu'
        if TV_GUIDE else '/resources/lib/main:generic_menu',
        'label': 30054,
        'thumb': 'channels/be.png',
        'enabled': True,
        'order': 5
    },
    'jp_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30055,
        'thumb': 'channels/jp.png',
        'enabled': True,
        'order': 6
    },
    'ca_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30056,
        'thumb': 'channels/ca.png',
        'enabled': True,
        'order': 7
    },
    'us_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30057,
        'thumb': 'channels/us.png',
        'enabled': True,
        'order': 8
    },
    'pl_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30058,
        'thumb': 'channels/pl.png',
        'enabled': True,
        'order': 9
    },
    'es_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30059,
        'thumb': 'channels/es.png',
        'enabled': True,
        'order': 10
    },
    'tn_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30060,
        'thumb': 'channels/tn.png',
        'enabled': True,
        'order': 11
    },
    'it_live': {
        'route': '/resources/lib/main:tv_guide_menu'
        if TV_GUIDE else '/resources/lib/main:generic_menu',
        'label': 30061,
        'thumb': 'channels/it.png',
        'enabled': True,
        'order': 12
    },
    'nl_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30062,
        'thumb': 'channels/nl.png',
        'enabled': True,
        'order': 13
    },
    'cn_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30063,
        'thumb': 'channels/cn.png',
        'enabled': True,
        'order': 14
    },
    'cm_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30064,
        'thumb': 'channels/cm.png',
        'enabled': True,
        'order': 15
    },
    'si_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30065,
        'thumb': 'channels/si.png',
        'enabled': True,
        'order': 16
    },
    'et_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30066,
        'thumb': 'channels/et.png',
        'enabled': True,
        'order': 17
    },
    'ma_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30067,
        'thumb': 'channels/ma.png',
        'enabled': True,
        'order': 18
    },
    'sg_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30068,
        'thumb': 'channels/sg.png',
        'enabled': True,
        'order': 19
    },
    'lt_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30069,
        'thumb': 'channels/lt.png',
        'enabled': True,
        'order': 20
    }
}
