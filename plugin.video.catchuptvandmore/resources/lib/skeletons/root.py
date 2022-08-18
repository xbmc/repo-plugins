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

root = None

menu = {
    'live_tv': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30030,
        'thumb': 'live_tv.png',
        'enabled': True,
        'order': 1
    },
    'replay': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30031,
        'thumb': 'replay.png',
        'enabled': True,
        'order': 2
    },
    'websites': {
        'route': '/resources/lib/main:generic_menu',
        'label': 30032,
        'thumb': 'websites.png',
        'enabled': True,
        'order': 3
    },
    'favourites': {
        'route': '/resources/lib/main:favourites',
        'label': 30033,
        'thumb': 'favourites.png',
        'enabled': True,
        'order': 4
    }
}
