# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2016  SylvainCecchetto

    This file is part of Catch-up TV & More.

    Catch-up TV & More is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Catch-up TV & More is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with Catch-up TV & More; if not, write to the Free Software Foundation,
    Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals
from codequick import Script, utils
"""
The following dictionaries describe
the addon's tree architecture.
* Key: item id
* Value: item infos
    - route (folder)/resolver (playable URL): Callback function to run once this item is selected
    - thumb: Item thumb path relative to "media" folder
    - fanart: Item fanart path relative to "meia" folder
"""

root = 'live_tv'

menu = {
    'euronews': {
        'resolver': '/resources/lib/channels/wo/euronews:get_live_url',
        'label': 'Euronews (' + utils.ensure_unicode(Script.setting['euronews.language']) + ')',
        'thumb':
        'channels/wo/euronews.png',
        'fanart':
        'channels/wo/euronews_fanart.jpg',
        'available_languages': [
            'FR', 'EN', 'AR', 'DE', 'IT', 'ES', 'PT', 'RU', 'TR', 'FA', 'GR',
            'HU'
        ],
        'enabled': True,
        'order': 2
    },
    'arte': {
        'resolver': '/resources/lib/channels/wo/arte:get_live_url',
        'label': 'Arte (' + utils.ensure_unicode(Script.setting['arte.language']) + ')',
        'thumb': 'channels/wo/arte.png',
        'fanart': 'channels/wo/arte_fanart.jpg',
        'available_languages': ['FR', 'DE'],
        'xmltv_ids': {
            'FR': 'C111.api.telerama.fr'
        },
        'm3u_groups': {
            'FR': 'France TNT'
        },
        'm3u_orders': {
            'FR': 7
        },
        'enabled': True,
        'order': 3
    },
    'france24': {
        'resolver': '/resources/lib/channels/wo/france24:get_live_url',
        'label': 'France 24 (' + utils.ensure_unicode(Script.setting['france24.language']) + ')',
        'thumb': 'channels/wo/france24.png',
        'fanart': 'channels/wo/france24_fanart.jpg',
        'available_languages': ['FR', 'EN', 'AR', 'ES'],
        'enabled': True,
        'order': 4
    },
    'nhkworld': {
        'resolver': '/resources/lib/channels/wo/nhkworld:get_live_url',
        'label': 'NHK World (' + utils.ensure_unicode(Script.setting['nhkworld.language']) + ')',
        'thumb': 'channels/wo/nhkworld.png',
        'fanart': 'channels/wo/nhkworld_fanart.jpg',
        'available_languages': ['Outside Japan', 'In Japan'],
        'enabled': True,
        'order': 5
    },
    'tivi5monde': {
        'resolver': '/resources/lib/channels/wo/tivi5monde:get_live_url',
        'label': 'Tivi 5Monde',
        'thumb': 'channels/wo/tivi5monde.png',
        'fanart': 'channels/wo/tivi5monde_fanart.jpg',
        'enabled': True,
        'order': 7
    },
    'bvn': {
        'resolver': '/resources/lib/channels/wo/bvn:get_live_url',
        'label': 'BVN',
        'thumb': 'channels/wo/bvn.png',
        'fanart': 'channels/wo/bvn_fanart.jpg',
        'enabled': True,
        'order': 8
    },
    'icitelevision': {
        'resolver': '/resources/lib/channels/wo/icitelevision:get_live_url',
        'label': 'ICI Télévision',
        'thumb': 'channels/wo/icitelevision.png',
        'fanart': 'channels/wo/icitelevision_fanart.jpg',
        'enabled': True,
        'order': 9
    },
    'arirang': {
        'resolver': '/resources/lib/channels/wo/arirang:get_live_url',
        'label': 'Arirang (아리랑)',
        'thumb': 'channels/wo/arirang.png',
        'fanart': 'channels/wo/arirang_fanart.jpg',
        'enabled': True,
        'order': 11
    },
    'dw': {
        'resolver': '/resources/lib/channels/wo/dw:get_live_url',
        'label': 'DW (' + utils.ensure_unicode(Script.setting['dw.language']) + ')',
        'thumb': 'channels/wo/dw.png',
        'fanart': 'channels/wo/dw_fanart.jpg',
        'available_languages': ['EN', 'AR', 'ES', 'DE'],
        'enabled': True,
        'order': 12
    },
    'qvc': {
        'resolver': '/resources/lib/channels/wo/qvc:get_live_url',
        'label': 'QVC (' + utils.ensure_unicode(Script.setting['qvc.language']) + ')',
        'thumb': 'channels/wo/qvc.png',
        'fanart': 'channels/wo/qvc_fanart.jpg',
        'available_languages': ['JP', 'DE', 'IT', 'UK', 'US'],
        'enabled': True,
        'order': 15
    },
    'icirdi': {
        'resolver': '/resources/lib/channels/wo/icirdi:get_live_url',
        'label': 'ICI RDI',
        'thumb': 'channels/wo/icirdi.png',
        'fanart': 'channels/wo/icirdi_fanart.jpg',
        'enabled': True,
        'order': 16
    },
    'cgtn': {
        'resolver': '/resources/lib/channels/wo/cgtn:get_live_url',
        'label': 'CGTN (' + utils.ensure_unicode(Script.setting['cgtn.language']) + ')',
        'thumb': 'channels/wo/cgtn.png',
        'fanart': 'channels/wo/cgtn_fanart.jpg',
        'available_languages': ['FR', 'EN', 'AR', 'ES', 'RU'],
        'enabled': True,
        'order': 17
    },
    'cgtndocumentary': {
        'resolver': '/resources/lib/channels/wo/cgtn:get_live_url',
        'label': 'CGTN Documentary',
        'thumb': 'channels/wo/cgtndocumentary.png',
        'fanart': 'channels/wo/cgtndocumentary_fanart.jpg',
        'enabled': True,
        'order': 18
    },
    'afriquemedia': {
        'resolver': '/resources/lib/channels/wo/afriquemedia:get_live_url',
        'label': 'Afrique Media',
        'thumb': 'channels/wo/afriquemedia.png',
        'fanart': 'channels/wo/afriquemedia_fanart.jpg',
        'enabled': True,
        'order': 20
    },
    'tv5mondefbs': {
        'resolver': '/resources/lib/channels/wo/tv5monde:get_live_url',
        'label': 'TV5Monde France Belgique Suisse',
        'thumb': 'channels/wo/tv5mondefbs.png',
        'fanart': 'channels/wo/tv5mondefbs_fanart.jpg',
        'enabled': True,
        'order': 21
    },
    'tv5mondeinfo': {
        'resolver': '/resources/lib/channels/wo/tv5monde:get_live_url',
        'label': 'TV5Monde Info',
        'thumb': 'channels/wo/tv5mondeinfo.png',
        'fanart': 'channels/wo/tv5mondeinfo_fanart.jpg',
        'enabled': True,
        'order': 22
    },
    'channelnewsasia': {
        'resolver': '/resources/lib/channels/wo/channelnewsasia:get_live_url',
        'label': 'Channel NewsAsia',
        'thumb': 'channels/wo/channelnewsasia.png',
        'fanart': 'channels/wo/channelnewsasia_fanart.jpg',
        'enabled': True,
        'order': 23
    },
    'rt': {
        'resolver': '/resources/lib/channels/wo/rt:get_live_url',
        'label': 'RT (' + utils.ensure_unicode(Script.setting['rt.language']) + ')',
        'thumb': 'channels/wo/rt.png',
        'fanart': 'channels/wo/rt_fanart.jpg',
        'available_languages': ['FR', 'EN', 'AR', 'ES'],
        'enabled': True,
        'order': 24
    },
    'africa24': {
        'resolver': '/resources/lib/channels/wo/africa24:get_live_url',
        'label': 'Africa 24',
        'thumb': 'channels/wo/africa24.png',
        'fanart': 'channels/wo/africa24_fanart.jpg',
        'enabled': True,
        'order': 25
    }
}
