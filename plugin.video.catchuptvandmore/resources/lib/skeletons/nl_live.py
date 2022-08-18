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
    'npo-1': {
        'resolver': '/resources/lib/channels/nl/npo:get_live_url',
        'label': 'NPO 1',
        'thumb': 'channels/nl/npo1.png',
        'fanart': 'channels/nl/npo1_fanart.jpg',
        'enabled': True,
        'order': 1
    },
    'npo-2': {
        'resolver': '/resources/lib/channels/nl/npo:get_live_url',
        'label': 'NPO 2',
        'thumb': 'channels/nl/npo2.png',
        'fanart': 'channels/nl/npo2_fanart.jpg',
        'enabled': True,
        'order': 2
    },
    'npo-zapp': {
        'resolver': '/resources/lib/channels/nl/npo:get_live_url',
        'label': 'NPO Zapp',
        'thumb': 'channels/nl/npozapp.png',
        'fanart': 'channels/nl/npozapp_fanart.jpg',
        'enabled': True,
        'order': 3
    },
    'npo-1-extra': {
        'resolver': '/resources/lib/channels/nl/npo:get_live_url',
        'label': 'NPO 1 Extra',
        'thumb': 'channels/nl/npo1extra.png',
        'fanart': 'channels/nl/npo1extra_fanart.jpg',
        'enabled': True,
        'order': 4
    },
    'npo-2-extra': {
        'resolver': '/resources/lib/channels/nl/npo:get_live_url',
        'label': 'NPO 2 Extra',
        'thumb': 'channels/nl/npo2extra.png',
        'fanart': 'channels/nl/npo2extra_fanart.jpg',
        'enabled': True,
        'order': 5
    },
    'npo-zappelin-extra': {
        'resolver': '/resources/lib/channels/nl/npo:get_live_url',
        'label': 'NPO Zappelin Extra',
        'thumb': 'channels/nl/npozappelinextra.png',
        'fanart': 'channels/nl/npozappelinextra_fanart.jpg',
        'enabled': True,
        'order': 6
    },
    'npo-nieuws': {
        'resolver': '/resources/lib/channels/nl/npo:get_live_url',
        'label': 'NPO Nieuws',
        'thumb': 'channels/nl/nponieuws.png',
        'fanart': 'channels/nl/nponieuws_fanart.jpg',
        'enabled': True,
        'order': 7
    },
    'npo-politiek': {
        'resolver': '/resources/lib/channels/nl/npo:get_live_url',
        'label': 'NPO Politiek',
        'thumb': 'channels/nl/npopolitiek.png',
        'fanart': 'channels/nl/npopolitiek_fanart.jpg',
        'enabled': True,
        'order': 8
    },
    'at5': {
        'resolver': '/resources/lib/channels/nl/at5:get_live_url',
        'label': 'AT5',
        'thumb': 'channels/nl/at5.png',
        'fanart': 'channels/nl/at5_fanart.jpg',
        'enabled': True,
        'order': 10
    },
    'ob': {
        'resolver': '/resources/lib/channels/nl/ob:get_live_url',
        'label': 'Omroep Brabant',
        'thumb': 'channels/nl/ob.png',
        'fanart': 'channels/nl/ob_fanart.jpg',
        'enabled': True,
        'order': 11
    }
}
