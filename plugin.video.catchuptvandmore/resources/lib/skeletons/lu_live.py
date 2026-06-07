# -*- coding: utf-8 -*-
# Copyright: (c) 2023, Joaopa
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

# The following dictionaries describe
# the addon's tree architecture.
# * Key: item id
# * Value: item infos
#    - route (folder)/resolver (playable URL): Callback function to run once this item is selected
#    - thumb: Item thumb path relative to "media" folder
#    - fanart: Item fanart path relative to "media" folder

root = 'live_tv'

menu = {
    'rtl': {
        'resolver': '/resources/lib/channels/lu/rtl:get_live_url',
        'label': 'RTL',
        'thumb': 'channels/lu/rtl.png',
        'fanart': 'channels/lu/rtl_fanart.jpg',
        'enabled': True,
        'order': 1
    },
    'rtl-zwee': {
        'resolver': '/resources/lib/channels/lu/rtl:get_live_url',
        'label': 'RTL Zwee',
        'thumb': 'channels/lu/rtl_zwee.png',
        'fanart': 'channels/lu/rtl_zwee_fanart.jpg',
        'enabled': True,
        'order': 2
    },
    'rtl-gold': {
        'resolver': '/resources/lib/channels/lu/rtl:get_live_url',
        'label': 'RTL Gold',
        'thumb': 'channels/lu/rtl_gold.png',
        'fanart': 'channels/lu/rtl_gold_fanart.jpg',
        'enabled': True,
        'order': 3
    },
    'radio': {
        'resolver': '/resources/lib/channels/lu/rtl:get_live_url',
        'label': 'RTL Radio Lëtzebuerg',
        'thumb': 'channels/lu/rtl_radio.png',
        'fanart': 'channels/lu/rtl_radio_fanart.jpg',
        'enabled': True,
        'order': 4
    },
    'rtl-today-radio': {
        'resolver': '/resources/lib/channels/lu/rtl:get_live_url',
        'label': 'RTL Today Radio',
        'thumb': 'channels/lu/rtl_today.png',
        'fanart': 'channels/lu/rtl_today_fanart.jpg',
        'enabled': True,
        'order': 5
    },
    'rtl-lx': {
        'resolver': '/resources/lib/channels/lu/rtl:get_live_url',
        'label': 'RTL LX',
        'thumb': 'channels/lu/rtl_lx.png',
        'fanart': 'channels/lu/rtl_lx_fanart.jpg',
        'enabled': True,
        'order': 6
    },
}
