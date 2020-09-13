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
    'la7': {
        'resolver': '/resources/lib/channels/it/la7:get_live_url',
        'label': 'La7',
        'thumb': 'channels/it/la7.png',
        'fanart': 'channels/it/la7_fanart.jpg',
        'xmltv_id': 'www.la7.it',
        'enabled': True,
        'order': 1
    },
    'rainews24': {
        'resolver': '/resources/lib/channels/it/raiplay:get_live_url',
        'label': 'Rai News 24',
        'thumb': 'channels/it/rainews24.png',
        'fanart': 'channels/it/rainews24_fanart.jpg',
        'xmltv_id': 'rainews.guidatv.sky.it',
        'enabled': True,
        'order': 2
    },
    'rai1': {
        'resolver': '/resources/lib/channels/it/raiplay:get_live_url',
        'label': 'Rai 1',
        'thumb': 'channels/it/rai1.png',
        'fanart': 'channels/it/rai1_fanart.jpg',
        'xmltv_id': 'www.raiuno.rai.it',
        'enabled': True,
        'order': 3
    },
    'rai2': {
        'resolver': '/resources/lib/channels/it/raiplay:get_live_url',
        'label': 'Rai 2',
        'thumb': 'channels/it/rai2.png',
        'fanart': 'channels/it/rai2_fanart.jpg',
        'xmltv_id': 'www.raidue.rai.it',
        'enabled': True,
        'order': 4
    },
    'rai3': {
        'resolver': '/resources/lib/channels/it/raiplay:get_live_url',
        'label': 'Rai 3',
        'thumb': 'channels/it/rai3.png',
        'fanart': 'channels/it/rai3_fanart.jpg',
        'xmltv_id': 'www.raitre.rai.it',
        'enabled': True,
        'order': 5
    },
    'rai4': {
        'resolver': '/resources/lib/channels/it/raiplay:get_live_url',
        'label': 'Rai 4',
        'thumb': 'channels/it/rai4.png',
        'fanart': 'channels/it/rai4_fanart.jpg',
        'xmltv_id': 'rai4.raisat.it',
        'enabled': True,
        'order': 6
    },
    'rai5': {
        'resolver': '/resources/lib/channels/it/raiplay:get_live_url',
        'label': 'Rai 5',
        'thumb': 'channels/it/rai5.png',
        'fanart': 'channels/it/rai5_fanart.jpg',
        'xmltv_id': 'rai5.rai.it',
        'enabled': True,
        'order': 7
    },
    'raisportpiuhd': {
        'resolver': '/resources/lib/channels/it/raiplay:get_live_url',
        'label': 'Rai Sport',
        'thumb': 'channels/it/raisportpiuhd.png',
        'fanart': 'channels/it/raisportpiuhd_fanart.jpg',
        'xmltv_id': 'raisport.guidatv.sky.it',
        'enabled': True,
        'order': 8
    },
    'raimovie': {
        'resolver': '/resources/lib/channels/it/raiplay:get_live_url',
        'label': 'Rai Movie',
        'thumb': 'channels/it/raimovie.png',
        'fanart': 'channels/it/raimovie_fanart.jpg',
        'xmltv_id': 'raimovie.rai.it',
        'enabled': True,
        'order': 9
    },
    'raipremium': {
        'resolver': '/resources/lib/channels/it/raiplay:get_live_url',
        'label': 'Rai Premium',
        'thumb': 'channels/it/raipremium.png',
        'fanart': 'channels/it/raipremium_fanart.jpg',
        'xmltv_id': 'raipremium.guidatv.sky.it',
        'enabled': True,
        'order': 10
    },
    'raiyoyo': {
        'resolver': '/resources/lib/channels/it/raiplay:get_live_url',
        'label': 'Rai Yoyo',
        'thumb': 'channels/it/raiyoyo.png',
        'fanart': 'channels/it/raiyoyo_fanart.jpg',
        'xmltv_id': 'yoyo.raisat.it',
        'enabled': True,
        'order': 11
    },
    'raigulp': {
        'resolver': '/resources/lib/channels/it/raiplay:get_live_url',
        'label': 'Rai Gulp',
        'thumb': 'channels/it/raigulp.png',
        'fanart': 'channels/it/raigulp_fanart.jpg',
        'xmltv_id': 'raigulp.rai.it',
        'enabled': True,
        'order': 12
    },
    'raistoria': {
        'resolver': '/resources/lib/channels/it/raiplay:get_live_url',
        'label': 'Rai Storia',
        'thumb': 'channels/it/raistoria.png',
        'fanart': 'channels/it/raistoria_fanart.jpg',
        'xmltv_id': 'raistoria.rai.it',
        'enabled': True,
        'order': 13
    },
    'raiscuola': {
        'resolver': '/resources/lib/channels/it/raiplay:get_live_url',
        'label': 'Rai Scuola',
        'thumb': 'channels/it/raiscuola.png',
        'fanart': 'channels/it/raiscuola_fanart.jpg',
        'xmltv_id': 'raiscuola.rai.it',
        'enabled': True,
        'order': 14
    },
    'paramountchannel_it': {
        'resolver': '/resources/lib/channels/it/paramountchannel_it:get_live_url',
        'label': 'Paramount Channel (IT)',
        'thumb': 'channels/it/paramountchannel_it.png',
        'fanart': 'channels/it/paramountchannel_it_fanart.jpg',
        'enabled': True,
        'order': 17
    }
}
