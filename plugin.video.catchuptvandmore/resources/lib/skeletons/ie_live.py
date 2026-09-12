# -*- coding: utf-8 -*-
# Copyright: (c) 2025
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
    'RTEONE': {
        'resolver': '/resources/lib/channels/ie/rte:get_live_url',
        'label': 'RTÉ One',
        'thumb': 'channels/ie/rte_one.png',
        'fanart': 'channels/ie/rte_one_fanart.png',
        'xmltv_id': '',
        'enabled': True,
        'order': 1
    }, 'RTE2': {
        'resolver': '/resources/lib/channels/ie/rte:get_live_url',
        'label': 'RTÉ2',
        'thumb': 'channels/ie/rte_two.png',
        'fanart': 'channels/ie/rte_two_fanart.png',
        'xmltv_id': '',
        'enabled': True,
        'order': 2
    }, 'RTENewsNow': {
        'resolver': '/resources/lib/channels/ie/rte:get_live_url',
        'label': 'RTÉ News',
        'thumb': 'channels/ie/rte_news.png',
        'fanart': 'channels/ie/rte_news_fanart.png',
        'xmltv_id': '',
        'enabled': True,
        'order': 3
    }, 'RTEJr': {
        'resolver': '/resources/lib/channels/ie/rte:get_live_url',
        'label': 'RTÉjr',
        'thumb': 'channels/ie/rte_jr.png',
        'fanart': 'channels/ie/rte_jr_fanart.png',
        'xmltv_id': '',
        'enabled': True,
        'order': 4
    }, 'tg4': {
        'resolver': '/resources/lib/channels/ie/tg4:get_live_url',
        'label': 'TG4',
        'thumb': 'channels/ie/tg4.png',
        'fanart': 'channels/ie/tg4_fanart.png',
        'xmltv_id': '',
        'enabled': True,
        'order': 5
    }, 'cula4': {
        'resolver': '/resources/lib/channels/ie/cula4:get_live_url',
        'label': 'Cúla4',
        'thumb': 'channels/ie/cula4.png',
        'fanart': 'channels/ie/cula4_fanart.png',
        'xmltv_id': '',
        'enabled': True,
        'order': 6
    },
}
