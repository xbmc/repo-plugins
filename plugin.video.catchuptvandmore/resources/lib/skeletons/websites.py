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
    - callback: Callback function to run once this item is selected
    - thumb: Item thumb path relative to "media" folder
    - fanart: Item fanart path relative to "meia" folder
    - module: Item module to load in order to work (like 6play.py)
"""

menu = {
    'allocine': {
        'callback': 'website_bridge',
        'label': 'Allociné',
        'thumb': 'websites/allocine.png',
        'fanart': 'websites/allocine_fanart.jpg',
        'module': 'resources.lib.websites.allocine',
        'enabled': True,
        'order': 1
    },
    'tetesaclaques': {
        'callback': 'website_bridge',
        'label': 'Au pays des Têtes à claques',
        'thumb': 'websites/tetesaclaques.png',
        'fanart': 'websites/tetesaclaques_fanart.jpg',
        'module': 'resources.lib.websites.tetesaclaques',
        'enabled': True,
        'order': 2
    },
    'taratata': {
        'callback': 'website_bridge',
        'label': 'Taratata',
        'thumb': 'websites/taratata.png',
        'fanart': 'websites/taratata_fanart.jpg',
        'module': 'resources.lib.websites.taratata',
        'enabled': True,
        'order': 3
    },
    'noob': {
        'callback': 'website_bridge',
        'label': 'Noob TV',
        'thumb': 'websites/noob.png',
        'fanart': 'websites/noob_fanart.jpg',
        'module': 'resources.lib.websites.noob',
        'enabled': True,
        'order': 4
    },
    'culturepub': {
        'callback': 'website_bridge',
        'label': 'Culturepub',
        'thumb': 'websites/culturepub.png',
        'fanart': 'websites/culturepub_fanart.jpg',
        'module': 'resources.lib.websites.culturepub',
        'enabled': True,
        'order': 5
    },
    'autoplus': {
        'callback': 'website_bridge',
        'label': 'Auto Plus',
        'thumb': 'websites/autoplus.png',
        'fanart': 'websites/autoplus_fanart.jpg',
        'module': 'resources.lib.websites.autoplus',
        'enabled': True,
        'order': 6
    },
    'notrehistoirech': {
        'callback': 'website_bridge',
        'label': 'Notre Histoire',
        'thumb': 'websites/notrehistoirech.png',
        'fanart': 'websites/notrehistoirech_fanart.jpg',
        'module': 'resources.lib.websites.notrehistoirech',
        'enabled': True,
        'order': 7
    },
    '30millionsdamis': {
        'callback': 'website_bridge',
        'label': '30 Millions d\'Amis',
        'thumb': 'websites/30millionsdamis.png',
        'fanart': 'websites/30millionsdamis_fanart.jpg',
        'module': 'resources.lib.websites.30millionsdamis',
        'enabled': True,
        'order': 8
    },
    'elle': {
        'callback': 'website_bridge',
        'label': 'Elle',
        'thumb': 'websites/elle.png',
        'fanart': 'websites/elle_fanart.jpg',
        'module': 'resources.lib.websites.elle',
        'enabled': True,
        'order': 9
    },
    'nytimes': {
        'callback': 'website_bridge',
        'label': 'New York Times',
        'thumb': 'websites/nytimes.png',
        'fanart': 'websites/nytimes_fanart.jpg',
        'module': 'resources.lib.websites.nytimes',
        'enabled': True,
        'order': 10
    },
    'fosdem': {
        'callback': 'website_bridge',
        'label': 'Fosdem',
        'thumb': 'websites/fosdem.png',
        'fanart': 'websites/fosdem_fanart.jpg',
        'module': 'resources.lib.websites.fosdem',
        'enabled': True,
        'order': 11
    },
    'ina': {
        'callback': 'website_bridge',
        'label': 'Ina',
        'thumb': 'websites/ina.png',
        'fanart': 'websites/ina_fanart.jpg',
        'module': 'resources.lib.websites.ina',
        'enabled': True,
        'order': 12
    },
    'onf': {
        'callback': 'website_bridge',
        'label': 'Office National du Film du Canada',
        'thumb': 'websites/onf.png',
        'fanart': 'websites/onf_fanart.jpg',
        'module': 'resources.lib.websites.onf',
        'enabled': True,
        'order': 13
    },
    'nfb': {
        'callback': 'website_bridge',
        'label': 'National Film Board Of Canada',
        'thumb': 'websites/nfb.png',
        'fanart': 'websites/nfb_fanart.jpg',
        'module': 'resources.lib.websites.nfb',
        'enabled': True,
        'order': 14
    },
    'marmiton': {
        'callback': 'website_bridge',
        'label': 'Marmiton',
        'thumb': 'websites/marmiton.png',
        'fanart': 'websites/marmiton_fanart.jpg',
        'module': 'resources.lib.websites.marmiton',
        'enabled': True,
        'order': 15
    },
    'lesargonautes': {
        'callback': 'website_bridge',
        'label': 'Les Argonautes',
        'thumb': 'websites/lesargonautes.png',
        'fanart': 'websites/lesargonautes_fanart.jpg',
        'module': 'resources.lib.websites.lesargonautes',
        'enabled': True,
        'order': 16
    },
    'nationalfff': {
        'callback': 'website_bridge',
        'label': 'National FFF',
        'thumb': 'websites/nationalfff.png',
        'fanart': 'websites/nationalfff_fanart.jpg',
        'module': 'resources.lib.websites.nationalfff',
        'enabled': True,
        'order': 17
    },
    'philharmoniedeparis': {
        'callback': 'website_bridge',
        'label': 'Philharmonie de Paris',
        'thumb': 'websites/philharmoniedeparis.png',
        'fanart': 'websites/philharmoniedeparis_fanart.jpg',
        'module': 'resources.lib.websites.philharmoniedeparis',
        'enabled': True,
        'order': 18
    }
}
