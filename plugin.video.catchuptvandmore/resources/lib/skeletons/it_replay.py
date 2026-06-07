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
    'la7': {
        'route': '/resources/lib/channels/it/la7:list_days',
        'label': 'La7',
        'thumb': 'channels/it/la7.png',
        'fanart': 'channels/it/la7_fanart.jpg',
        'enabled': True,
        'order': 1
    },
    'la7d': {
        'route': '/resources/lib/channels/it/la7:list_days',
        'label': 'La7d',
        'thumb': 'channels/it/la7d.png',
        'fanart': 'channels/it/la7d_fanart.jpg',
        'enabled': True,
        'order': 15
    },
    'raiplay': {
        'route': '/resources/lib/channels/it/raiplay:list_root',
        'label': 'Rai Play',
        'thumb': 'channels/it/raiplay.png',
        'fanart': 'channels/it/raiplay_fanart.jpg',
        'enabled': True,
        'order': 16
    }
}
