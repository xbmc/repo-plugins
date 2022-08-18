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
    'npo-start': {
        'route': '/resources/lib/channels/nl/npo:list_categories',
        'label': 'NPO Start',
        'thumb': 'channels/nl/npostart.png',
        'fanart': 'channels/nl/npostart_fanart.jpg',
        'enabled': True,
        'order': 9
    },
    'at5': {
        'route': '/resources/lib/channels/nl/at5:list_categories',
        'label': 'AT5',
        'thumb': 'channels/nl/at5.png',
        'fanart': 'channels/nl/at5_fanart.jpg',
        'enabled': True,
        'order': 10
    }
}
