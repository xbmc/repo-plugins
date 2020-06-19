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
    - callback: Callback function to run once this item is selected
    - thumb: Item thumb path relative to "media" folder
    - fanart: Item fanart path relative to "meia" folder
    - module: Item module to load in order to work (like 6play.py)
"""

menu = {
    'euronews': {
        'callback':
        'live_bridge',
        'label': 'Euronews (' + utils.ensure_unicode(Script.setting['euronews.language']) + ')',
        'thumb':
        'channels/wo/euronews.png',
        'fanart':
        'channels/wo/euronews_fanart.jpg',
        'module':
        'resources.lib.channels.wo.euronews',
        'available_languages': [
            'FR', 'EN', 'AR', 'DE', 'IT', 'ES', 'PT', 'RU', 'TR', 'FA', 'GR',
            'HU'
        ],
        'enabled': True,
        'order': 2
    },
    'arte': {
        'callback': 'live_bridge',
        'label': 'Arte (' + utils.ensure_unicode(Script.setting['arte.language']) + ')',
        'thumb': 'channels/wo/arte.png',
        'fanart': 'channels/wo/arte_fanart.jpg',
        'module': 'resources.lib.channels.wo.arte',
        'available_languages': ['FR', 'DE'],
        'xmltv_ids': {
            'fr': 'C111.api.telerama.fr'
        },
        'm3u_groups': {
            'fr': 'France TNT'
        },
        'm3u_orders': {
            'fr': 7
        },
        'enabled': True,
        'order': 3
    },
    'france24': {
        'callback': 'live_bridge',
        'label': 'France 24 (' + utils.ensure_unicode(Script.setting['france24.language']) + ')',
        'thumb': 'channels/wo/france24.png',
        'fanart': 'channels/wo/france24_fanart.jpg',
        'module': 'resources.lib.channels.wo.france24',
        'available_languages': ['FR', 'EN', 'AR', 'ES'],
        'enabled': True,
        'order': 4
    },
    'nhkworld': {
        'callback': 'live_bridge',
        'label': 'NHK World (' + utils.ensure_unicode(Script.setting['nhkworld.language']) + ')',
        'thumb': 'channels/wo/nhkworld.png',
        'fanart': 'channels/wo/nhkworld_fanart.jpg',
        'module': 'resources.lib.channels.wo.nhkworld',
        'available_languages': ['Outside Japan', 'In Japan'],
        'enabled': True,
        'order': 5
    },
    'tivi5monde': {
        'callback': 'live_bridge',
        'label': 'Tivi 5Monde',
        'thumb': 'channels/wo/tivi5monde.png',
        'fanart': 'channels/wo/tivi5monde_fanart.jpg',
        'module': 'resources.lib.channels.wo.tivi5monde',
        'enabled': True,
        'order': 7
    },
    'bvn': {
        'callback': 'live_bridge',
        'label': 'BVN',
        'thumb': 'channels/wo/bvn.png',
        'fanart': 'channels/wo/bvn_fanart.jpg',
        'module': 'resources.lib.channels.wo.bvn',
        'enabled': True,
        'order': 8
    },
    'icitelevision': {
        'callback': 'live_bridge',
        'label': 'ICI Télévision',
        'thumb': 'channels/wo/icitelevision.png',
        'fanart': 'channels/wo/icitelevision_fanart.jpg',
        'module': 'resources.lib.channels.wo.icitelevision',
        'enabled': True,
        'order': 9
    },
    'arirang': {
        'callback': 'live_bridge',
        'label': 'Arirang (아리랑)',
        'thumb': 'channels/wo/arirang.png',
        'fanart': 'channels/wo/arirang_fanart.jpg',
        'module': 'resources.lib.channels.wo.arirang',
        'enabled': True,
        'order': 11
    },
    'dw': {
        'callback': 'live_bridge',
        'label': 'DW (' + utils.ensure_unicode(Script.setting['dw.language']) + ')',
        'thumb': 'channels/wo/dw.png',
        'fanart': 'channels/wo/dw_fanart.jpg',
        'module': 'resources.lib.channels.wo.dw',
        'available_languages': ['EN', 'AR', 'ES', 'DE'],
        'enabled': True,
        'order': 12
    },
    'qvc': {
        'callback': 'live_bridge',
        'label': 'QVC (' + utils.ensure_unicode(Script.setting['qvc.language']) + ')',
        'thumb': 'channels/wo/qvc.png',
        'fanart': 'channels/wo/qvc_fanart.jpg',
        'module': 'resources.lib.channels.wo.qvc',
        'available_languages': ['JP', 'DE', 'IT', 'UK', 'US'],
        'enabled': True,
        'order': 15
    },
    'icirdi': {
        'callback': 'live_bridge',
        'label': 'ICI RDI',
        'thumb': 'channels/wo/icirdi.png',
        'fanart': 'channels/wo/icirdi_fanart.jpg',
        'module': 'resources.lib.channels.wo.icirdi',
        'enabled': True,
        'order': 16
    },
    'cgtn': {
        'callback': 'live_bridge',
        'label': 'CGTN (' + utils.ensure_unicode(Script.setting['cgtn.language']) + ')',
        'thumb': 'channels/wo/cgtn.png',
        'fanart': 'channels/wo/cgtn_fanart.jpg',
        'module': 'resources.lib.channels.wo.cgtn',
        'available_languages': ['FR', 'EN', 'AR', 'ES', 'RU'],
        'enabled': True,
        'order': 17
    },
    'cgtndocumentary': {
        'callback': 'live_bridge',
        'label': 'CGTN Documentary',
        'thumb': 'channels/wo/cgtndocumentary.png',
        'fanart': 'channels/wo/cgtndocumentary_fanart.jpg',
        'module': 'resources.lib.channels.wo.cgtn',
        'enabled': True,
        'order': 18
    },
    'afriquemedia': {
        'callback': 'live_bridge',
        'label': 'Afrique Media',
        'thumb': 'channels/wo/afriquemedia.png',
        'fanart': 'channels/wo/afriquemedia_fanart.jpg',
        'module': 'resources.lib.channels.wo.afriquemedia',
        'enabled': True,
        'order': 20
    },
    'tv5mondefbs': {
        'callback': 'live_bridge',
        'label': 'TV5Monde France Belgique Suisse',
        'thumb': 'channels/wo/tv5mondefbs.png',
        'fanart': 'channels/wo/tv5mondefbs_fanart.jpg',
        'module': 'resources.lib.channels.wo.tv5monde',
        'enabled': True,
        'order': 21
    },
    'tv5mondeinfo': {
        'callback': 'live_bridge',
        'label': 'TV5Monde Info',
        'thumb': 'channels/wo/tv5mondeinfo.png',
        'fanart': 'channels/wo/tv5mondeinfo_fanart.jpg',
        'module': 'resources.lib.channels.wo.tv5monde',
        'enabled': True,
        'order': 22
    },
    'channelnewsasia': {
        'callback': 'live_bridge',
        'label': 'Channel NewsAsia',
        'thumb': 'channels/wo/channelnewsasia.png',
        'fanart': 'channels/wo/channelnewsasia_fanart.jpg',
        'module': 'resources.lib.channels.wo.channelnewsasia',
        'enabled': True,
        'order': 23
    },
    'rt': {
        'callback': 'live_bridge',
        'label': 'RT (' + utils.ensure_unicode(Script.setting['rt.language']) + ')',
        'thumb': 'channels/wo/rt.png',
        'fanart': 'channels/wo/rt_fanart.jpg',
        'module': 'resources.lib.channels.wo.rt',
        'available_languages': ['FR', 'EN', 'AR', 'ES'],
        'enabled': True,
        'order': 24
    },
    'africa24': {
        'callback': 'live_bridge',
        'label': 'Africa 24',
        'thumb': 'channels/wo/africa24.png',
        'fanart': 'channels/wo/africa24_fanart.jpg',
        'module': 'resources.lib.channels.wo.africa24',
        'enabled': True,
        'order': 25
    }
}
