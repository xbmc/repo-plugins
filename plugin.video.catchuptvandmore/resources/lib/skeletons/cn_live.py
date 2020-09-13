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

menu = {
    'cctv1': {
        'resolver': '/resources/lib/channels/cn/cctv:get_live_url',
        'label': 'CCTV-1 综合',
        'thumb': 'channels/cn/cctv1.png',
        'fanart': 'channels/cn/cctv1_fanart.jpg',
        'enabled': True,
        'order': 1
    },
    'cctv2': {
        'resolver': '/resources/lib/channels/cn/cctv:get_live_url',
        'label': 'CCTV-2 财经',
        'thumb': 'channels/cn/cctv2.png',
        'fanart': 'channels/cn/cctv2_fanart.jpg',
        'enabled': True,
        'order': 2
    },
    'cctv3': {
        'resolver': '/resources/lib/channels/cn/cctv:get_live_url',
        'label': 'CCTV-3 综艺',
        'thumb': 'channels/cn/cctv3.png',
        'fanart': 'channels/cn/cctv3_fanart.jpg',
        'enabled': True,
        'order': 3
    },
    'cctv4': {
        'resolver': '/resources/lib/channels/cn/cctv:get_live_url',
        'label': 'CCTV-4 中文国际（亚）',
        'thumb': 'channels/cn/cctv4.png',
        'fanart': 'channels/cn/cctv4_fanart.jpg',
        'enabled': True,
        'order': 4
    },
    'cctveurope': {
        'resolver': '/resources/lib/channels/cn/cctv:get_live_url',
        'label': 'CCTV-4 中文国际（欧）',
        'thumb': 'channels/cn/cctveurope.png',
        'fanart': 'channels/cn/cctveurope_fanart.jpg',
        'enabled': True,
        'order': 5
    },
    'cctvamerica': {
        'resolver': '/resources/lib/channels/cn/cctv:get_live_url',
        'label': 'CCTV-4 中文国际（美）',
        'thumb': 'channels/cn/cctvamerica.png',
        'fanart': 'channels/cn/cctvamerica_fanart.jpg',
        'enabled': True,
        'order': 6
    },
    'cctv5': {
        'resolver': '/resources/lib/channels/cn/cctv:get_live_url',
        'label': 'CCTV-5 体育',
        'thumb': 'channels/cn/cctv5.png',
        'fanart': 'channels/cn/cctv5_fanart.jpg',
        'enabled': True,
        'order': 7
    },
    'cctv5plus': {
        'resolver': '/resources/lib/channels/cn/cctv:get_live_url',
        'label': 'CCTV-5+ 体育赛事',
        'thumb': 'channels/cn/cctv5plus.png',
        'fanart': 'channels/cn/cctv5plus_fanart.jpg',
        'enabled': True,
        'order': 8
    },
    'cctv6': {
        'resolver': '/resources/lib/channels/cn/cctv:get_live_url',
        'label': 'CCTV-6 电影',
        'thumb': 'channels/cn/cctv6.png',
        'fanart': 'channels/cn/cctv6_fanart.jpg',
        'enabled': True,
        'order': 9
    },
    'cctv7': {
        'resolver': '/resources/lib/channels/cn/cctv:get_live_url',
        'label': 'CCTV-7 军事农业',
        'thumb': 'channels/cn/cctv7.png',
        'fanart': 'channels/cn/cctv7_fanart.jpg',
        'enabled': True,
        'order': 10
    },
    'cctv8': {
        'resolver': '/resources/lib/channels/cn/cctv:get_live_url',
        'label': 'CCTV-8 电视剧',
        'thumb': 'channels/cn/cctv8.png',
        'fanart': 'channels/cn/cctv8_fanart.jpg',
        'enabled': True,
        'order': 11
    },
    'cctvjilu': {
        'resolver': '/resources/lib/channels/cn/cctv:get_live_url',
        'label': 'CCTV-9 纪录',
        'thumb': 'channels/cn/cctvjilu.png',
        'fanart': 'channels/cn/cctvjilu_fanart.jpg',
        'enabled': True,
        'order': 12
    },
    'cctv10': {
        'resolver': '/resources/lib/channels/cn/cctv:get_live_url',
        'label': 'CCTV-10 科教',
        'thumb': 'channels/cn/cctv10.png',
        'fanart': 'channels/cn/cctv10_fanart.jpg',
        'enabled': True,
        'order': 13
    },
    'cctv11': {
        'resolver': '/resources/lib/channels/cn/cctv:get_live_url',
        'label': 'CCTV-11 戏曲',
        'thumb': 'channels/cn/cctv11.png',
        'fanart': 'channels/cn/cctv11_fanart.jpg',
        'enabled': True,
        'order': 14
    },
    'cctv12': {
        'resolver': '/resources/lib/channels/cn/cctv:get_live_url',
        'label': 'CCTV-12 社会与法',
        'thumb': 'channels/cn/cctv12.png',
        'fanart': 'channels/cn/cctv12_fanart.jpg',
        'enabled': True,
        'order': 15
    },
    'cctv13': {
        'resolver': '/resources/lib/channels/cn/cctv:get_live_url',
        'label': 'CCTV-13 新闻',
        'thumb': 'channels/cn/cctv13.png',
        'fanart': 'channels/cn/cctv13_fanart.jpg',
        'enabled': True,
        'order': 16
    },
    'cctvchild': {
        'resolver': '/resources/lib/channels/cn/cctv:get_live_url',
        'label': 'CCTV-14 少儿',
        'thumb': 'channels/cn/cctvchild.png',
        'fanart': 'channels/cn/cctvchild_fanart.jpg',
        'enabled': True,
        'order': 17
    },
    'cctv15': {
        'resolver': '/resources/lib/channels/cn/cctv:get_live_url',
        'label': 'CCTV-15 音乐',
        'thumb': 'channels/cn/cctv15.png',
        'fanart': 'channels/cn/cctv15_fanart.jpg',
        'enabled': True,
        'order': 18
    }
}
