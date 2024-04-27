# -*- coding: utf-8 -*-
# Copyright: (c) 2016, SylvainCecchetto
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
    'tvp1': {
        'resolver': '/resources/lib/channels/pl/tvp:get_live_url',
        'label': 'TVP 1',
        'thumb': 'channels/pl/tvp1.png',
        'fanart': 'channels/pl/tvp.png',
        'enabled': True,
        'order': 1
    },
    'tvp2': {
        'resolver': '/resources/lib/channels/pl/tvp:get_live_url',
        'label': 'TVP 2',
        'thumb': 'channels/pl/tvp2.png',
        'fanart': 'channels/pl/tvp.png',
        'enabled': True,
        'order': 2
    },
    'tvp3': {
        'resolver': '/resources/lib/channels/pl/tvp:get_live_url',
        'label': 'TVP 3',
        'thumb': 'channels/pl/tvp3.png',
        'fanart': 'channels/pl/tvp.png',
        'available_languages': {
            "Białystok": {}, "Bydgoszcz": {}, "Gdańsk": {}, "Gorzów Wielkopolski": {},
            "Katowice": {}, "Kielce": {}, "Kraków": {}, "Lublin": {}, "Łódź": {}, "Olsztyn": {},
            "Opole": {}, "Poznań": {}, "Rzeszów": {}, "Szczecin": {}, "Warszawa": {}, "Wrocław": {}
        },
        'enabled': True,
        'order': 3
    },
    'tvpinfo': {
        'resolver': '/resources/lib/channels/pl/tvp:get_live_url',
        'label': 'TVP Info',
        'thumb': 'channels/pl/tvpinfo.png',
        'fanart': 'channels/pl/tvpinfo_fanart.png',
        'enabled': True,
        'order': 4
    },
    'tvpworld': {
        'resolver': '/resources/lib/channels/pl/tvp:get_live_url',
        'label': 'TVP World',
        'thumb': 'channels/pl/tvpworld.png',
        'fanart': 'channels/pl/tvp.png',
        'enabled': True,
        'order': 5
    },
    'tvppolonia': {
        'resolver': '/resources/lib/channels/pl/tvp:get_live_url',
        'label': 'TVP Polonia',
        'thumb': 'channels/pl/tvppolonia.png',
        'fanart': 'channels/pl/tvp.png',
        'enabled': True,
        'order': 6
    },
    'tvpwilno': {
        'resolver': '/resources/lib/channels/pl/tvp:get_live_url',
        'label': 'TVP Wilno',
        'thumb': 'channels/pl/tvpwilno.png',
        'fanart': 'channels/pl/tvp.png',
        'enabled': True,
        'order': 7
    },
    'tvpalfa': {
        'resolver': '/resources/lib/channels/pl/tvp:get_live_url',
        'label': 'TVP Alfa',
        'thumb': 'channels/pl/tvpalfa.png',
        'fanart': 'channels/pl/tvp.png',
        'enabled': True,
        'order': 8
    },
    'ua1': {
        'resolver': '/resources/lib/channels/pl/tvp:get_live_url',
        'label': 'UA 1',
        'thumb': 'channels/pl/ua1.png',
        'fanart': 'channels/pl/tvp.png',
        'enabled': True,
        'order': 9
    },
    'tvpabc': {
        'resolver': '/resources/lib/channels/pl/tvpabc:get_live_url',
        'label': 'TVP ABC',
        'thumb': 'channels/pl/tvpabc.png',
        'fanart': 'channels/pl/tvpabc_fanart.jpg',
        'enabled': True,
        'order': 10
    },
    'tvpabc2': {
        'resolver': '/resources/lib/channels/pl/tvpabc:get_live_url',
        'label': 'TVP ABC 2',
        'thumb': 'channels/pl/tvpabc2.png',
        'fanart': 'channels/pl/tvpabc_fanart.jpg',
        'enabled': True,
        'order': 11
    },
}
