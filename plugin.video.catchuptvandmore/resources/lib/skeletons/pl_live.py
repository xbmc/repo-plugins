# -*- coding: utf-8 -*-
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from codequick import Script, utils

# The following dictionaries describe
# the addon's tree architecture.
# * Key: item id
# * Value: item infos
#    - route (folder)/resolver (playable URL): Callback function to run once this item is selected
#    - thumb: Item thumb path relative to "media" folder
#    - fanart: Item fanart path relative to "media" folder

root = 'live_tv'

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
