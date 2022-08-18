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
    'cbsnews': {
        'resolver': '/resources/lib/channels/us/cbsnews:get_live_url',
        'label': 'CBS News',
        'thumb': 'channels/us/cbsnews.png',
        'fanart': 'channels/us/cbsnews_fanart.jpg',
        'enabled': True,
        'order': 1
    },
    'tbd': {
        'resolver': '/resources/lib/channels/us/tbd:get_live_url',
        'label': 'TBD',
        'thumb': 'channels/us/tbd.png',
        'fanart': 'channels/us/tbd_fanart.jpg',
        'enabled': True,
        'order': 2
    },
    'abcnews': {
        'resolver': '/resources/lib/channels/us/abcnews:get_live_url',
        'label': 'ABC News',
        'thumb': 'channels/us/abcnews.png',
        'fanart': 'channels/us/abcnews_fanart.jpg',
        'enabled': True,
        'order': 4
    },
    'pbskids': {
        'resolver': '/resources/lib/channels/us/pbskids:get_live_url',
        'label': 'PBS Kids',
        'thumb': 'channels/us/pbskids.png',
        'fanart': 'channels/us/pbskids_fanart.jpg',
        'enabled': True,
        'order': 5
    }
}
