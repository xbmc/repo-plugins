# -*- coding: utf-8 -*-
# Copyright: (c) 2025, QValette
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

# The following dictionaries describe
# the addon's tree architecture.
# * Key: item id
# * Value: item infos
#    - route (folder)/resolver (playable URL): Callback function to run once this item is selected
#    - thumb: Item thumb path relative to "media" folder
#    - fanart: Item fanart path relative to "media" folder

root = 'live_tv'

menu = {
    'atomicacademytv': {
        'resolver': '/resources/lib/channels/ro/atomic:get_live_url',
        'label': 'Atomic Academy TV',
        'thumb': 'channels/ro/atomic_academy.png',
        'fanart': 'channels/ro/atomic_fanart.jpg',
        'xmltv_id': 'AtomicAcademyTV.ro@SD',
        'm3u_group': 'Atomic',
        'enabled': True,
        'order': 1
    },
    'atomictv': {
        'resolver': '/resources/lib/channels/ro/atomic:get_live_url',
        'label': 'Atomic TV',
        'thumb': 'channels/ro/atomic_tv.png',
        'fanart': 'channels/ro/atomic_fanart.jpg',
        'xmltv_id': 'AtomicTV.ro@SD',
        'm3u_group': 'Atomic',
        'enabled': True,
        'order': 2
    },
    'banat-tv': {
        'resolver': '/resources/lib/channels/ro/regional:get_live_url',
        'label': 'Banat TV',
        'thumb': 'channels/ro/banat_tv.png',
        'fanart': 'channels/ro/banat_tv_fanart.jpg',
        'xmltv_id': 'BanatTV.ro@SD',
        'm3u_group': 'Regional',
        'enabled': True,
        'order': 3
    }
}
