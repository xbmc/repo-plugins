# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Joaopa
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
    'MPT 1': {
        'resolver': '/resources/lib/channels/mk/mpt:get_live_url',
        'label': 'MPT1',
        'thumb': 'channels/mk/mpt1.png',
        'fanart': 'channels/mk/mpt1_fanart.png',
        'enabled': True,
        'order': 1
    },
    'MPT 2': {
        'resolver': '/resources/lib/channels/mk/mpt:get_live_url',
        'label': 'MPT2',
        'thumb': 'channels/mk/mpt2.png',
        'fanart': 'channels/mk/mpt2_fanart.png',
        'enabled': True,
        'order': 2
    },
    'MPT 3': {
        'resolver': '/resources/lib/channels/mk/mpt:get_live_url',
        'label': 'MPT3',
        'thumb': 'channels/mk/mpt3.png',
        'fanart': 'channels/mk/mpt3_fanart.png',
        'enabled': True,
        'order': 3
    },
    'MPT 4': {
        'resolver': '/resources/lib/channels/mk/mpt:get_live_url',
        'label': 'MPT4',
        'thumb': 'channels/mk/mpt4.png',
        'fanart': 'channels/mk/mpt4_fanart.png',
        'enabled': True,
        'order': 4
    },
    'MPT 5': {
        'resolver': '/resources/lib/channels/mk/mpt:get_live_url',
        'label': 'MPT5',
        'thumb': 'channels/mk/mpt5.png',
        'fanart': 'channels/mk/mpt5_fanart.png',
        'enabled': True,
        'order': 5
    },

    'СОБРАНИСКИ КАНАЛ': {
        'resolver': '/resources/lib/channels/mk/mpt:get_live_url',
        'label': 'СОБРАНИСКИ КАНАЛ',
        'thumb': 'channels/mk/собранискиканал.png',
        'fanart': 'channels/mk/собранискиканал_fanart.png',
        'enabled': True,
        'order': 6
    },
    'МРТ 1 САТ': {
        'resolver': '/resources/lib/channels/mk/mpt:get_live_url',
        'label': 'МРТ1 САТ',
        'thumb': 'channels/mk/mpt1cat.png',
        'fanart': 'channels/mk/mpt1cat_fanart.png',
        'enabled': True,
        'order': 7
    },
    'МРТ 2 САТ': {
        'resolver': '/resources/lib/channels/mk/mpt:get_live_url',
        'label': 'МРТ2 САТ',
        'thumb': 'channels/mk/mpt2cat.png',
        'fanart': 'channels/mk/mpt2cat_fanart.png',
        'enabled': True,
        'order': 8
    },
    'МАКЕДОНСКО РАДИО 1': {
        'resolver': '/resources/lib/channels/mk/mpt:get_live_url',
        'label': 'MАКЕДОНСКО РАДИО1',
        'thumb': 'channels/mk/македонскорадио1.png',
        'fanart': 'channels/mk/македонскорадио1_fanart.png',
        'enabled': True,
        'order': 9
    },
    'МАКЕДОНСКО РАДИО 2': {
        'resolver': '/resources/lib/channels/mk/mpt:get_live_url',
        'label': 'MАКЕДОНСКО РАДИО2',
        'thumb': 'channels/mk/македонскорадио2.png',
        'fanart': 'channels/mk/македонскорадио2_fanart.png',
        'enabled': True,
        'order': 10
    },
    'МАКЕДОНСКО РАДИО 3': {
        'resolver': '/resources/lib/channels/mk/mpt:get_live_url',
        'label': 'MАКЕДОНСКО РАДИО3',
        'thumb': 'channels/mk/македонскорадио3.png',
        'fanart': 'channels/mk/македонскорадио3_fanart.png',
        'enabled': True,
        'order': 11
    },
    'МАКЕДОНСКО РАДИО САТ': {
        'resolver': '/resources/lib/channels/mk/mpt:get_live_url',
        'label': 'MАКЕДОНСКО РМАКЕДОНСКО РАДИО САТ',
        'thumb': 'channels/mk/македонско_радио_сат.png',
        'fanart': 'channels/mk/македонско_радио_cat_fanart.png',
        'enabled': True,
        'order': 12
    }
}
