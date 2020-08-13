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
    'blaze': {
        'route': '/resources/lib/channels/uk/blaze:list_categories',
        'label': 'Blaze',
        'thumb': 'channels/uk/blaze.png',
        'fanart': 'channels/uk/blaze_fanart.jpg',
        'enabled': True,
        'order': 1
    },
    'skynews': {
        'route': '/resources/lib/channels/uk/sky:list_categories',
        'label': 'Sky News',
        'thumb': 'channels/uk/skynews.png',
        'fanart': 'channels/uk/skynews_fanart.jpg',
        'enabled': True,
        'order': 6
    },
    'skysports': {
        'route': '/resources/lib/channels/uk/sky:list_categories',
        'label': 'Sky Sports',
        'thumb': 'channels/uk/skysports.png',
        'fanart': 'channels/uk/skysports_fanart.jpg',
        'enabled': True,
        'order': 7
    },
    'stv': {
        'route': '/resources/lib/channels/uk/stv:list_programs',
        'label': 'STV',
        'thumb': 'channels/uk/stv.png',
        'fanart': 'channels/uk/stv_fanart.jpg',
        'enabled': True,
        'order': 8
    },
    'questod': {
        'route': '/resources/lib/channels/uk/questod:list_categories',
        'label': 'Quest OD',
        'thumb': 'channels/uk/questod.png',
        'fanart': 'channels/uk/questod_fanart.jpg',
        'enabled': True,
        'order': 9
    },
    'uktvplay': {
        'route': '/resources/lib/channels/uk/uktvplay:list_categories',
        'label': 'UKTV Play',
        'thumb': 'channels/uk/uktvplay.png',
        'fanart': 'channels/uk/uktvplay_fanart.jpg',
        'enabled': True,
        'order': 17
    },
    'fiveusa': {
        'route': '/resources/lib/channels/uk/my5:list_programs',
        'label': '5USA',
        'thumb': 'channels/uk/fiveusa.png',
        'fanart': 'channels/uk/fiveusa_fanart.jpg',
        'enabled': False,
        'order': 20
    },
    'bristoltv': {
        'route': '/resources/lib/channels/uk/bristoltv:list_categories',
        'label': 'Bristol TV',
        'thumb': 'channels/uk/bristoltv.png',
        'fanart': 'channels/uk/bristoltv_fanart.jpg',
        'enabled': True,
        'order': 21
    }
}
