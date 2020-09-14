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

menu = {
    'rtl_tvi': {
        'resolver': '/resources/lib/channels/be/rtlplaybe:get_live_url',
        'label': 'RTL-TVI',
        'thumb': 'channels/be/rtltvi.png',
        'fanart': 'channels/be/rtltvi_fanart.jpg',
        'xmltv_id': 'C168.api.telerama.fr',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 2
    },
    'plug_rtl': {
        'resolver': '/resources/lib/channels/be/rtlplaybe:get_live_url',
        'label': 'PLUG RTL',
        'thumb': 'channels/be/plugrtl.png',
        'fanart': 'channels/be/plugrtl_fanart.jpg',
        'xmltv_id': 'C377.api.telerama.fr',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 3
    },
    'club_rtl': {
        'resolver': '/resources/lib/channels/be/rtlplaybe:get_live_url',
        'label': 'CLUB RTL',
        'thumb': 'channels/be/clubrtl.png',
        'fanart': 'channels/be/clubrtl_fanart.jpg',
        'xmltv_id': 'C50.api.telerama.fr',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 4
    },
    'telemb': {
        'resolver': '/resources/lib/channels/be/telemb:get_live_url',
        'label': 'Télé MB',
        'thumb': 'channels/be/telemb.png',
        'fanart': 'channels/be/telemb_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 6
    },
    'rtc': {
        'resolver': '/resources/lib/channels/be/rtc:get_live_url',
        'label': 'RTC Télé Liège',
        'thumb': 'channels/be/rtc.png',
        'fanart': 'channels/be/rtc_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 7
    },
    'auvio': {
        'route': '/resources/lib/channels/be/rtbf:list_lives',
        'label': 'RTBF Auvio',
        'thumb': 'channels/be/auvio.png',
        'fanart': 'channels/be/auvio_fanart.jpg',
        'enabled': True,
        'order': 8
    },
    'tvlux': {
        'resolver': '/resources/lib/channels/be/tvlux:get_live_url',
        'label': 'TV Lux',
        'thumb': 'channels/be/tvlux.png',
        'fanart': 'channels/be/tvlux_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 9
    },
    'rtl_info': {
        'resolver': '/resources/lib/channels/be/rtlplaybe:get_live_url',
        'label': 'RTL INFO',
        'thumb': 'channels/be/rtlinfo.png',
        'fanart': 'channels/be/rtlinfo_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 10
    },
    'bel_rtl': {
        'resolver': '/resources/lib/channels/be/rtlplaybe:get_live_url',
        'label': 'BEL RTL',
        'thumb': 'channels/be/belrtl.png',
        'fanart': 'channels/be/belrtl_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 11
    },
    'contact': {
        'resolver': '/resources/lib/channels/be/rtlplaybe:get_live_url',
        'label': 'Contact',
        'thumb': 'channels/be/contact.png',
        'fanart': 'channels/be/contact_fanart.jpg',
        'm3u_group': 'Belgique fr Radio',
        'enabled': True,
        'order': 12
    },
    'bx1': {
        'resolver': '/resources/lib/channels/be/bx1:get_live_url',
        'label': 'BX1',
        'thumb': 'channels/be/bx1.png',
        'fanart': 'channels/be/bx1_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 13
    },
    'een': {
        'resolver': '/resources/lib/channels/be/vrt:get_live_url',
        'label': 'Één',
        'thumb': 'channels/be/een.png',
        'fanart': 'channels/be/een_fanart.jpg',
        'xmltv_id': 'C23.api.telerama.fr',
        'm3u_group': 'België nl',
        'enabled': True,
        'order': 14
    },
    'canvas': {
        'resolver': '/resources/lib/channels/be/vrt:get_live_url',
        'label': 'Canvas',
        'thumb': 'channels/be/canvas.png',
        'fanart': 'channels/be/canvas_fanart.jpg',
        'm3u_group': 'België nl',
        'enabled': True,
        'order': 15
    },
    'ketnet': {
        'resolver': '/resources/lib/channels/be/vrt:get_live_url',
        'label': 'Ketnet',
        'thumb': 'channels/be/ketnet.png',
        'fanart': 'channels/be/ketnet_fanart.jpg',
        'xmltv_id': 'C1280.api.telerama.fr',
        'm3u_group': 'België nl',
        'enabled': True,
        'order': 16
    },
    'nrjhitstvbe': {
        'resolver': '/resources/lib/channels/be/nrjhitstvbe:get_live_url',
        'label': 'NRJ Hits TV',
        'thumb': 'channels/be/nrjhitstvbe.png',
        'fanart': 'channels/be/nrjhitstvbe_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 17
    },
    'rtl_sport': {
        'resolver': '/resources/lib/channels/be/rtlplaybe:get_live_url',
        'label': 'RTL Sport',
        'thumb': 'channels/be/rtlsport.png',
        'fanart': 'channels/be/rtlsport_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 18
    },
    'tvcom': {
        'resolver': '/resources/lib/channels/be/tvcom:get_live_url',
        'label': 'TV Com',
        'thumb': 'channels/be/tvcom.png',
        'fanart': 'channels/be/tvcom_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 19
    },
    'canalc': {
        'resolver': '/resources/lib/channels/be/canalc:get_live_url',
        'label': 'Canal C',
        'thumb': 'channels/be/canalc.png',
        'fanart': 'channels/be/canalc_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 20
    },
    'abxplore': {
        'resolver': '/resources/lib/channels/be/abbe:get_live_url',
        'label': 'ABXPLORE',
        'thumb': 'channels/be/abxplore.png',
        'fanart': 'channels/be/abxplore_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 21
    },
    'ab3': {
        'resolver': '/resources/lib/channels/be/abbe:get_live_url',
        'label': 'AB3',
        'thumb': 'channels/be/ab3.png',
        'fanart': 'channels/be/ab3_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 22
    },
    'ln24': {
        'resolver': '/resources/lib/channels/be/ln24:get_live_url',
        'label': 'LN24',
        'thumb': 'channels/be/ln24.png',
        'fanart': 'channels/be/ln24_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 23
    },
    'laune': {
        'resolver': '/resources/lib/channels/be/rtbf:set_live_url',
        'label': 'La Une',
        'thumb': 'channels/be/laune.png',
        'fanart': 'channels/be/laune_fanart.jpg',
        'xmltv_id': 'C164.api.telerama.fr',
        'enabled': True,
        'order': 24
    },
    'tipik': {
        'resolver': '/resources/lib/channels/be/rtbf:set_live_url',
        'label': 'Tipik',
        'thumb': 'channels/be/tipik.png',
        'fanart': 'channels/be/tipik_fanart.jpg',
        'xmltv_id': 'C187.api.telerama.fr',
        'enabled': True,
        'order': 25
    },
    'latrois': {
        'resolver': '/resources/lib/channels/be/rtbf:set_live_url',
        'label': 'La Trois',
        'thumb': 'channels/be/latrois.png',
        'fanart': 'channels/be/latrois_fanart.jpg',
        'xmltv_id': 'C892.api.telerama.fr',
        'enabled': True,
        'order': 26
    },
    'actv': {
        'resolver': '/resources/lib/channels/be/actv:get_live_url',
        'label': 'Antenne Centre TV',
        'thumb': 'channels/be/actv.png',
        'fanart': 'channels/be/actv_fanart.jpg',
        'enabled': True,
        'order': 27
    }
}
