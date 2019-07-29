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
        'thumb': 'websites/allocine.png',
        'fanart': 'websites/allocine_fanart.jpg',
        'module': 'resources.lib.websites.allocine'
    },
    'tetesaclaques': {
        'callback': 'website_bridge',
        'thumb': 'websites/tetesaclaques.png',
        'fanart': 'websites/tetesaclaques_fanart.jpg',
        'module': 'resources.lib.websites.tetesaclaques'
    },
    'taratata': {
        'callback': 'website_bridge',
        'thumb': 'websites/taratata.png',
        'fanart': 'websites/taratata_fanart.jpg',
        'module': 'resources.lib.websites.taratata'
    },
    'onf': {
        'callback': 'website_bridge',
        'thumb': 'websites/onf.png',
        'fanart': 'websites/onf_fanart.jpg',
        'module': 'resources.lib.websites.onf'
    },
    'nytimes': {
        'callback': 'website_bridge',
        'thumb': 'websites/nytimes.png',
        'fanart': 'websites/nytimes_fanart.jpg',
        'module': 'resources.lib.websites.nytimes'
    },
    'notrehistoirech': {
        'callback': 'website_bridge',
        'thumb': 'websites/notrehistoirech.png',
        'fanart': 'websites/notrehistoirech_fanart.jpg',
        'module': 'resources.lib.websites.notrehistoirech'
    },
    'noob': {
        'callback': 'website_bridge',
        'thumb': 'websites/noob.png',
        'fanart': 'websites/noob_fanart.jpg',
        'module': 'resources.lib.websites.noob'
    },
    'nfb': {
        'callback': 'website_bridge',
        'thumb': 'websites/nfb.png',
        'fanart': 'websites/nfb_fanart.jpg',
        'module': 'resources.lib.websites.nfb'
    },
    'ina': {
        'callback': 'website_bridge',
        'thumb': 'websites/ina.png',
        'fanart': 'websites/ina_fanart.jpg',
        'module': 'resources.lib.websites.ina'
    },
    'fosdem': {
        'callback': 'website_bridge',
        'thumb': 'websites/fosdem.png',
        'fanart': 'websites/fosdem_fanart.jpg',
        'module': 'resources.lib.websites.fosdem'
    },
    'elle': {
        'callback': 'website_bridge',
        'thumb': 'websites/elle.png',
        'fanart': 'websites/elle_fanart.jpg',
        'module': 'resources.lib.websites.elle'
    },
    'culturepub': {
        'callback': 'website_bridge',
        'thumb': 'websites/culturepub.png',
        'fanart': 'websites/culturepub_fanart.jpg',
        'module': 'resources.lib.websites.culturepub'
    },
    'autoplus': {
        'callback': 'website_bridge',
        'thumb': 'websites/autoplus.png',
        'fanart': 'websites/autoplus_fanart.jpg',
        'module': 'resources.lib.websites.autoplus'
    },
    '30millionsdamis': {
        'callback': 'website_bridge',
        'thumb': 'websites/30millionsdamis.png',
        'fanart': 'websites/30millionsdamis_fanart.jpg',
        'module': 'resources.lib.websites.30millionsdamis'
    },
    'marmiton': {
        'callback': 'website_bridge',
        'thumb': 'websites/marmiton.png',
        'fanart': 'websites/marmiton_fanart.jpg',
        'module': 'resources.lib.websites.marmiton'
    },
    'lesargonautes': {
        'callback': 'website_bridge',
        'thumb': 'websites/lesargonautes.png',
        'fanart': 'websites/lesargonautes_fanart.jpg',
        'module': 'resources.lib.websites.lesargonautes'
    },
    'nationalfff': {
        'callback': 'website_bridge',
        'thumb': 'websites/nationalfff.png',
        'fanart': 'websites/nationalfff_fanart.jpg',
        'module': 'resources.lib.websites.nationalfff'
    },
    'philharmoniedeparis': {
        'callback': 'website_bridge',
        'thumb': 'websites/philharmoniedeparis.png',
        'fanart': 'websites/philharmoniedeparis_fanart.jpg',
        'module': 'resources.lib.websites.philharmoniedeparis'
    }
}
