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
    'be_replay': {
        'callback': 'generic_menu',
        'thumb': 'channels/be.png'
    },
    'ca_replay': {
        'callback': 'generic_menu',
        'thumb': 'channels/ca.png'
    },
    'fr_replay': {
        'callback': 'generic_menu',
        'thumb': 'channels/fr.png'
    },
    'jp_replay': {
        'callback': 'generic_menu',
        'thumb': 'channels/jp.png'
    },
    'ch_replay': {
        'callback': 'generic_menu',
        'thumb': 'channels/ch.png'
    },
    'uk_replay': {
        'callback': 'generic_menu',
        'thumb': 'channels/uk.png'
    },
    'wo_replay': {
        'callback': 'generic_menu',
        'thumb': 'channels/wo.png'
    },
    'us_replay': {
        'callback': 'generic_menu',
        'thumb': 'channels/us.png'
    },
    # ,
    # 'es_replay': {
    #    'callback': 'generic_menu',
    #    'thumb': 'channels/es.png'
    # }
    'it_replay': {
        'callback': 'generic_menu',
        'thumb': 'channels/it.png'
    },
    'tn_replay': {
        'callback': 'generic_menu',
        'thumb': 'channels/tn.png'
    },
    'nl_replay': {
        'callback': 'generic_menu',
        'thumb': 'channels/nl.png'
    }
}
