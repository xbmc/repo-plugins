# -*- coding: utf-8 -*-
# Copyright: (c) 2020, darodi
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
    'joj': {
        'resolver': '/resources/lib/channels/sk/joj:get_live_url',
        'label': 'JOJ.sk',
        'thumb': 'channels/sk/joj.png',
        'fanart': 'channels/sk/joj.png',
        'm3u_group': 'Slovakia',
        'enabled': True,
        'order': 1
    },
    'jojplus': {
        'resolver': '/resources/lib/channels/sk/joj:get_live_url',
        'label': 'Televízia PLUS',
        'thumb': 'channels/sk/jojplus.png',
        'fanart': 'channels/sk/jojplus.png',
        'm3u_group': 'Slovakia',
        'enabled': True,
        'order': 2
    },
    'jojwau': {
        'resolver': '/resources/lib/channels/sk/joj:get_live_url',
        'label': 'Televízia WAU',
        'thumb': 'channels/sk/jojwau.png',
        'fanart': 'channels/sk/jojwau.png',
        'm3u_group': 'Slovakia',
        'enabled': True,
        'order': 3
    },
    'jojfamily': {
        'resolver': '/resources/lib/channels/sk/joj:get_live_url',
        'label': 'JOJ Family',
        'thumb': 'channels/sk/jojfamily.png',
        'fanart': 'channels/sk/jojfamily.png',
        'm3u_group': 'Slovakia',
        'enabled': True,
        'order': 4
    }
}
