# -*- coding: utf-8 -*-
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

# The following dictionaries describe
# the addon's tree architecture.
# * Key: item id
# * Value: item infos
#     - route (folder)/resolver (playable URL): Callback function to run once this item is selected
#     - thumb: Item thumb path relative to "media" folder
#     - fanart: Item fanart path relative to "media" folder

root = 'live_tv'

menu = {
    '387238': {
        'resolver': '/resources/lib/channels/sa/shahid:get_live_url',
        'label': 'MBC1',
        'thumb': 'https://shahid.mbc.net/mediaObject/d191d806-50ff-4374-9868-4423fb0ab5e1',
        'fanart': '',
        'xmltv_id': '',
        'enabled': True,
        'order': 1
    },
    '400917': {
        'resolver': '/resources/lib/channels/sa/shahid:get_live_url',
        'label': 'MBC2',
        'thumb': 'https://shahid.mbc.net/mediaObject/0fc148ad-de25-4bf6-8fc8-5f8f97a52e2d',
        'fanart': '',
        'xmltv_id': '',
        'enabled': True,
        'order': 2
    },
    '409385': {
        'resolver': '/resources/lib/channels/sa/shahid:get_live_url',
        'label': 'MBC3',
        'thumb': 'https://shahid.mbc.net/mediaObject/3c5cf22a-3f74-4c24-aacf-a21c4a3e3138',
        'fanart': '',
        'xmltv_id': '',
        'enabled': True,
        'order': 3
    },
    '400919': {
        'resolver': '/resources/lib/channels/sa/shahid:get_live_url',
        'label': 'MBC4',
        'thumb': 'https://shahid.mbc.net/mediaObject/e4658f69-3cac-4522-a6db-ff399c4f48f1',
        'fanart': '',
        'xmltv_id': '',
        'enabled': True,
        'order': 4
    },
}
