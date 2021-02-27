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

root = 'live_tv'

menu = {
    'cbsnews': {
        'resolver': '/resources/lib/channels/us/cbsnews:get_live_url',
        'label': 'CBS News',
        'thumb': 'channels/us/cbsnews.png',
        'fanart': 'channels/us/cbsnews_fanart.jpg',
        'enabled': True,
        'order': 1
    },
    'tbd': {
        'resolver': '/resources/lib/channels/us/tbd:get_live_url',
        'label': 'TBD',
        'thumb': 'channels/us/tbd.png',
        'fanart': 'channels/us/tbd_fanart.jpg',
        'enabled': True,
        'order': 2
    },
    'abcnews': {
        'resolver': '/resources/lib/channels/us/abcnews:get_live_url',
        'label': 'ABC News',
        'thumb': 'channels/us/abcnews.png',
        'fanart': 'channels/us/abcnews_fanart.jpg',
        'enabled': True,
        'order': 4
    },
    'pbskids': {
        'resolver': '/resources/lib/channels/us/pbskids:get_live_url',
        'label': 'PBS Kids',
        'thumb': 'channels/us/pbskids.png',
        'fanart': 'channels/us/pbskids_fanart.jpg',
        'enabled': True,
        'order': 5
    }
}
