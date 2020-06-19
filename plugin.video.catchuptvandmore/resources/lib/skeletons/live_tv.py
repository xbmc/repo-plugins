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

TV_GUIDE = Script.setting.get_boolean('tv_guide')

menu = {
    'fr_live': {
        'callback': 'tv_guide_menu'
        if TV_GUIDE else 'generic_menu',
        'label': 30050,
        'thumb': 'channels/fr.png',
        'enabled': True,
        'order': 1
    },
    'ch_live': {
        'callback': 'generic_menu',
        'label': 30051,
        'thumb': 'channels/ch.png',
        'enabled': True,
        'order': 2
    },
    'uk_live': {
        'callback': 'tv_guide_menu'
        if TV_GUIDE else 'generic_menu',
        'label': 30052,
        'thumb': 'channels/uk.png',
        'enabled': True,
        'order': 3
    },
    'wo_live': {
        'callback': 'generic_menu',
        'label': 30053,
        'thumb': 'channels/wo.png',
        'enabled': True,
        'order': 4
    },
    'be_live': {
        'callback': 'tv_guide_menu'
        if TV_GUIDE else 'generic_menu',
        'label': 30054,
        'thumb': 'channels/be.png',
        'enabled': True,
        'order': 5
    },
    'jp_live': {
        'callback': 'generic_menu',
        'label': 30055,
        'thumb': 'channels/jp.png',
        'enabled': True,
        'order': 6
    },
    'ca_live': {
        'callback': 'generic_menu',
        'label': 30056,
        'thumb': 'channels/ca.png',
        'enabled': True,
        'order': 7
    },
    'us_live': {
        'callback': 'generic_menu',
        'label': 30057,
        'thumb': 'channels/us.png',
        'enabled': True,
        'order': 8
    },
    'pl_live': {
        'callback': 'generic_menu',
        'label': 30058,
        'thumb': 'channels/pl.png',
        'enabled': True,
        'order': 9
    },
    'es_live': {
        'callback': 'generic_menu',
        'label': 30059,
        'thumb': 'channels/es.png',
        'enabled': True,
        'order': 10
    },
    'tn_live': {
        'callback': 'generic_menu',
        'label': 30060,
        'thumb': 'channels/tn.png',
        'enabled': True,
        'order': 11
    },
    'it_live': {
        'callback': 'tv_guide_menu'
        if TV_GUIDE else 'generic_menu',
        'label': 30061,
        'thumb': 'channels/it.png',
        'enabled': True,
        'order': 12
    },
    'nl_live': {
        'callback': 'generic_menu',
        'label': 30062,
        'thumb': 'channels/nl.png',
        'enabled': True,
        'order': 13
    },
    'cn_live': {
        'callback': 'generic_menu',
        'label': 30063,
        'thumb': 'channels/cn.png',
        'enabled': True,
        'order': 14
    },
    'cm_live': {
        'callback': 'generic_menu',
        'label': 30064,
        'thumb': 'channels/cm.png',
        'enabled': True,
        'order': 15
    },
    'si_live': {
        'callback': 'generic_menu',
        'label': 30065,
        'thumb': 'channels/si.png',
        'enabled': True,
        'order': 16
    },
    'et_live': {
        'callback': 'generic_menu',
        'label': 30066,
        'thumb': 'channels/et.png',
        'enabled': True,
        'order': 17
    }
}
