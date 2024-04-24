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
    'tv5mondeafrique': {
        'route': '/resources/lib/channels/wo/tv5mondeafrique:list_categories',
        'label': 'TV5Monde Afrique',
        'thumb': 'channels/wo/tv5mondeafrique.png',
        'fanart': 'channels/wo/tv5mondeafrique_fanart.jpg',
        'enabled': True,
        'order': 1
    },
    'arte': {
        'route': '/resources/lib/channels/wo/arte:list_categories',
        'label': 'Arte',
        'thumb': 'channels/wo/arte.png',
        'fanart': 'channels/wo/arte_fanart.jpg',
        'available_languages': ['FR', 'DE', 'EN', 'ES', 'PL', 'IT'],
        'enabled': True,
        'order': 3
    },
    'france24': {
        'route': '/resources/lib/channels/wo/france24:root_catchup_tv',
        'label': 'France 24',
        'thumb': 'channels/wo/france24.png',
        'fanart': 'channels/wo/france24_fanart.jpg',
        'available_languages': ['FR', 'EN', 'AR', 'ES'],
        'enabled': True,
        'order': 4
    },
    'nhkworld': {
        'route': '/resources/lib/channels/wo/nhkworld:list_categories',
        'label': 'NHK World',
        'thumb': 'channels/wo/nhkworld.png',
        'fanart': 'channels/wo/nhkworld_fanart.jpg',
        'available_languages': ['Outside Japan', 'In Japan'],
        'enabled': True,
        'order': 5
    },
    'tv5monde': {
        'route': '/resources/lib/channels/wo/tv5monde:list_categories',
        'label': 'TV5Monde',
        'thumb': 'channels/wo/tv5monde.png',
        'fanart': 'channels/wo/tv5monde_fanart.jpg',
        'enabled': True,
        'order': 6
    },
    'tivi5monde': {
        'route': '/resources/lib/channels/wo/tivi5monde:list_categories',
        'label': 'Tivi 5Monde',
        'thumb': 'channels/wo/tivi5monde.png',
        'fanart': 'channels/wo/tivi5monde_fanart.jpg',
        'enabled': True,
        'order': 7
    },
    'bvn': {
        'route': '/resources/lib/channels/wo/bvn:list_days',
        'label': 'BVN',
        'thumb': 'channels/wo/bvn.png',
        'fanart': 'channels/wo/bvn_fanart.jpg',
        'enabled': True,
        'order': 8
    },
    'arirang': {
        'route': '/resources/lib/channels/wo/arirang:list_categories',
        'label': 'Arirang (아리랑)',
        'thumb': 'channels/wo/arirang.png',
        'fanart': 'channels/wo/arirang_fanart.jpg',
        'enabled': True,
        'order': 11
    },
    'beinsports': {
        'route': '/resources/lib/channels/wo/beinsports:list_sites',
        'label': 'Bein Sports',
        'thumb': 'channels/wo/beinsports.png',
        'fanart': 'channels/wo/beinsports_fanart.jpg',
        'enabled': True,
        'order': 13
    },
    'afriquemedia': {
        'route': '/resources/lib/channels/wo/afriquemedia:list_categories',
        'label': 'Afrique Media',
        'thumb': 'channels/wo/afriquemedia.png',
        'fanart': 'channels/wo/afriquemedia_fanart.jpg',
        'enabled': True,
        'order': 20
    },
    'channelnewsasia': {
        'route': '/resources/lib/channels/wo/channelnewsasia:list_categories',
        'label': 'Channel NewsAsia',
        'thumb': 'channels/wo/channelnewsasia.png',
        'fanart': 'channels/wo/channelnewsasia_fanart.jpg',
        'enabled': True,
        'order': 23
    },
    'rt': {
        'route': '/resources/lib/channels/wo/rt:list_categories',
        'label': 'RT',
        'thumb': 'channels/wo/rt.png',
        'fanart': 'channels/wo/rt_fanart.jpg',
        'available_languages': ['FR', 'EN'],
        'enabled': True,
        'order': 24
    },
    'africa24': {
        'route': '/resources/lib/channels/wo/africa24:list_categories',
        'label': 'Africa 24',
        'thumb': 'channels/wo/africa24.png',
        'fanart': 'channels/wo/africa24_fanart.jpg',
        'enabled': True,
        'order': 25
    },
    'tv5mondeplus': {
        'route': '/resources/lib/channels/wo/tv5mondeplus:list_categories',
        'label': 'TV5Monde Plus',
        'thumb': 'channels/wo/tv5mondeplus.png',
        'fanart': 'channels/wo/tv5mondeplus.png',
        'enabled': True,
        'order': 26
    },
    'aljazeera': {
        'route': '/resources/lib/channels/wo/aljazeera:list_programs',
        'label': 'Aljazeera',
        'thumb': 'channels/wo/aljazeera.png',
        'fanart': 'channels/wo/aljazeera_fanart.png',
        'enabled': True,
        'order': 27
    }
}
