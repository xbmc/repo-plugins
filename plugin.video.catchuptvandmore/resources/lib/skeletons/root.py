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
    - route (folder)/resolver (playable URL): Callback function to run once this item is selected
    - thumb: Item thumb path relative to "media" folder
    - fanart: Item fanart path relative to "meia" folder
"""

root = None

menu = {
    'live_tv': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30030,
        'thumb': 'live_tv.png',
        'enabled': True,
        'order': 1
    },
    'replay': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30031,
        'thumb': 'replay.png',
        'enabled': True,
        'order': 2
    },
    'websites': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30032,
        'thumb': 'websites.png',
        'enabled': True,
        'order': 3
    },
    'favourites': {
        'route': '/resources/lib/main:favourites',
        'label': 30033,
        'thumb': 'favourites.png',
        'enabled': True,
        'order': 4
    }
}
