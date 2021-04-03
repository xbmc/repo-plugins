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
    'slo1': {
        'resolver': '/resources/lib/channels/si/rtvslo:get_live_url',
        'label': 'TV SLO 1',
        'thumb': 'channels/si/slo1.png',
        'fanart': 'channels/si/slo1_fanart.jpg',
        'enabled': True,
        'order': 1
    },
    'slo2': {
        'resolver': '/resources/lib/channels/si/rtvslo:get_live_url',
        'label': 'TV SLO 2',
        'thumb': 'channels/si/slo2.png',
        'fanart': 'channels/si/slo2_fanart.jpg',
        'enabled': True,
        'order': 2
    },
    'slo3': {
        'resolver': '/resources/lib/channels/si/rtvslo:get_live_url',
        'label': 'TV SLO 3',
        'thumb': 'channels/si/slo3.png',
        'fanart': 'channels/si/slo3_fanart.jpg',
        'enabled': True,
        'order': 3
    },
    'koper': {
        'resolver': '/resources/lib/channels/si/rtvslo:get_live_url',
        'label': 'Koper',
        'thumb': 'channels/si/koper.png',
        'fanart': 'channels/si/koper_fanart.jpg',
        'enabled': True,
        'order': 4
    },
    'maribor': {
        'resolver': '/resources/lib/channels/si/rtvslo:get_live_url',
        'label': 'Maribor',
        'thumb': 'channels/si/maribor.png',
        'fanart': 'channels/si/maribor_fanart.jpg',
        'enabled': True,
        'order': 5
    },
    'mmc': {
        'resolver': '/resources/lib/channels/si/rtvslo:get_live_url',
        'label': 'MMC',
        'thumb': 'channels/si/mmc.png',
        'fanart': 'channels/si/mmc_fanart.jpg',
        'enabled': True,
        'order': 6
    }
}
