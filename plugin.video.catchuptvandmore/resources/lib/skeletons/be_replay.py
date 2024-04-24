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
    'brf': {
        'route': '/resources/lib/channels/be/brf:list_categories',
        'label': 'BRF Mediathek',
        'thumb': 'channels/be/brf.png',
        'fanart': 'channels/be/brf_fanart.jpg',
        'enabled': True,
        'order': 1
    },
    'rtlplay': {
        'route': '/resources/lib/channels/be/rtlplaybe:rtlplay_root',
        'label': 'RTLplay',
        'thumb': 'channels/be/rtlplay.png',
        'fanart': 'channels/be/rtlplay_fanart.jpg',
        'enabled': True,
        'order': 2
    },
    'vrt': {
        'route': '/resources/lib/channels/be/vrt:list_root',
        'label': 'VRT NU',
        'thumb': 'channels/be/vrt.png',
        'fanart': 'channels/be/vrt_fanart.jpg',
        'enabled': True,
        'order': 5
    },
    'telemb': {
        'route': '/resources/lib/channels/be/telemb:list_programs',
        'label': 'Télé MB',
        'thumb': 'channels/be/telemb.png',
        'fanart': 'channels/be/telemb_fanart.jpg',
        'enabled': True,
        'order': 6
    },
    'rtc': {
        'route': '/resources/lib/channels/be/rtc:list_categories',
        'label': 'RTC Télé Liège',
        'thumb': 'channels/be/rtc.png',
        'fanart': 'channels/be/rtc_fanart.jpg',
        'enabled': True,
        'order': 7
    },
    'auvio': {
        'route': '/resources/lib/channels/be/rtbf:list_categories',
        'label': 'RTBF Auvio',
        'thumb': 'channels/be/auvio.png',
        'fanart': 'channels/be/auvio_fanart.jpg',
        'enabled': True,
        'order': 8
    },
    'tvlux': {
        'route': '/resources/lib/channels/be/tvlux:list_categories',
        'label': 'TV Lux',
        'thumb': 'channels/be/tvlux.png',
        'fanart': 'channels/be/tvlux_fanart.jpg',
        'enabled': True,
        'order': 9
    },
    'bx1': {
        'route': '/resources/lib/channels/be/bx1:list_programs',
        'label': 'BX1',
        'thumb': 'channels/be/bx1.png',
        'fanart': 'channels/be/bx1_fanart.jpg',
        'enabled': True,
        'order': 13
    },
    'nrjhitstvbe': {
        'route': '/resources/lib/channels/be/nrjhitstvbe:list_categories',
        'label': 'NRJ Hits TV',
        'thumb': 'channels/be/nrjhitstvbe.png',
        'fanart': 'channels/be/nrjhitstvbe_fanart.jpg',
        'enabled': True,
        'order': 17
    },
    'tvcom': {
        'route': '/resources/lib/channels/be/tvcom:list_categories',
        'label': 'TV Com',
        'thumb': 'channels/be/tvcom.png',
        'fanart': 'channels/be/tvcom_fanart.jpg',
        'enabled': True,
        'order': 19
    },
    'bouke': {
        'route': '/resources/lib/channels/be/bouke:list_programs',
        'label': 'Bouké',
        'thumb': 'channels/be/bouke.png',
        'fanart': 'channels/be/bouke.png',
        'enabled': True,
        'order': 20
    },
    'robtv': {
        'route': '/resources/lib/channels/be/robtv:list_programs',
        'label': 'ROB-tv (Oost-Brabant)',
        'thumb': 'channels/be/robtv.png',
        'fanart': 'channels/be/robtv_fanart.jpg',
        'enabled': True,
        'order': 21
    },
    'ln24': {
        'route': '/resources/lib/channels/be/ln24:list_programs',
        'label': 'LN24',
        'thumb': 'channels/be/ln24.png',
        'fanart': 'channels/be/ln24.png',
        'enabled': True,
        'order': 22
    },
    'telesambre': {
        'route': '/resources/lib/channels/be/telesambre:list_root',
        'label': 'Télésambre',
        'thumb': 'channels/be/telesambre.png',
        'fanart': 'channels/be/telesambre_fanart.jpg',
        'enabled': True,
        'order': 23
    }
}
