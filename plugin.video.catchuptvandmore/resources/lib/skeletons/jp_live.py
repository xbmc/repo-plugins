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

root = 'live_tv'

menu = {
    'ntvnews24': {
        'resolver': '/resources/lib/channels/jp/ntvnews24:get_live_url',
        'label': '日テレ News24',
        'thumb': 'channels/jp/ntvnews24.png',
        'fanart': 'channels/jp/ntvnews24_fanart.jpg',
        'enabled': True,
        'order': 11
    },
    'japanetshoppingdx': {
        'resolver': '/resources/lib/channels/jp/japanetshoppingdx:get_live_url',
        'label': 'ジャパネットチャンネルDX',
        'thumb': 'channels/jp/japanetshoppingdx.png',
        'fanart': 'channels/jp/japanetshoppingdx_fanart.jpg',
        'enabled': True,
        'order': 12
    },
    'weathernewsjp': {
        'resolver': '/resources/lib/channels/jp/weathernewsjp:get_live_url',
        'label': '株式会社ウェザーニューズ',
        'thumb': 'channels/jp/weathernewsjp.png',
        'fanart': 'channels/jp/weathernewsjp_fanart.jpg',
        'enabled': True,
        'order': 14
    }
}
