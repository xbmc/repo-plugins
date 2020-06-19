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
    'tv5mondeafrique': {
        'callback': 'replay_bridge',
        'label': 'TV5Monde Afrique',
        'thumb': 'channels/wo/tv5mondeafrique.png',
        'fanart': 'channels/wo/tv5mondeafrique_fanart.jpg',
        'module': 'resources.lib.channels.wo.tv5mondeafrique',
        'enabled': True,
        'order': 1
    },
    'arte': {
        'callback': 'replay_bridge',
        'label': 'Arte (' + utils.ensure_unicode(Script.setting['arte.language']) + ')',
        'thumb': 'channels/wo/arte.png',
        'fanart': 'channels/wo/arte_fanart.jpg',
        'module': 'resources.lib.channels.wo.arte',
        'enabled': True,
        'order': 3
    },
    'france24': {
        'callback': 'replay_bridge',
        'label': 'France 24 (' + utils.ensure_unicode(Script.setting['france24.language']) + ')',
        'thumb': 'channels/wo/france24.png',
        'fanart': 'channels/wo/france24_fanart.jpg',
        'module': 'resources.lib.channels.wo.france24',
        'enabled': True,
        'order': 4
    },
    'nhkworld': {
        'callback': 'replay_bridge',
        'label': 'NHK World (' + utils.ensure_unicode(Script.setting['nhkworld.language']) + ')',
        'thumb': 'channels/wo/nhkworld.png',
        'fanart': 'channels/wo/nhkworld_fanart.jpg',
        'module': 'resources.lib.channels.wo.nhkworld',
        'enabled': True,
        'order': 5
    },
    'tv5monde': {
        'callback': 'replay_bridge',
        'label': 'TV5Monde',
        'thumb': 'channels/wo/tv5monde.png',
        'fanart': 'channels/wo/tv5monde_fanart.jpg',
        'module': 'resources.lib.channels.wo.tv5monde',
        'enabled': True,
        'order': 6
    },
    'tivi5monde': {
        'callback': 'replay_bridge',
        'label': 'Tivi 5Monde',
        'thumb': 'channels/wo/tivi5monde.png',
        'fanart': 'channels/wo/tivi5monde_fanart.jpg',
        'module': 'resources.lib.channels.wo.tivi5monde',
        'enabled': True,
        'order': 7
    },
    'bvn': {
        'callback': 'replay_bridge',
        'label': 'BVN',
        'thumb': 'channels/wo/bvn.png',
        'fanart': 'channels/wo/bvn_fanart.jpg',
        'module': 'resources.lib.channels.wo.bvn',
        'enabled': True,
        'order': 8
    },
    'arirang': {
        'callback': 'replay_bridge',
        'label': 'Arirang (아리랑)',
        'thumb': 'channels/wo/arirang.png',
        'fanart': 'channels/wo/arirang_fanart.jpg',
        'module': 'resources.lib.channels.wo.arirang',
        'enabled': True,
        'order': 11
    },
    'beinsports': {
        'callback': 'replay_bridge',
        'label': 'Bein Sports',
        'thumb': 'channels/wo/beinsports.png',
        'fanart': 'channels/wo/beinsports_fanart.jpg',
        'module': 'resources.lib.channels.wo.beinsports',
        'enabled': True,
        'order': 13
    },
    'afriquemedia': {
        'callback': 'replay_bridge',
        'label': 'Afrique Media',
        'thumb': 'channels/wo/afriquemedia.png',
        'fanart': 'channels/wo/afriquemedia_fanart.jpg',
        'module': 'resources.lib.channels.wo.afriquemedia',
        'enabled': True,
        'order': 20
    },
    'channelnewsasia': {
        'callback': 'replay_bridge',
        'label': 'Channel NewsAsia',
        'thumb': 'channels/wo/channelnewsasia.png',
        'fanart': 'channels/wo/channelnewsasia_fanart.jpg',
        'module': 'resources.lib.channels.wo.channelnewsasia',
        'enabled': True,
        'order': 23
    },
    'rt': {
        'callback': 'replay_bridge',
        'label': 'RT (' + utils.ensure_unicode(Script.setting['rt.language']) + ')',
        'thumb': 'channels/wo/rt.png',
        'fanart': 'channels/wo/rt_fanart.jpg',
        'module': 'resources.lib.channels.wo.rt',
        'available_languages': ['FR', 'EN'],
        'enabled': True,
        'order': 24
    },
    'africa24': {
        'callback': 'replay_bridge',
        'label': 'Africa 24',
        'thumb': 'channels/wo/africa24.png',
        'fanart': 'channels/wo/africa24_fanart.jpg',
        'module': 'resources.lib.channels.wo.africa24',
        'enabled': True,
        'order': 25
    }
}
