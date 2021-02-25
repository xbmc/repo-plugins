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
from codequick import Script
"""
The following dictionaries describe
the addon's tree architecture.
* Key: item id
* Value: item infos
    - route (folder)/resolver (playable URL): Callback function to run once this item is selected
    - thumb: Item thumb path relative to "media" folder
    - fanart: Item fanart path relative to "meia" folder
"""

root = 'root'

menu = {
    'allocine': {
        'route': '/resources/lib/websites/allocine:website_root',
        'label': 'Allociné',
        'thumb': 'websites/allocine.png',
        'fanart': 'websites/allocine_fanart.jpg',
        'enabled': True,
        'order': 1
    },
    'tetesaclaques': {
        'route': '/resources/lib/websites/tetesaclaques:website_root',
        'label': 'Au pays des Têtes à claques',
        'thumb': 'websites/tetesaclaques.png',
        'fanart': 'websites/tetesaclaques_fanart.jpg',
        'enabled': True,
        'order': 2
    },
    'taratata': {
        'route': '/resources/lib/websites/taratata:website_root',
        'label': 'Taratata',
        'thumb': 'websites/taratata.png',
        'fanart': 'websites/taratata_fanart.jpg',
        'enabled': True,
        'order': 3
    },
    'noob': {
        'route': '/resources/lib/websites/noob:website_root',
        'label': 'Noob TV',
        'thumb': 'websites/noob.png',
        'fanart': 'websites/noob_fanart.jpg',
        'enabled': True,
        'order': 4
    },
    'culturepub': {
        'route': '/resources/lib/websites/culturepub:website_root',
        'label': 'Culturepub',
        'thumb': 'websites/culturepub.png',
        'fanart': 'websites/culturepub_fanart.jpg',
        'enabled': True,
        'order': 5
    },
    'autoplus': {
        'route': '/resources/lib/websites/autoplus:website_root',
        'label': 'Auto Plus',
        'thumb': 'websites/autoplus.png',
        'fanart': 'websites/autoplus_fanart.jpg',
        'enabled': True,
        'order': 6
    },
    'notrehistoirech': {
        'route': '/resources/lib/websites/notrehistoirech:website_root',
        'label': 'Notre Histoire',
        'thumb': 'websites/notrehistoirech.png',
        'fanart': 'websites/notrehistoirech_fanart.jpg',
        'enabled': True,
        'order': 7
    },
    '30millionsdamis': {
        'route': '/resources/lib/websites/30millionsdamis:website_root',
        'label': '30 Millions d\'Amis',
        'thumb': 'websites/30millionsdamis.png',
        'fanart': 'websites/30millionsdamis_fanart.jpg',
        'enabled': True,
        'order': 8
    },
    'elle': {
        'route': '/resources/lib/websites/elle:website_root',
        'label': 'Elle',
        'thumb': 'websites/elle.png',
        'fanart': 'websites/elle_fanart.jpg',
        'enabled': True,
        'order': 9
    },
    'nytimes': {
        'route': '/resources/lib/websites/nytimes:website_root',
        'label': 'New York Times',
        'thumb': 'websites/nytimes.png',
        'fanart': 'websites/nytimes_fanart.jpg',
        'enabled': True,
        'order': 10
    },
    'fosdem': {
        'route': '/resources/lib/websites/fosdem:website_root',
        'label': 'Fosdem',
        'thumb': 'websites/fosdem.png',
        'fanart': 'websites/fosdem_fanart.jpg',
        'enabled': True,
        'order': 11
    },
    'ina': {
        'route': '/resources/lib/websites/ina:website_root',
        'label': 'Ina',
        'thumb': 'websites/ina.png',
        'fanart': 'websites/ina_fanart.jpg',
        'enabled': True,
        'order': 12
    },
    'onf': {
        'route': '/resources/lib/websites/onf:website_root',
        'label': 'Office National du Film du Canada',
        'thumb': 'websites/onf.png',
        'fanart': 'websites/onf_fanart.jpg',
        'enabled': True,
        'order': 13
    },
    'nfb': {
        'route': '/resources/lib/websites/nfb:website_root',
        'label': 'National Film Board Of Canada',
        'thumb': 'websites/nfb.png',
        'fanart': 'websites/nfb_fanart.jpg',
        'enabled': True,
        'order': 14
    },
    'marmiton': {
        'route': '/resources/lib/websites/marmiton:website_root',
        'label': 'Marmiton',
        'thumb': 'websites/marmiton.png',
        'fanart': 'websites/marmiton_fanart.jpg',
        'enabled': True,
        'order': 15
    },
    'lesargonautes': {
        'route': '/resources/lib/websites/lesargonautes:website_root',
        'label': 'Les Argonautes',
        'thumb': 'websites/lesargonautes.png',
        'fanart': 'websites/lesargonautes_fanart.jpg',
        'enabled': True,
        'order': 16
    },
    'nationalfff': {
        'route': '/resources/lib/websites/nationalfff:website_root',
        'label': 'National FFF',
        'thumb': 'websites/nationalfff.png',
        'fanart': 'websites/nationalfff_fanart.jpg',
        'enabled': True,
        'order': 17
    },
    'philharmoniedeparis': {
        'route': '/resources/lib/websites/philharmoniedeparis:website_root',
        'label': 'Philharmonie de Paris',
        'thumb': 'websites/philharmoniedeparis.png',
        'fanart': 'websites/philharmoniedeparis_fanart.jpg',
        'enabled': True,
        'order': 18
    }
}
