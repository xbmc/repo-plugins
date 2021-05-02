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

root = 'replay'

menu = {
    'la7': {
        'route': '/resources/lib/channels/it/la7:list_days',
        'label': 'La7',
        'thumb': 'channels/it/la7.png',
        'fanart': 'channels/it/la7_fanart.jpg',
        'enabled': True,
        'order': 1
    },
    'la7d': {
        'route': '/resources/lib/channels/it/la7:list_days',
        'label': 'La7d',
        'thumb': 'channels/it/la7d.png',
        'fanart': 'channels/it/la7d_fanart.jpg',
        'enabled': True,
        'order': 15
    },
    'raiplay': {
        'route': '/resources/lib/channels/it/raiplay:list_letters',
        'label': 'Rai Play',
        'thumb': 'channels/it/raiplay.png',
        'fanart': 'channels/it/raiplay_fanart.jpg',
        'enabled': True,
        'order': 16
    }
}
