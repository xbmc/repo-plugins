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

menu = {
    'blaze': {
        'callback': 'replay_bridge',
        'thumb': 'channels/uk/blaze.png',
        'fanart': 'channels/uk/blaze_fanart.jpg',
        'module': 'resources.lib.channels.uk.blaze',
        'enabled': True,
        'order': 1
    },
    'skynews': {
        'callback': 'replay_bridge',
        'thumb': 'channels/uk/skynews.png',
        'fanart': 'channels/uk/skynews_fanart.jpg',
        'module': 'resources.lib.channels.uk.sky',
        'enabled': True,
        'order': 6
    },
    'skysports': {
        'callback': 'replay_bridge',
        'thumb': 'channels/uk/skysports.png',
        'fanart': 'channels/uk/skysports_fanart.jpg',
        'module': 'resources.lib.channels.uk.sky',
        'enabled': True,
        'order': 7
    },
    'stv': {
        'callback': 'replay_bridge',
        'thumb': 'channels/uk/stv.png',
        'fanart': 'channels/uk/stv_fanart.jpg',
        'module': 'resources.lib.channels.uk.stv',
        'enabled': True,
        'order': 8
    },
    'questod': {
        'callback': 'replay_bridge',
        'thumb': 'channels/uk/questod.png',
        'fanart': 'channels/uk/questod_fanart.jpg',
        'module': 'resources.lib.channels.uk.questod',
        'enabled': True,
        'order': 9
    },
    'uktvplay': {
        'callback': 'replay_bridge',
        'thumb': 'channels/uk/uktvplay.png',
        'fanart': 'channels/uk/uktvplay_fanart.jpg',
        'module': 'resources.lib.channels.uk.uktvplay',
        'enabled': True,
        'order': 17
    },
    'fiveusa': {
        'callback': 'replay_bridge',
        'thumb': 'channels/uk/fiveusa.png',
        'fanart': 'channels/uk/fiveusa_fanart.jpg',
        'module': 'resources.lib.channels.uk.my5',
        'enabled': False,
        'order': 20
    },
    'bristoltv': {
        'callback': 'replay_bridge',
        'thumb': 'channels/uk/bristoltv.png',
        'fanart': 'channels/uk/bristoltv_fanart.jpg',
        'module': 'resources.lib.channels.uk.bristoltv',
        'enabled': True,
        'order': 21
    }
}
