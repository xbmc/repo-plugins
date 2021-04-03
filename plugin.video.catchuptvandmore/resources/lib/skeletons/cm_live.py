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
    'crtv': {
        'resolver': '/resources/lib/channels/cm/crtv:get_live_url',
        'label': 'CRTV',
        'thumb': 'channels/cm/crtv.png',
        'fanart': 'channels/cm/crtv_fanart.jpg',
        'enabled': True,
        'order': 1
    },
    'crtvnews': {
        'resolver': '/resources/lib/channels/cm/crtv:get_live_url',
        'label': 'CRTV News',
        'thumb': 'channels/cm/crtvnews.png',
        'fanart': 'channels/cm/crtvnews_fanart.jpg',
        'enabled': True,
        'order': 2
    }
}
