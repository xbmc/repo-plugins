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
    - route (folder)/resolver (playable URL): Callback function to run once this item is selected
    - thumb: Item thumb path relative to "media" folder
    - fanart: Item fanart path relative to "meia" folder
"""

menu = {
    'tvp3': {
        'resolver': '/resources/lib/channels/pl/tvp:get_live_url',
        'label': 'TVP 3 (' + utils.ensure_unicode(Script.setting['tvp3.language']) + ')',
        'thumb':
        'channels/pl/tvp3.png',
        'fanart':
        'channels/pl/tvp3_fanart.jpg',
        'available_languages': [
            "Białystok", "Bydgoszcz", "Gdańsk", "Gorzów Wielkopolski",
            "Katowice", "Kielce", "Kraków", "Lublin", "Łódź", "Olsztyn",
            "Opole", "Poznań", "Rzeszów", "Szczecin", "Warszawa", "Wrocław"
        ],
        'enabled': True,
        'order': 2
    },
    'tvpinfo': {
        'resolver': '/resources/lib/channels/pl/tvp:get_live_url',
        'label': 'TVP Info',
        'thumb': 'channels/pl/tvpinfo.png',
        'fanart': 'channels/pl/tvpinfo_fanart.jpg',
        'enabled': True,
        'order': 3
    },
    'tvppolonia': {
        'resolver': '/resources/lib/channels/pl/tvp:get_live_url',
        'label': 'TVP Polonia',
        'thumb': 'channels/pl/tvppolonia.png',
        'fanart': 'channels/pl/tvppolonia_fanart.jpg',
        'enabled': True,
        'order': 4
    },
    'tvppolandin': {
        'resolver': '/resources/lib/channels/pl/tvp:get_live_url',
        'label': 'TVP Poland IN',
        'thumb': 'channels/pl/tvppolandin.png',
        'fanart': 'channels/pl/tvppolandin_fanart.jpg',
        'enabled': True,
        'order': 5
    }
}
