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
    'nessma': {
        'route': '/resources/lib/channels/tn/nessma:list_categories',
        'label': 'نسمة تي في',
        'thumb': 'channels/tn/nessma.png',
        'fanart': 'channels/tn/nessma_fanart.jpg',
        'enabled': True,
        'order': 3
    }
}
