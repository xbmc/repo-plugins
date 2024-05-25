# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Joaopa
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
    'ept1': {
        'resolver': '/resources/lib/channels/gr/ept:get_live_url',
        'label': 'EPT1',
        'thumb': 'channels/gr/ept1.png',
        'fanart': 'channels/gr/ept1_fanart.jpg',
        'enabled': True,
        'order': 1
    },
    'ept2': {
        'resolver': '/resources/lib/channels/gr/ept:get_live_url',
        'label': 'EPT2',
        'thumb': 'channels/gr/ept2.png',
        'fanart': 'channels/gr/ept2_fanart.jpg',
        'enabled': True,
        'order': 2
    },
    'ept3': {
        'resolver': '/resources/lib/channels/gr/ept:get_live_url',
        'label': 'EPT3',
        'thumb': 'channels/gr/ept3.png',
        'fanart': 'channels/gr/ept3_fanart.jpg',
        'enabled': True,
        'order': 3
    },
    'eptsport': {
        'resolver': '/resources/lib/channels/gr/ept:get_live_url',
        'label': 'EPT Sport',
        'thumb': 'channels/gr/eptsport.png',
        'fanart': 'channels/gr/eptsport_fanart.jpg',
        'enabled': True,
        'order': 4
    },
    'eptnews': {
        'resolver': '/resources/lib/channels/gr/ept:get_live_url',
        'label': 'EPT News',
        'thumb': 'channels/gr/eptnews.png',
        'fanart': 'channels/gr/eptnews_fanart.jpg',
        'enabled': True,
        'order': 5
    }
}
