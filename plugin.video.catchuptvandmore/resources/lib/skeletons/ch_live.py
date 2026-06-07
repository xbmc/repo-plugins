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
    },
    'canal9': {
        'resolver': '/resources/lib/channels/ch/canal9:get_live_url',
        'label': 'CANAL9',
        'thumb': 'channels/ch/canal9.png',
        'fanart': 'channels/ch/canal9.png',
        'enabled': True,
        'order': 26
    },
    'canalalpha': {
        'resolver': '/resources/lib/channels/ch/canalalpha:get_live_url',
        'label': 'CANALALPHA',
        'thumb': 'channels/ch/canalalpha.png',
        'fanart': 'channels/ch/canalalpha.png',
        'enabled': True,
        'order': 27
    },
    'CARAC1': {
        'resolver': '/resources/lib/channels/ch/carac:get_live_url',
        'label': 'CARAC1',
        'thumb': 'channels/ch/carac1.png',
        'fanart': 'channels/ch/carac1.png',
        'enabled': True,
        'order': 28
    },
    'CARAC2': {
        'resolver': '/resources/lib/channels/ch/carac:get_live_url',
        'label': 'CARAC2',
        'thumb': 'channels/ch/carac2.png',
        'fanart': 'channels/ch/carac2.png',
        'enabled': True,
        'order': 29
    },
    'CARAC3': {
        'resolver': '/resources/lib/channels/ch/carac:get_live_url',
        'label': 'CARAC3',
        'thumb': 'channels/ch/carac3.png',
        'fanart': 'channels/ch/carac3.png',
        'enabled': True,
        'order': 30
    },
    'CARAC4': {
        'resolver': '/resources/lib/channels/ch/carac:get_live_url',
        'label': 'CARAC4',
        'thumb': 'channels/ch/carac4.png',
        'fanart': 'channels/ch/carac4.png',
        'enabled': True,
        'order': 31
    },
    'alpenwelle': {
        'resolver': '/resources/lib/channels/ch/alpenwelle:get_live_url',
        'label': 'alpen-welle',
        'thumb': 'channels/ch/awpluslogo.png',
        'fanart': 'channels/ch/awpluslogo.png',
        'enabled': True,
        'order': 32
    },
    'blick': {
        'resolver': '/resources/lib/channels/ch/blick:get_live_url',
        'label': 'Blick',
        'thumb': 'channels/ch/blick.png',
        'fanart': 'channels/ch/blick.png',
        'enabled': True,
        'order': 33
    },
    'dieneuezeit': {
        'resolver': '/resources/lib/channels/ch/dieneuezeit:get_live_url',
        'label': 'Die Neue Zeit',
        'thumb': 'channels/ch/dieneuezeit.png',
        'fanart': 'channels/ch/dieneuezeit.png',
        'enabled': True,
        'order': 34
    },
    'dieutv': {
        'resolver': '/resources/lib/channels/ch/dieutv:get_live_url',
        'label': 'DieuTV',
        'thumb': 'channels/ch/dieutv.png',
        'fanart': 'channels/ch/dieutv.png',
        'enabled': True,
        'order': 35
    },
    'dritatv': {
        'resolver': '/resources/lib/channels/ch/dritatv:get_live_url',
        'label': 'DritaTV',
        'thumb': 'channels/ch/dritatv.png',
        'fanart': 'channels/ch/dritatv.png',
        'enabled': True,
        'order': 36
    }
}
