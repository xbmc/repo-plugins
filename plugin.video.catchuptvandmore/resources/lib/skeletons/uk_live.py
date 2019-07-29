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
        'callback': 'live_bridge',
        'thumb': 'channels/uk/blaze.png',
        'fanart': 'channels/uk/blaze_fanart.jpg',
        'module': 'resources.lib.channels.uk.blaze'
    },
    'skynews': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/skynews.png',
        'fanart': 'channels/uk/skynews_fanart.jpg',
        'module': 'resources.lib.channels.uk.sky'
    },
    'stv': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/stv.png',
        'fanart': 'channels/uk/stv_fanart.jpg',
        'module': 'resources.lib.channels.uk.stv'
    },
    'kerrang': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/kerrang.png',
        'fanart': 'channels/uk/kerrang_fanart.jpg',
        'module': 'resources.lib.channels.uk.boxplus'
    },
    'magic': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/magic.png',
        'fanart': 'channels/uk/magic_fanart.jpg',
        'module': 'resources.lib.channels.uk.boxplus'
    },
    'kiss': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/kiss.png',
        'fanart': 'channels/uk/kiss_fanart.jpg',
        'module': 'resources.lib.channels.uk.boxplus'
    },
    'the-box': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/thebox.png',
        'fanart': 'channels/uk/thebox_fanart.jpg',
        'module': 'resources.lib.channels.uk.boxplus'
    },
    'box-upfront': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/boxupfront.png',
        'fanart': 'channels/uk/boxupfront_fanart.jpg',
        'module': 'resources.lib.channels.uk.boxplus'
    },
    'box-hits': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/boxhits.png',
        'fanart': 'channels/uk/boxhits_fanart.jpg',
        'module': 'resources.lib.channels.uk.boxplus'
    },
    'questtv': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/questtv.png',
        'fanart': 'channels/uk/questtv_fanart.jpg',
        'module': 'resources.lib.channels.uk.questod'
    },
    'questred': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/questred.png',
        'fanart': 'channels/uk/questred_fanart.jpg',
        'module': 'resources.lib.channels.uk.questod'
    },
    'bristoltv': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/bristoltv.png',
        'fanart': 'channels/uk/bristoltv_fanart.jpg',
        'module': 'resources.lib.channels.uk.bristoltv'
    },
    'drama': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/drama.png',
        'fanart': 'channels/uk/drama_fanart.jpg',
        'module': 'resources.lib.channels.uk.uktvplay'
    },
    'dave': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/dave.png',
        'fanart': 'channels/uk/dave_fanart.jpg',
        'module': 'resources.lib.channels.uk.uktvplay'
    },
    'really': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/really.png',
        'fanart': 'channels/uk/really_fanart.jpg',
        'module': 'resources.lib.channels.uk.uktvplay'
    },
    'yesterday': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/yesterday.png',
        'fanart': 'channels/uk/yesterday_fanart.jpg',
        'module': 'resources.lib.channels.uk.uktvplay'
    },
    'home_uktvplay': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/home.png',
        'fanart': 'channels/uk/home_fanart.jpg',
        'module': 'resources.lib.channels.uk.uktvplay'
    }
}
