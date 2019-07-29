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
    'rtsun': {
        'callback': 'live_bridge',
        'thumb': 'channels/ch/rtsun.png',
        'fanart': 'channels/ch/rtsun_fanart.jpg',
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'rtsdeux': {
        'callback': 'live_bridge',
        'thumb': 'channels/ch/rtsdeux.png',
        'fanart': 'channels/ch/rtsdeux_fanart.jpg',
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'rtsinfo': {
        'callback': 'live_bridge',
        'thumb': 'channels/ch/rtsinfo.png',
        'fanart': 'channels/ch/rtsinfo_fanart.jpg',
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'rtscouleur3': {
        'callback': 'live_bridge',
        'thumb': 'channels/ch/rtscouleur3.png',
        'fanart': 'channels/ch/rtscouleur3_fanart.jpg',
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'rsila1': {
        'callback': 'live_bridge',
        'thumb': 'channels/ch/rsila1.png',
        'fanart': 'channels/ch/rsila1_fanart.jpg',
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'rsila2': {
        'callback': 'live_bridge',
        'thumb': 'channels/ch/rsila2.png',
        'fanart': 'channels/ch/rsila2_fanart.jpg',
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'srf1': {
        'callback': 'live_bridge',
        'thumb': 'channels/ch/srf1.png',
        'fanart': 'channels/ch/srf1_fanart.jpg',
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'srfinfo': {
        'callback': 'live_bridge',
        'thumb': 'channels/ch/srfinfo.png',
        'fanart': 'channels/ch/srfinfo_fanart.jpg',
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'srfzwei': {
        'callback': 'live_bridge',
        'thumb': 'channels/ch/srfzwei.png',
        'fanart': 'channels/ch/srfzwei_fanart.jpg',
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'rtraufsrf1': {
        'callback': 'live_bridge',
        'thumb': 'channels/ch/rtraufsrf1.png',
        'fanart': 'channels/ch/rtraufsrf1_fanart.jpg',
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'rtraufsrfinfo': {
        'callback': 'live_bridge',
        'thumb': 'channels/ch/rtraufsrfinfo.png',
        'fanart': 'channels/ch/rtraufsrfinfo_fanart.jpg',
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'rtraufsrf2': {
        'callback': 'live_bridge',
        'thumb': 'channels/ch/rtraufsrf2.png',
        'fanart': 'channels/ch/rtraufsrf2_fanart.jpg',
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'rougetv': {
        'callback': 'live_bridge',
        'thumb': 'channels/ch/rougetv.png',
        'fanart': 'channels/ch/rougetv_fanart.jpg',
        'module': 'resources.lib.channels.ch.rougetv'
    },
    'teleticino': {
        'callback': 'live_bridge',
        'thumb': 'channels/ch/teleticino.png',
        'fanart': 'channels/ch/teleticino_fanart.jpg',
        'module': 'resources.lib.channels.ch.teleticino'
    },
    'lemanbleu': {
        'callback': 'live_bridge',
        'thumb': 'channels/ch/lemanbleu.png',
        'fanart': 'channels/ch/lemanbleu_fanart.jpg',
        'module': 'resources.lib.channels.ch.lemanbleu'
    },
    'tvm3': {
        'callback': 'live_bridge',
        'thumb': 'channels/ch/tvm3.png',
        'fanart': 'channels/ch/tvm3_fanart.jpg',
        'module': 'resources.lib.channels.ch.tvm3'
    }
}
