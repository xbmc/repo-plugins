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
    'elhiwarettounsi': {
        'resolver': '/resources/lib/channels/tn/elhiwarettounsi:get_live_url',
        'label': 'Elhiwar Ettounsi',
        'thumb': 'channels/tn/elhiwarettounsi.png',
        'fanart': 'channels/tn/elhiwarettounsi_fanart.jpg',
        'enabled': True,
        'order': 1
    },
    'nessma': {
        'resolver': '/resources/lib/channels/tn/nessma:get_live_url',
        'label': 'نسمة تي في',
        'thumb': 'channels/tn/nessma.png',
        'fanart': 'channels/tn/nessma_fanart.jpg',
        'enabled': True,
        'order': 2
    },
    'watania1': {
        'resolver': '/resources/lib/channels/tn/watania:get_live_url',
        'label': 'التلفزة التونسية الوطنية 1',
        'thumb': 'channels/tn/watania1.png',
        'fanart': 'channels/tn/watania1_fanart.jpg',
        'enabled': True,
        'order': 3
    },
    'watania2': {
        'resolver': '/resources/lib/channels/tn/watania:get_live_url',
        'label': 'التلفزة التونسية الوطنية 2',
        'thumb': 'channels/tn/watania2.png',
        'fanart': 'channels/tn/watania2_fanart.jpg',
        'enabled': True,
        'order': 4
    }
}
