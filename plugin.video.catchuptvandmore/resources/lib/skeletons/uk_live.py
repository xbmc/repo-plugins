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
        'module': 'resources.lib.channels.uk.blaze',
        'xmltv_id': '1013.tvguide.co.uk',
        'enabled': True,
        'order': 1
    },
    'dave': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/dave.png',
        'fanart': 'channels/uk/dave_fanart.jpg',
        'module': 'resources.lib.channels.uk.uktvplay',
        'xmltv_id': '432.tvguide.co.uk',
        'enabled': True,
        'order': 2
    },
    'yesterday': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/yesterday.png',
        'fanart': 'channels/uk/yesterday_fanart.jpg',
        'module': 'resources.lib.channels.uk.uktvplay',
        'xmltv_id': '320.tvguide.co.uk',
        'enabled': True,
        'order': 4
    },
    'drama': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/drama.png',
        'fanart': 'channels/uk/drama_fanart.jpg',
        'module': 'resources.lib.channels.uk.uktvplay',
        'xmltv_id': '871.tvguide.co.uk',
        'enabled': True,
        'order': 5
    },
    'skynews': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/skynews.png',
        'fanart': 'channels/uk/skynews_fanart.jpg',
        'module': 'resources.lib.channels.uk.sky',
        'xmltv_id': '257.tvguide.co.uk',
        'enabled': True,
        'order': 6
    },
    'stv': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/stv.png',
        'fanart': 'channels/uk/stv_fanart.jpg',
        'module': 'resources.lib.channels.uk.stv',
        'xmltv_id': '178.tvguide.co.uk',
        'enabled': True,
        'order': 8
    },
    'kerrang': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/kerrang.png',
        'fanart': 'channels/uk/kerrang_fanart.jpg',
        'module': 'resources.lib.channels.uk.boxplus',
        'xmltv_id': '1207.tvguide.co.uk',
        'enabled': True,
        'order': 11
    },
    'magic': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/magic.png',
        'fanart': 'channels/uk/magic_fanart.jpg',
        'module': 'resources.lib.channels.uk.boxplus',
        'xmltv_id': '185.tvguide.co.uk',
        'enabled': True,
        'order': 12
    },
    'kiss': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/kiss.png',
        'fanart': 'channels/uk/kiss_fanart.jpg',
        'module': 'resources.lib.channels.uk.boxplus',
        'xmltv_id': '182.tvguide.co.uk',
        'enabled': True,
        'order': 13
    },
    'the-box': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/thebox.png',
        'fanart': 'channels/uk/thebox_fanart.jpg',
        'module': 'resources.lib.channels.uk.boxplus',
        'xmltv_id': '279.tvguide.co.uk',
        'enabled': True,
        'order': 14
    },
    'box-hits': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/boxhits.png',
        'fanart': 'channels/uk/boxhits_fanart.jpg',
        'module': 'resources.lib.channels.uk.boxplus',
        'xmltv_id': '267.tvguide.co.uk',
        'enabled': True,
        'order': 15
    },
    'box-upfront': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/boxupfront.png',
        'fanart': 'channels/uk/boxupfront_fanart.jpg',
        'module': 'resources.lib.channels.uk.boxplus',
        'enabled': True,
        'order': 16
    },
    'questtv': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/questtv.png',
        'fanart': 'channels/uk/questtv_fanart.jpg',
        'module': 'resources.lib.channels.uk.questod',
        'xmltv_id': '1230.tvguide.co.uk',
        'enabled': True,
        'order': 18
    },
    'questred': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/questred.png',
        'fanart': 'channels/uk/questred_fanart.jpg',
        'module': 'resources.lib.channels.uk.questod',
        'xmltv_id': '1014.tvguide.co.uk',
        'enabled': True,
        'order': 19
    },
    'bristoltv': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/bristoltv.png',
        'fanart': 'channels/uk/bristoltv_fanart.jpg',
        'module': 'resources.lib.channels.uk.bristoltv',
        'enabled': True,
        'order': 21
    },
    'freesports': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/freesports.png',
        'fanart': 'channels/uk/freesports_fanart.jpg',
        'module': 'resources.lib.channels.uk.stv',
        'enabled': True,
        'order': 23
    },
    'stv_plusone': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/stv_plusone.png',
        'fanart': 'channels/uk/stv_plusone_fanart.jpg',
        'module': 'resources.lib.channels.uk.stv',
        'enabled': True,
        'order': 24
    },
    'edgesport': {
        'callback': 'live_bridge',
        'thumb': 'channels/uk/edgesport.png',
        'fanart': 'channels/uk/edgesport_fanart.jpg',
        'module': 'resources.lib.channels.uk.stv',
        'enabled': True,
        'order': 25
    }
}
