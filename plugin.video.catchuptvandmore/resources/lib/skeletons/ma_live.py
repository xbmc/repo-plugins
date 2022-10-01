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
    'alAoula': {
        'resolver': '/resources/lib/channels/ma/snrt:get_live_url',
        'label': 'Al Aoula',
        'thumb': 'channels/ma/alaoula.png',
        'fanart': 'channels/ma/alaoula_live_fanart.jpg',
        'm3u_group': 'Maroc',
        'enabled': True,
        'order': 1,
    },
    'laayoune': {
        'resolver': '/resources/lib/channels/ma/snrt:get_live_url',
        'label': 'Al Aoula Laayoune',
        'thumb': 'channels/ma/laayoune.png',
        'fanart': 'channels/ma/laayoune_live_fanart.jpg',
        'm3u_group': 'Maroc',
        'enabled': True,
        'order': 2,
    },
    'arryadia': {
        'resolver': '/resources/lib/channels/ma/snrt:get_live_url',
        'label': 'Arryadia',
        'thumb': 'channels/ma/arryadia.png',
        'fanart': 'channels/ma/arryadia_live_fanart.jpg',
        'm3u_group': 'Maroc',
        'enabled': True,
        'order': 3,
    },
    'athaqafia': {
        'resolver': '/resources/lib/channels/ma/snrt:get_live_url',
        'label': 'Athaqafia',
        'thumb': 'channels/ma/athaqafia.png',
        'fanart': 'channels/ma/athaqafia_live_fanart.jpg',
        'm3u_group': 'Maroc',
        'enabled': True,
        'order': 4,
    },
    'alMaghribia': {
        'resolver': '/resources/lib/channels/ma/snrt:get_live_url',
        'label': 'Al Maghribia',
        'thumb': 'channels/ma/almaghribia.png',
        'fanart': 'channels/ma/almaghribia_live_fanart.jpg',
        'm3u_group': 'Maroc',
        'enabled': True,
        'order': 5,
    },
    'assadissa': {
        'resolver': '/resources/lib/channels/ma/snrt:get_live_url',
        'label': 'Assadissa',
        'thumb': 'channels/ma/assadissa.png',
        'fanart': 'channels/ma/assadissa_live_fanart.jpg',
        'm3u_group': 'Maroc',
        'enabled': True,
        'order': 6,
    },
    'tamazight': {
        'resolver': '/resources/lib/channels/ma/snrt:get_live_url',
        'label': 'Tamazight',
        'thumb': 'channels/ma/tamazight.png',
        'fanart': 'channels/ma/tamazight_live_fanart.jpg',
        'm3u_group': 'Maroc',
        'enabled': True,
        'order': 7,
    },
    'télémaroc': {
        'resolver': '/resources/lib/channels/ma/telemaroc:get_live_url',
        'label': 'Télé Maroc',
        'thumb': 'channels/ma/telemaroc.png',
        'fanart': 'channels/ma/telemaroc_fanart.jpg',
        'enabled': True,
        'order': 8
    },
    'maghreb': {
        'resolver': '/resources/lib/channels/ma/medi1:get_live_url',
        'label': 'Medi1 Maghreb',
        'thumb': 'channels/ma/medi1.png',
        'fanart': 'channels/ma/medi1maghreb_fanart.jpg',
        'enabled': True,
        'order': 9
    },
    'arabic': {
        'resolver': '/resources/lib/channels/ma/medi1:get_live_url',
        'label': 'Medi1 Arabic',
        'thumb': 'channels/ma/medi1.png',
        'fanart': 'channels/ma/medi1arabic_fanart.jpg',
        'enabled': True,
        'order': 10
    },
    'afrique': {
        'resolver': '/resources/lib/channels/ma/medi1:get_live_url',
        'label': 'Medi1 Afrique',
        'thumb': 'channels/ma/medi1afrique.png',
        'fanart': 'channels/ma/medi1afrique_fanart.jpg',
        'enabled': True,
        'order': 11
    },
    'm24': {
        'resolver': '/resources/lib/channels/ma/m24:get_live_url',
        'label': 'M24',
        'thumb': 'channels/ma/m24.png',
        'fanart': 'channels/ma/m24_fanart.jpg',
        'enabled': True,
        'order': 12
    }
}
