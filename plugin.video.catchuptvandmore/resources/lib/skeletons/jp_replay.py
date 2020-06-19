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
    'nhknews': {
        'callback': 'replay_bridge',
        'label': 'NHK ニュース',
        'thumb': 'channels/jp/nhknews.png',
        'fanart': 'channels/jp/nhknews_fanart.jpg',
        'module': 'resources.lib.channels.jp.nhknews',
        'enabled': True,
        'order': 1
    },
    'nhklifestyle': {
        'callback': 'replay_bridge',
        'label': 'NHKらいふ',
        'thumb': 'channels/jp/nhklifestyle.png',
        'fanart': 'channels/jp/nhklifestyle_fanart.jpg',
        'module': 'resources.lib.channels.jp.nhklifestyle',
        'enabled': True,
        'order': 2
    },
    'tbsnews': {
        'callback': 'replay_bridge',
        'label': 'TBS ニュース',
        'thumb': 'channels/jp/tbsnews.png',
        'fanart': 'channels/jp/tbsnews_fanart.jpg',
        'module': 'resources.lib.channels.jp.tbsnews',
        'enabled': True,
        'order': 3
    },
    'ex': {
        'callback': 'replay_bridge',
        'label': 'テレビ朝日',
        'thumb': 'channels/jp/ex.png',
        'fanart': 'channels/jp/ex_fanart.jpg',
        'module': 'resources.lib.channels.jp.tver',
        'enabled': True,
        'order': 5
    },
    'tbs': {
        'callback': 'replay_bridge',
        'label': 'TBSテレビ',
        'thumb': 'channels/jp/tbs.png',
        'fanart': 'channels/jp/tbs_fanart.jpg',
        'module': 'resources.lib.channels.jp.tver',
        'enabled': True,
        'order': 6
    },
    'tx': {
        'callback': 'replay_bridge',
        'label': 'テレビ東京',
        'thumb': 'channels/jp/tx.png',
        'fanart': 'channels/jp/tx_fanart.jpg',
        'module': 'resources.lib.channels.jp.tver',
        'enabled': True,
        'order': 7
    },
    'mbs': {
        'callback': 'replay_bridge',
        'label': 'MBSテレビ',
        'thumb': 'channels/jp/mbs.png',
        'fanart': 'channels/jp/mbs_fanart.jpg',
        'module': 'resources.lib.channels.jp.tver',
        'enabled': True,
        'order': 8
    },
    'abc': {
        'callback': 'replay_bridge',
        'label': '朝日放送株式会社',
        'thumb': 'channels/jp/abc.png',
        'fanart': 'channels/jp/abc_fanart.jpg',
        'module': 'resources.lib.channels.jp.tver',
        'enabled': True,
        'order': 9
    },
    'ytv': {
        'callback': 'replay_bridge',
        'label': '読売テレビ',
        'thumb': 'channels/jp/ytv.png',
        'fanart': 'channels/jp/ytv_fanart.jpg',
        'module': 'resources.lib.channels.jp.tver',
        'enabled': True,
        'order': 10
    },
    'ntv': {
        'callback': 'replay_bridge',
        'label': '日テレ',
        'thumb': 'channels/jp/ntv.png',
        'fanart': 'channels/jp/ntv_fanart.jpg',
        'module': 'resources.lib.channels.jp.tver',
        'enabled': True,
        'order': 11
    },
    'ktv': {
        'callback': 'replay_bridge',
        'label': '関西テレビ',
        'thumb': 'channels/jp/ktv.png',
        'fanart': 'channels/jp/ktv_fanart.jpg',
        'module': 'resources.lib.channels.jp.tver',
        'enabled': True,
        'order': 13
    },
    'tvo': {
        'callback': 'replay_bridge',
        'label': 'テレビ大阪株式会社',
        'thumb': 'channels/jp/tvo.png',
        'fanart': 'channels/jp/tvo_fanart.jpg',
        'module': 'resources.lib.channels.jp.tver',
        'enabled': True,
        'order': 15
    },
    'nhk': {
        'callback': 'replay_bridge',
        'label': 'NHK',
        'thumb': 'channels/jp/nhk.png',
        'fanart': 'channels/jp/nhk_fanart.jpg',
        'module': 'resources.lib.channels.jp.tver',
        'enabled': True,
        'order': 16
    }

}
