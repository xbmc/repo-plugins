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
    'tbd': {
        'route': '/resources/lib/channels/us/tbd:list_programs',
        'label': 'TBD',
        'thumb': 'channels/us/tbd.png',
        'fanart': 'channels/us/tbd_fanart.jpg',
        'enabled': True,
        'order': 2
    },
    'nycmedia': {
        'route': '/resources/lib/channels/us/nycmedia:list_programs',
        'label': 'NYC Media',
        'thumb': 'channels/us/nycmedia.png',
        'fanart': 'channels/us/nycmedia_fanart.jpg',
        'enabled': True,
        'order': 3
    },
    'abcnews': {
        'route': '/resources/lib/channels/us/abcnews:list_programs',
        'label': 'ABC News',
        'thumb': 'channels/us/abcnews.png',
        'fanart': 'channels/us/abcnews_fanart.jpg',
        'enabled': True,
        'order': 4
    }
}
