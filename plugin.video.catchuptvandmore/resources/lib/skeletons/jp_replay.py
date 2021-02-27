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
    'nhknews': {
        'route': '/resources/lib/channels/jp/nhknews:list_categories',
        'label': 'NHK ニュース',
        'thumb': 'channels/jp/nhknews.png',
        'fanart': 'channels/jp/nhknews_fanart.jpg',
        'enabled': True,
        'order': 1
    },
    'nhklifestyle': {
        'route': '/resources/lib/channels/jp/nhklifestyle:list_categories',
        'label': 'NHKらいふ',
        'thumb': 'channels/jp/nhklifestyle.png',
        'fanart': 'channels/jp/nhklifestyle_fanart.jpg',
        'enabled': True,
        'order': 2
    },
    'tbsnews': {
        'route': '/resources/lib/channels/jp/tbsnews:list_categories',
        'label': 'TBS ニュース',
        'thumb': 'channels/jp/tbsnews.png',
        'fanart': 'channels/jp/tbsnews_fanart.jpg',
        'enabled': True,
        'order': 3
    },
    'ex': {
        'route': '/resources/lib/channels/jp/tver:list_categories',
        'label': 'テレビ朝日',
        'thumb': 'channels/jp/ex.png',
        'fanart': 'channels/jp/ex_fanart.jpg',
        'enabled': True,
        'order': 5
    },
    'tbs': {
        'route': '/resources/lib/channels/jp/tver:list_categories',
        'label': 'TBSテレビ',
        'thumb': 'channels/jp/tbs.png',
        'fanart': 'channels/jp/tbs_fanart.jpg',
        'enabled': True,
        'order': 6
    },
    'tx': {
        'route': '/resources/lib/channels/jp/tver:list_categories',
        'label': 'テレビ東京',
        'thumb': 'channels/jp/tx.png',
        'fanart': 'channels/jp/tx_fanart.jpg',
        'enabled': True,
        'order': 7
    },
    'mbs': {
        'route': '/resources/lib/channels/jp/tver:list_categories',
        'label': 'MBSテレビ',
        'thumb': 'channels/jp/mbs.png',
        'fanart': 'channels/jp/mbs_fanart.jpg',
        'enabled': True,
        'order': 8
    },
    'abc': {
        'route': '/resources/lib/channels/jp/tver:list_categories',
        'label': '朝日放送株式会社',
        'thumb': 'channels/jp/abc.png',
        'fanart': 'channels/jp/abc_fanart.jpg',
        'enabled': True,
        'order': 9
    },
    'ytv': {
        'route': '/resources/lib/channels/jp/tver:list_categories',
        'label': '読売テレビ',
        'thumb': 'channels/jp/ytv.png',
        'fanart': 'channels/jp/ytv_fanart.jpg',
        'enabled': True,
        'order': 10
    },
    'ntv': {
        'route': '/resources/lib/channels/jp/tver:list_categories',
        'label': '日テレ',
        'thumb': 'channels/jp/ntv.png',
        'fanart': 'channels/jp/ntv_fanart.jpg',
        'enabled': True,
        'order': 11
    },
    'ktv': {
        'route': '/resources/lib/channels/jp/tver:list_categories',
        'label': '関西テレビ',
        'thumb': 'channels/jp/ktv.png',
        'fanart': 'channels/jp/ktv_fanart.jpg',
        'enabled': True,
        'order': 13
    },
    'tvo': {
        'route': '/resources/lib/channels/jp/tver:list_categories',
        'label': 'テレビ大阪株式会社',
        'thumb': 'channels/jp/tvo.png',
        'fanart': 'channels/jp/tvo_fanart.jpg',
        'enabled': True,
        'order': 15
    },
    'nhk': {
        'route': '/resources/lib/channels/jp/tver:list_categories',
        'label': 'NHK',
        'thumb': 'channels/jp/nhk.png',
        'fanart': 'channels/jp/nhk_fanart.jpg',
        'enabled': True,
        'order': 16
    }

}
