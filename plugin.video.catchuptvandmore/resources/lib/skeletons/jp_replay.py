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
    'tbsnews': {
        'callback': 'replay_bridge',
        'thumb': 'channels/jp/tbsnews.png',
        'fanart': 'channels/jp/tbsnews_fanart.jpg',
        'module': 'resources.lib.channels.jp.tbsnews'
    },
    'ntv': {
        'callback': 'replay_bridge',
        'thumb': 'channels/jp/ntv.png',
        'fanart': 'channels/jp/ntv_fanart.jpg',
        'module': 'resources.lib.channels.jp.tver'
    },
    'ex': {
        'callback': 'replay_bridge',
        'thumb': 'channels/jp/ex.png',
        'fanart': 'channels/jp/ex_fanart.jpg',
        'module': 'resources.lib.channels.jp.tver'
    },
    'tbs': {
        'callback': 'replay_bridge',
        'thumb': 'channels/jp/tbs.png',
        'fanart': 'channels/jp/tbs_fanart.jpg',
        'module': 'resources.lib.channels.jp.tver'
    },
    'tx': {
        'callback': 'replay_bridge',
        'thumb': 'channels/jp/tx.png',
        'fanart': 'channels/jp/tx_fanart.jpg',
        'module': 'resources.lib.channels.jp.tver'
    },
    'mbs': {
        'callback': 'replay_bridge',
        'thumb': 'channels/jp/mbs.png',
        'fanart': 'channels/jp/mbs_fanart.jpg',
        'module': 'resources.lib.channels.jp.tver'
    },
    'abc': {
        'callback': 'replay_bridge',
        'thumb': 'channels/jp/abc.png',
        'fanart': 'channels/jp/abc_fanart.jpg',
        'module': 'resources.lib.channels.jp.tver'
    },
    'ytv': {
        'callback': 'replay_bridge',
        'thumb': 'channels/jp/ytv.png',
        'fanart': 'channels/jp/ytv_fanart.jpg',
        'module': 'resources.lib.channels.jp.tver'
    },
    'nhknews': {
        'callback': 'replay_bridge',
        'thumb': 'channels/jp/nhknews.png',
        'fanart': 'channels/jp/nhknews_fanart.jpg',
        'module': 'resources.lib.channels.jp.nhknews'
    },
    'nhklifestyle': {
        'callback': 'replay_bridge',
        'thumb': 'channels/jp/nhklifestyle.png',
        'fanart': 'channels/jp/nhklifestyle_fanart.jpg',
        'module': 'resources.lib.channels.jp.nhklifestyle'
    },
    'ktv': {
        'callback': 'replay_bridge',
        'thumb': 'channels/jp/ktv.png',
        'fanart': 'channels/jp/ktv_fanart.jpg',
        'module': 'resources.lib.channels.jp.tver'
    }
}
