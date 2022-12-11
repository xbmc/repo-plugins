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
    'rougetv': {
        'resolver': '/resources/lib/channels/ch/rougetv:get_live_url',
        'label': 'Rouge TV',
        'thumb': 'channels/ch/rougetv.png',
        'fanart': 'channels/ch/rougetv_fanart.jpg',
        'enabled': True,
        'order': 6
    },
    'tvm3': {
        'resolver': '/resources/lib/channels/ch/tvm3:get_live_url',
        'label': 'TVM3',
        'thumb': 'channels/ch/tvm3.png',
        'fanart': 'channels/ch/tvm3_fanart.jpg',
        'enabled': True,
        'order': 7
    },
    'rtsun': {
        'resolver': '/resources/lib/channels/ch/srgssr:get_live_url',
        'label': 'RTS Un',
        'thumb': 'channels/ch/rtsun.png',
        'fanart': 'channels/ch/rtsun_fanart.jpg',
        'xmltv_id': 'C202.api.telerama.fr',
        'enabled': True,
        'order': 9
    },
    'rtsdeux': {
        'resolver': '/resources/lib/channels/ch/srgssr:get_live_url',
        'label': 'RTS Deux',
        'thumb': 'channels/ch/rtsdeux.png',
        'fanart': 'channels/ch/rtsdeux_fanart.jpg',
        'xmltv_id': 'C183.api.telerama.fr',
        'enabled': True,
        'order': 10
    },
    'rtsinfo': {
        'resolver': '/resources/lib/channels/ch/srgssr:get_live_url',
        'label': 'RTS Info',
        'thumb': 'channels/ch/rtsinfo.png',
        'fanart': 'channels/ch/rtsinfo_fanart.jpg',
        'enabled': True,
        'order': 11
    },
    'rtscouleur3': {
        'resolver': '/resources/lib/channels/ch/srgssr:get_live_url',
        'label': 'RTS Couleur 3',
        'thumb': 'channels/ch/rtscouleur3.png',
        'fanart': 'channels/ch/rtscouleur3_fanart.jpg',
        'enabled': True,
        'order': 12
    },
    'rsila1': {
        'resolver': '/resources/lib/channels/ch/srgssr:get_live_url',
        'label': 'RSI La 1',
        'thumb': 'channels/ch/rsila1.png',
        'fanart': 'channels/ch/rsila1_fanart.jpg',
        'xmltv_id': 'C200.api.telerama.fr',
        'enabled': True,
        'order': 13
    },
    'rsila2': {
        'resolver': '/resources/lib/channels/ch/srgssr:get_live_url',
        'label': 'RSI La 2',
        'thumb': 'channels/ch/rsila2.png',
        'fanart': 'channels/ch/rsila2_fanart.jpg',
        'xmltv_id': 'C201.api.telerama.fr',
        'enabled': True,
        'order': 14
    },
    'srf1': {
        'resolver': '/resources/lib/channels/ch/srgssr:get_live_url',
        'label': 'SRF 1',
        'thumb': 'channels/ch/srf1.png',
        'fanart': 'channels/ch/srf1_fanart.jpg',
        'xmltv_id': 'C59.api.telerama.fr',
        'enabled': True,
        'order': 15
    },
    'srfinfo': {
        'resolver': '/resources/lib/channels/ch/srgssr:get_live_url',
        'label': 'SRF Info',
        'thumb': 'channels/ch/srfinfo.png',
        'fanart': 'channels/ch/srfinfo_fanart.jpg',
        'enabled': True,
        'order': 16
    },
    'srfzwei': {
        'resolver': '/resources/lib/channels/ch/srgssr:get_live_url',
        'label': 'SRF Zwei',
        'thumb': 'channels/ch/srfzwei.png',
        'fanart': 'channels/ch/srfzwei_fanart.jpg',
        'enabled': True,
        'order': 17
    },
    'rtraufsrf1': {
        'resolver': '/resources/lib/channels/ch/srgssr:get_live_url',
        'label': 'RTR auf SRF 1',
        'thumb': 'channels/ch/rtraufsrf1.png',
        'fanart': 'channels/ch/rtraufsrf1_fanart.jpg',
        'enabled': True,
        'order': 18
    },
    'rtraufsrfinfo': {
        'resolver': '/resources/lib/channels/ch/srgssr:get_live_url',
        'label': 'RTR auf SRF Info',
        'thumb': 'channels/ch/rtraufsrfinfo.png',
        'fanart': 'channels/ch/rtraufsrfinfo_fanart.jpg',
        'enabled': True,
        'order': 19
    },
    'rtraufsrf2': {
        'resolver': '/resources/lib/channels/ch/srgssr:get_live_url',
        'label': 'RTR auf SRF 2',
        'thumb': 'channels/ch/rtraufsrf2.png',
        'fanart': 'channels/ch/rtraufsrf2_fanart.jpg',
        'enabled': True,
        'order': 20
    },
    'teleticino': {
        'resolver': '/resources/lib/channels/ch/teleticino:get_live_url',
        'label': 'Teleticino',
        'thumb': 'channels/ch/teleticino.png',
        'fanart': 'channels/ch/teleticino_fanart.jpg',
        'enabled': True,
        'order': 21
    },
    'lemanbleu': {
        'resolver': '/resources/lib/channels/ch/lemanbleu:get_live_url',
        'label': 'Léman Bleu',
        'thumb': 'channels/ch/lemanbleu.png',
        'fanart': 'channels/ch/lemanbleu_fanart.jpg',
        'enabled': True,
        'order': 22
    },
    'telem1': {
        'resolver': '/resources/lib/channels/ch/telem1:get_live_url',
        'label': 'Tele M1',
        'thumb': 'channels/ch/telem1.png',
        'fanart': 'channels/ch/telem1_fanart.jpg',
        'enabled': True,
        'order': 23
    },
    'lfmtv': {
        'resolver': '/resources/lib/channels/ch/lfmtv:get_live_url',
        'label': 'LFM TV',
        'thumb': 'channels/ch/lfmtv.png',
        'fanart': 'channels/ch/lfmtv_fanart.jpg',
        'enabled': True,
        'order': 24
    },
    'latele': {
        'resolver': '/resources/lib/channels/ch/latele:get_live_url',
        'label': 'LATELE',
        'thumb': 'channels/ch/latele.png',
        'fanart': 'channels/ch/latele.png',
        'enabled': True,
        'order': 25
    }
}
