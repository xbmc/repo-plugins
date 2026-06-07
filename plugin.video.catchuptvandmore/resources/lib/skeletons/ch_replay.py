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
    'rts': {
        'route': '/resources/lib/channels/ch/srgssr:list_categories',
        'label': 'RTS',
        'thumb': 'channels/ch/rts.png',
        'fanart': 'channels/ch/rts_fanart.jpg',
        'enabled': True,
        'order': 1
    },
    'rsi': {
        'route': '/resources/lib/channels/ch/srgssr:list_categories',
        'label': 'RSI',
        'thumb': 'channels/ch/rsi.png',
        'fanart': 'channels/ch/rsi_fanart.jpg',
        'enabled': True,
        'order': 2
    },
    'srf': {
        'route': '/resources/lib/channels/ch/srgssr:list_categories',
        'label': 'SRF',
        'thumb': 'channels/ch/srf.png',
        'fanart': 'channels/ch/srf_fanart.jpg',
        'enabled': True,
        'order': 3
    },
    'rtr': {
        'route': '/resources/lib/channels/ch/srgssr:list_categories',
        'label': 'RTR',
        'thumb': 'channels/ch/rtr.png',
        'fanart': 'channels/ch/rtr_fanart.jpg',
        'enabled': True,
        'order': 4
    },
    'swissinfo': {
        'route': '/resources/lib/channels/ch/srgssr:list_categories',
        'label': 'SWISSINFO',
        'thumb': 'channels/ch/swissinfo.png',
        'fanart': 'channels/ch/swissinfo_fanart.jpg',
        'enabled': True,
        'order': 5
    },
    'tvm3': {
        'route': '/resources/lib/channels/ch/tvm3:list_programs',
        'label': 'TVM3',
        'thumb': 'channels/ch/tvm3.png',
        'fanart': 'channels/ch/tvm3_fanart.jpg',
        'enabled': True,
        'order': 7
    },
    'becurioustv': {
        'route': '/resources/lib/channels/ch/becurioustv:list_categories',
        'label': 'BeCurious TV',
        'thumb': 'channels/ch/becurioustv.png',
        'fanart': 'channels/ch/becurioustv_fanart.jpg',
        'enabled': False,
        'order': 8
    },
    'lemanbleu': {
        'route': '/resources/lib/channels/ch/lemanbleu:list_programs',
        'label': 'Léman Bleu',
        'thumb': 'channels/ch/lemanbleu.png',
        'fanart': 'channels/ch/lemanbleu_fanart.jpg',
        'enabled': True,
        'order': 22
    },
    'lfmtv': {
        'route': '/resources/lib/channels/ch/lfmtv:list_programs',
        'label': 'LFM TV',
        'thumb': 'channels/ch/lfmtv.png',
        'fanart': 'channels/ch/lfmtv_fanart.jpg',
        'enabled': True,
        'order': 23
    }
}
