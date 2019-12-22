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
    'la7': {
        'callback': 'live_bridge',
        'thumb': 'channels/it/la7.png',
        'fanart': 'channels/it/la7_fanart.jpg',
        'module': 'resources.lib.channels.it.la7',
        'xmltv_id': 'www.la7.it'
    },
    'rainews24': {
        'callback': 'live_bridge',
        'thumb': 'channels/it/rainews24.png',
        'fanart': 'channels/it/rainews24_fanart.jpg',
        'module': 'resources.lib.channels.it.raiplay',
        'xmltv_id': 'rainews.guidatv.sky.it'
    },
    'rai1': {
        'callback': 'live_bridge',
        'thumb': 'channels/it/rai1.png',
        'fanart': 'channels/it/rai1_fanart.jpg',
        'module': 'resources.lib.channels.it.raiplay',
        'xmltv_id': 'www.raiuno.rai.it'
    },
    'rai2': {
        'callback': 'live_bridge',
        'thumb': 'channels/it/rai2.png',
        'fanart': 'channels/it/rai2_fanart.jpg',
        'module': 'resources.lib.channels.it.raiplay',
        'xmltv_id': 'www.raidue.rai.it'
    },
    'rai3': {
        'callback': 'live_bridge',
        'thumb': 'channels/it/rai3.png',
        'fanart': 'channels/it/rai3_fanart.jpg',
        'module': 'resources.lib.channels.it.raiplay',
        'xmltv_id': 'www.raitre.rai.it'
    },
    'rai4': {
        'callback': 'live_bridge',
        'thumb': 'channels/it/rai4.png',
        'fanart': 'channels/it/rai4_fanart.jpg',
        'module': 'resources.lib.channels.it.raiplay',
        'xmltv_id': 'rai4.raisat.it'
    },
    'rai5': {
        'callback': 'live_bridge',
        'thumb': 'channels/it/rai5.png',
        'fanart': 'channels/it/rai5_fanart.jpg',
        'module': 'resources.lib.channels.it.raiplay',
        'xmltv_id': 'rai5.rai.it'
    },
    'raisportpiuhd': {
        'callback': 'live_bridge',
        'thumb': 'channels/it/raisportpiuhd.png',
        'fanart': 'channels/it/raisportpiuhd_fanart.jpg',
        'module': 'resources.lib.channels.it.raiplay',
        'xmltv_id': 'raisport.guidatv.sky.it'
    },
    'raimovie': {
        'callback': 'live_bridge',
        'thumb': 'channels/it/raimovie.png',
        'fanart': 'channels/it/raimovie_fanart.jpg',
        'module': 'resources.lib.channels.it.raiplay',
        'xmltv_id': 'raimovie.rai.it'
    },
    'raipremium': {
        'callback': 'live_bridge',
        'thumb': 'channels/it/raipremium.png',
        'fanart': 'channels/it/raipremium_fanart.jpg',
        'module': 'resources.lib.channels.it.raiplay',
        'xmltv_id': 'raipremium.guidatv.sky.it'
    },
    'raiyoyo': {
        'callback': 'live_bridge',
        'thumb': 'channels/it/raiyoyo.png',
        'fanart': 'channels/it/raiyoyo_fanart.jpg',
        'module': 'resources.lib.channels.it.raiplay',
        'xmltv_id': 'yoyo.raisat.it'
    },
    'raigulp': {
        'callback': 'live_bridge',
        'thumb': 'channels/it/raigulp.png',
        'fanart': 'channels/it/raigulp_fanart.jpg',
        'module': 'resources.lib.channels.it.raiplay',
        'xmltv_id': 'raigulp.rai.it'
    },
    'raistoria': {
        'callback': 'live_bridge',
        'thumb': 'channels/it/raistoria.png',
        'fanart': 'channels/it/raistoria_fanart.jpg',
        'module': 'resources.lib.channels.it.raiplay',
        'xmltv_id': 'raistoria.rai.it'
    },
    'raiscuola': {
        'callback': 'live_bridge',
        'thumb': 'channels/it/raiscuola.png',
        'fanart': 'channels/it/raiscuola_fanart.jpg',
        'module': 'resources.lib.channels.it.raiplay',
        'xmltv_id': 'raiscuola.rai.it'
    },
    'paramountchannel_it': {
        'callback': 'live_bridge',
        'thumb': 'channels/it/paramountchannel_it.png',
        'fanart': 'channels/it/paramountchannel_it_fanart.jpg',
        'module': 'resources.lib.channels.it.paramountchannel_it'
    }
}
