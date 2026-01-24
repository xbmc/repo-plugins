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
    'wo_live': {
        'route': '/resources/lib/main:tv_guide_menu'
        if TV_GUIDE else '/resources/lib/main:generic_menu',
        'label': 30053,
        'thumb': 'channels/wo.png',
        'enabled': True,
        'order': 1
    },
    'fr_live': {
        'route': '/resources/lib/main:tv_guide_menu'
        if TV_GUIDE else '/resources/lib/main:generic_menu',
        'label': 30050,
        'thumb': 'channels/fr.png',
        'enabled': True,
        'order': 2
    },
    'ch_live': {
        'route': '/resources/lib/main:tv_guide_menu'
        if TV_GUIDE else '/resources/lib/main:generic_menu',
        'label': 30051,
        'thumb': 'channels/ch.png',
        'enabled': True,
        'order': 3
    },
    'be_live': {
        'route': '/resources/lib/main:tv_guide_menu'
        if TV_GUIDE else '/resources/lib/main:generic_menu',
        'label': 30054,
        'thumb': 'channels/be.png',
        'enabled': True,
        'order': 4
    },
    'lu_live': {
        'route': '/resources/lib/main:tv_guide_menu',
        'label': 30075,
        'thumb': 'channels/lu.png',
        'enabled': True,
        'order': 5
    },
    'uk_live': {
        'route': '/resources/lib/main:tv_guide_menu'
        if TV_GUIDE else '/resources/lib/main:generic_menu',
        'label': 30052,
        'thumb': 'channels/uk.png',
        'enabled': True,
        'order': 6
    },
    'ie_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30079,
        'thumb': 'channels/ie.png',
        'enabled': True,
        'order': 7
    },
    'es_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30059,
        'thumb': 'channels/es.png',
        'enabled': True,
        'order': 8
    },
    'it_live': {
        'route': '/resources/lib/main:tv_guide_menu'
        if TV_GUIDE else '/resources/lib/main:generic_menu',
        'label': 30061,
        'thumb': 'channels/it.png',
        'enabled': True,
        'order': 9
    },
    'nl_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30062,
        'thumb': 'channels/nl.png',
        'enabled': True,
        'order': 10
    },
    'gr_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30072,
        'thumb': 'channels/gr.png',
        'enabled': True,
        'order': 11
    },
    'pl_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30058,
        'thumb': 'channels/pl.png',
        'enabled': True,
        'order': 12
    },
    'sk_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30071,
        'thumb': 'channels/sk.png',
        'enabled': True,
        'order': 13
    },
    'si_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30065,
        'thumb': 'channels/si.png',
        'enabled': True,
        'order': 14
    },
    'lt_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30069,
        'thumb': 'channels/lt.png',
        'enabled': True,
        'order': 15
    },
    'mk_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30078,
        'thumb': 'channels/mk.png',
        'enabled': True,
        'order': 16
    },
    'ca_live': {
        'route': '/resources/lib/main:tv_guide_menu'
        if TV_GUIDE else '/resources/lib/main:generic_menu',
        'label': 30056,
        'thumb': 'channels/ca.png',
        'enabled': True,
        'order': 17
    },
    'us_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30057,
        'thumb': 'channels/us.png',
        'enabled': True,
        'order': 18
    },
    'jp_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30055,
        'thumb': 'channels/jp.png',
        'enabled': True,
        'order': 19
    },
    'cn_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30063,
        'thumb': 'channels/cn.png',
        'enabled': True,
        'order': 20
    },
    'sg_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30068,
        'thumb': 'channels/sg.png',
        'enabled': True,
        'order': 21
    },
    'tr_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30070,
        'thumb': 'channels/tr.png',
        'enabled': True,
        'order': 22
    },
    'ma_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30067,
        'thumb': 'channels/ma.png',
        'enabled': True,
        'order': 23
    },
    'tn_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30060,
        'thumb': 'channels/tn.png',
        'enabled': True,
        'order': 24
    },
    'cm_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30064,
        'thumb': 'channels/cm.png',
        'enabled': True,
        'order': 25
    },
    'et_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30066,
        'thumb': 'channels/et.png',
        'enabled': True,
        'order': 26
    },
    'bo_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30076,
        'thumb': 'channels/bo.png',
        'enabled': True,
        'order': 27
    },
    'pe_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30073,
        'thumb': 'channels/pe.png',
        'enabled': True,
        'order': 28
    },
    've_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30074,
        'thumb': 'channels/ve.png',
        'enabled': True,
        'order': 29
    },
    'sa_live': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30077,
        'thumb': 'channels/sa.png',
        'enabled': True,
        'order': 30
    }
}
