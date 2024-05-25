# -*- coding: utf-8 -*-
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from codequick import Script, utils

# The following dictionaries describe
# the addon's tree architecture.
# * Key: item id
# * Value: item infos
#     - route (folder)/resolver (playable URL): Callback function to run once this item is selected
#     - thumb: Item thumb path relative to "media" folder
#     - fanart: Item fanart path relative to "media" folder

root = 'replay'

menu = {
    'tv5unis': {
        'route': '/resources/lib/channels/ca/tv5unis:list_categories',
        'label': 'TV5 Unis',
        'thumb': 'channels/ca/tv5unis.png',
        'fanart': 'channels/ca/tv5unis_fanart.jpg',
        'enabled': True,
        'order': 1
    },
    'telequebec': {
        'route': '/resources/lib/channels/ca/telequebec:list_root',
        'label': 'Télé-Québec',
        'thumb': 'channels/ca/telequebec.png',
        'fanart': 'channels/ca/telequebec_fanart.jpg',
        'enabled': True,
        'order': 4
    },
    'tva': {
        'route': '/resources/lib/channels/ca/tva:tva_root',
        'label': 'TVA',
        'thumb': 'channels/ca/tva.png',
        'fanart': 'channels/ca/tva_fanart.jpg',
        'enabled': True,
        'order': 5
    },
    'icitele': {
        'route': '/resources/lib/channels/ca/icitele:list_programs',
        'label': 'ICI Télé (' + utils.ensure_unicode(Script.setting['icitele.language']) + ')',
        'thumb': 'channels/ca/icitele.png',
        'fanart': 'channels/ca/icitele_fanart.jpg',
        'enabled': True,
        'order': 6
    },
    'icitoutv': {
        'route': '/resources/lib/channels/ca/icitoutv:list_categories',
        'label': 'ICI Tou.tv',
        'thumb': 'channels/ca/icitoutv.png',
        'fanart': 'channels/ca/icitoutv_fanart.jpg',
        'enabled': True,
        'order': 8
    },
    'telemag': {
        'route': '/resources/lib/channels/ca/telemag:list_programs',
        'label': 'Télé-Mag',
        'thumb': 'channels/ca/telemag.png',
        'fanart': 'channels/ca/telemag_fanart.jpg',
        'enabled': True,
        'order': 9
    },
    'noovo': {
        'route': '/resources/lib/channels/ca/noovo:list_programs',
        'label': 'NOOVO',
        'thumb': 'channels/ca/noovo.png',
        'fanart': 'channels/ca/noovo_fanart.jpg',
        'enabled': True,
        'order': 10
    }
}
