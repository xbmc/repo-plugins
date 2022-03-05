# -*- coding: utf-8 -*-
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

# The following dictionaries describe
# the addon's tree architecture.
# * Key: item id
# * Value: item infos
#     - route (folder)/resolver (playable URL): Callback function to run once this item is selected
#     - thumb: Item thumb path relative to "media" folder
#     - fanart: Item fanart path relative to "media" folder

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
    'cx': {
        'route': '/resources/lib/channels/jp/tver:list_categories',
        'label': 'Fuji TV フジテレビ',
        'thumb': 'channels/jp/cx.png',
        'fanart': 'channels/jp/cx_fanart.jpg',
        'enabled': True,
        'order': 4
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
