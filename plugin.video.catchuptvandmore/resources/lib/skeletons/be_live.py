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
    'rtl_tvi': {
        'callback': 'live_bridge',
        'thumb': 'channels/be/rtltvi.png',
        'fanart': 'channels/be/rtltvi_fanart.jpg',
        'module': 'resources.lib.channels.be.rtlplaybe',
        'xmltv_id': 'C168.api.telerama.fr',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 2
    },
    'plug_rtl': {
        'callback': 'live_bridge',
        'thumb': 'channels/be/plugrtl.png',
        'fanart': 'channels/be/plugrtl_fanart.jpg',
        'module': 'resources.lib.channels.be.rtlplaybe',
        'xmltv_id': 'C377.api.telerama.fr',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 3
    },
    'club_rtl': {
        'callback': 'live_bridge',
        'thumb': 'channels/be/clubrtl.png',
        'fanart': 'channels/be/clubrtl_fanart.jpg',
        'module': 'resources.lib.channels.be.rtlplaybe',
        'xmltv_id': 'C50.api.telerama.fr',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 4
    },
    'telemb': {
        'callback': 'live_bridge',
        'thumb': 'channels/be/telemb.png',
        'fanart': 'channels/be/telemb_fanart.jpg',
        'module': 'resources.lib.channels.be.telemb',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 6
    },
    'rtc': {
        'callback': 'live_bridge',
        'thumb': 'channels/be/rtc.png',
        'fanart': 'channels/be/rtc_fanart.jpg',
        'module': 'resources.lib.channels.be.rtc',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 7
    },
    'auvio': {
        'callback': 'multi_live_bridge',
        'thumb': 'channels/be/auvio.png',
        'fanart': 'channels/be/auvio_fanart.jpg',
        'module': 'resources.lib.channels.be.rtbf',
        'enabled': True,
        'order': 8
    },
    'tvlux': {
        'callback': 'live_bridge',
        'thumb': 'channels/be/tvlux.png',
        'fanart': 'channels/be/tvlux_fanart.jpg',
        'module': 'resources.lib.channels.be.tvlux',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 9
    },
    'rtl_info': {
        'callback': 'live_bridge',
        'thumb': 'channels/be/rtlinfo.png',
        'fanart': 'channels/be/rtlinfo_fanart.jpg',
        'module': 'resources.lib.channels.be.rtlplaybe',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 10
    },
    'bel_rtl': {
        'callback': 'live_bridge',
        'thumb': 'channels/be/belrtl.png',
        'fanart': 'channels/be/belrtl_fanart.jpg',
        'module': 'resources.lib.channels.be.rtlplaybe',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 11
    },
    'contact': {
        'callback': 'live_bridge',
        'thumb': 'channels/be/contact.png',
        'fanart': 'channels/be/contact_fanart.jpg',
        'module': 'resources.lib.channels.be.rtlplaybe',
        'm3u_group': 'Belgique fr Radio',
        'enabled': True,
        'order': 12
    },
    'bx1': {
        'callback': 'live_bridge',
        'thumb': 'channels/be/bx1.png',
        'fanart': 'channels/be/bx1_fanart.jpg',
        'module': 'resources.lib.channels.be.bx1',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 13
    },
    'een': {
        'callback': 'live_bridge',
        'thumb': 'channels/be/een.png',
        'fanart': 'channels/be/een_fanart.jpg',
        'module': 'resources.lib.channels.be.vrt',
        'xmltv_id': 'C23.api.telerama.fr',
        'm3u_group': 'België nl',
        'enabled': True,
        'order': 14
    },
    'canvas': {
        'callback': 'live_bridge',
        'thumb': 'channels/be/canvas.png',
        'fanart': 'channels/be/canvas_fanart.jpg',
        'module': 'resources.lib.channels.be.vrt',
        'm3u_group': 'België nl',
        'enabled': True,
        'order': 15
    },
    'ketnet': {
        'callback': 'live_bridge',
        'thumb': 'channels/be/ketnet.png',
        'fanart': 'channels/be/ketnet_fanart.jpg',
        'module': 'resources.lib.channels.be.vrt',
        'xmltv_id': 'C1280.api.telerama.fr',
        'm3u_group': 'België nl',
        'enabled': True,
        'order': 16
    },
    'nrjhitstvbe': {
        'callback': 'live_bridge',
        'thumb': 'channels/be/nrjhitstvbe.png',
        'fanart': 'channels/be/nrjhitstvbe_fanart.jpg',
        'module': 'resources.lib.channels.be.nrjhitstvbe',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 17
    },
    'rtl_sport': {
        'callback': 'live_bridge',
        'thumb': 'channels/be/rtlsport.png',
        'fanart': 'channels/be/rtlsport_fanart.jpg',
        'module': 'resources.lib.channels.be.rtlplaybe',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 18
    },
    'tvcom': {
        'callback': 'live_bridge',
        'thumb': 'channels/be/tvcom.png',
        'fanart': 'channels/be/tvcom_fanart.jpg',
        'module': 'resources.lib.channels.be.tvcom',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 19
    },
    'canalc': {
        'callback': 'live_bridge',
        'thumb': 'channels/be/canalc.png',
        'fanart': 'channels/be/canalc_fanart.jpg',
        'module': 'resources.lib.channels.be.canalc',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 20
    },
    'abxplore': {
        'callback': 'live_bridge',
        'thumb': 'channels/be/abxplore.png',
        'fanart': 'channels/be/abxplore_fanart.jpg',
        'module': 'resources.lib.channels.be.abbe',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 21
    },
    'ab3': {
        'callback': 'live_bridge',
        'thumb': 'channels/be/ab3.png',
        'fanart': 'channels/be/ab3_fanart.jpg',
        'module': 'resources.lib.channels.be.abbe',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 22
    }
}
