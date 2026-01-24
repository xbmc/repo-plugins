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
    'blaze': {
        'resolver': '/resources/lib/channels/uk/blaze:get_live_url',
        'label': 'Blaze',
        'thumb': 'channels/uk/blaze.png',
        'fanart': 'channels/uk/blaze_fanart.jpg',
        'xmltv_id': '64.freeview.co.uk',
        'enabled': True,
        'order': 1
    },
    'dave': {
        'resolver': '/resources/lib/channels/uk/uktvplay:get_live_url',
        'label': 'Dave',
        'thumb': 'channels/uk/dave.png',
        'fanart': 'channels/uk/dave_fanart.jpg',
        'xmltv_id': '19.freeview.co.uk',
        'enabled': False,
        'order': 2
    },
    'yesterday': {
        'resolver': '/resources/lib/channels/uk/uktvplay:get_live_url',
        'label': 'Yesterday',
        'thumb': 'channels/uk/yesterday.png',
        'fanart': 'channels/uk/yesterday_fanart.jpg',
        'xmltv_id': '27.freeview.co.uk',
        'enabled': False,
        'order': 3
    },
    'drama': {
        'resolver': '/resources/lib/channels/uk/uktvplay:get_live_url',
        'label': 'Drama',
        'thumb': 'channels/uk/drama.png',
        'fanart': 'channels/uk/drama_fanart.jpg',
        'xmltv_id': '20.freeview.co.uk',
        'enabled': False,
        'order': 4
    },
    'skynews': {
        'resolver': '/resources/lib/channels/uk/sky:get_live_url',
        'label': 'Sky News',
        'thumb': 'channels/uk/skynews.png',
        'fanart': 'channels/uk/skynews_fanart.jpg',
        'xmltv_id': '233.freeview.co.uk',
        'enabled': True,
        'order': 5
    },
    'stv': {
        'resolver': '/resources/lib/channels/uk/stv:get_live_url',
        'label': 'STV',
        'thumb': 'channels/uk/stv.png',
        'fanart': 'channels/uk/stv_fanart.jpg',
        'xmltv_id': '103.freeview.co.uk',
        'enabled': True,
        'order': 6
    },
    'stv-plus-1': {
        'resolver': '/resources/lib/channels/uk/stv:get_live_url',
        'label': 'STV +1',
        'thumb': 'channels/uk/stv_plusone.png',
        'xmltv_id': '35.freeview.co.uk',
        'enabled': True,
        'order': 7
    },
    'C4': {
        'resolver': '/resources/lib/channels/uk/channel4:get_live_url',
        'label': 'Channel 4',
        'thumb': 'channels/uk/channel4.png',
        'fanart': 'channels/uk/channel4_fanart.jpg',
        'xmltv_id': '4.freeview.co.uk',
        'enabled': True,
        'order': 8
    },
    'E4': {
        'resolver': '/resources/lib/channels/uk/channel4:get_live_url',
        'label': 'E4',
        'thumb': 'channels/uk/E4.png',
        'fanart': 'channels/uk/E4_fanart.jpg',
        'xmltv_id': '13.freeview.co.uk',
        'enabled': True,
        'order': 9
    },
    'M4': {
        'resolver': '/resources/lib/channels/uk/channel4:get_live_url',
        'label': 'More4',
        'thumb': 'channels/uk/More4.png',
        'fanart': 'channels/uk/More4_fanart.jpg',
        'xmltv_id': '18.freeview.co.uk',
        'enabled': True,
        'order': 10
    },
    'F4': {
        'resolver': '/resources/lib/channels/uk/channel4:get_live_url',
        'label': 'Film4',
        'thumb': 'channels/uk/Film4.png',
        'fanart': 'channels/uk/Film4_fanart.jpg',
        'xmltv_id': '14.freeview.co.uk',
        'enabled': True,
        'order': 11
    },
    '4S': {
        'resolver': '/resources/lib/channels/uk/channel4:get_live_url',
        'label': '4seven',
        'thumb': 'channels/uk/4seven.png',
        'fanart': 'channels/uk/4seven_fanart.jpg',
        'xmltv_id': '49.freeview.co.uk',
        'enabled': True,
        'order': 12
    },
    'birminghamlocal': {
        'resolver': '/resources/lib/channels/uk/uklocaltv:get_live_url',
        'label': 'Birmingham Local TV',
        'thumb': 'channels/uk/birminghamlocal.png',
        'fanart': 'channels/uk/birminghamlocal_fanart.jpg',
        'enabled': False,
        'order': 13
    },
    'bristollocal': {
        'resolver': '/resources/lib/channels/uk/uklocaltv:get_live_url',
        'label': 'Bristol Local TV',
        'thumb': 'channels/uk/bristollocal.png',
        'fanart': 'channels/uk/bristollocal_fanart.jpg',
        'enabled': False,
        'order': 14
    },
    'cardifflocal': {
        'resolver': '/resources/lib/channels/uk/uklocaltv:get_live_url',
        'label': 'Cardiff Local TV',
        'thumb': 'channels/uk/cardifflocal.png',
        'fanart': 'channels/uk/cardifflocal_fanart.jpg',
        'enabled': False,
        'order': 15
    },
    'leedslocal': {
        'resolver': '/resources/lib/channels/uk/uklocaltv:get_live_url',
        'label': 'Leeds Local TV',
        'thumb': 'channels/uk/leedslocal.png',
        'fanart': 'channels/uk/leedslocal_fanart.jpg',
        'enabled': False,
        'order': 16
    },
    'liverpoollocal': {
        'resolver': '/resources/lib/channels/uk/uklocaltv:get_live_url',
        'label': 'Liverpool Local TV',
        'thumb': 'channels/uk/liverpoollocal.png',
        'fanart': 'channels/uk/liverpoollocal_fanart.jpg',
        'enabled': False,
        'order': 17
    },
    'northwaleslocal': {
        'resolver': '/resources/lib/channels/uk/uklocaltv:get_live_url',
        'label': 'North Wales Local TV',
        'thumb': 'channels/uk/northwaleslocal.png',
        'fanart': 'channels/uk/northwaleslocal_fanart.jpg',
        'enabled': False,
        'order': 18
    },
    'teessidelocal': {
        'resolver': '/resources/lib/channels/uk/uklocaltv:get_live_url',
        'label': 'Teesside Local TV',
        'thumb': 'channels/uk/teessidelocal.png',
        'fanart': 'channels/uk/teessidelocal_fanart.jpg',
        'enabled': False,
        'order': 19
    },
    'twlocal': {
        'resolver': '/resources/lib/channels/uk/uklocaltv:get_live_url',
        'label': 'Tyne & Wear Local TV',
        'thumb': 'channels/uk/twlocal.png',
        'fanart': 'channels/uk/twlocal_fanart.jpg',
        'enabled': False,
        'order': 20
    },
    'really': {
        'resolver': '/resources/lib/channels/uk/discoveryplus:get_live_url',
        'label': 'Really',
        'thumb': 'channels/uk/really.png',
        'fanart': 'channels/uk/really_fanart.jpg',
        'xmltv_id': '17.freeview.co.uk',
        'enabled': False,
        'order': 21
    },
    'food-network': {
        'resolver': '/resources/lib/channels/uk/discoveryplus:get_live_url',
        'label': 'Food Network',
        'thumb': 'channels/uk/foodnetwork.png',
        'fanart': 'channels/uk/foodnetwork_fanart.jpg',
        'xmltv_id': '43.freeview.co.uk',
        'enabled': False,
        'order': 22
    },
    'dmax': {
        'resolver': '/resources/lib/channels/uk/discoveryplus:get_live_url',
        'label': 'DMAX',
        'thumb': 'channels/uk/dmax.png',
        'fanart': 'channels/uk/dmax_fanart.jpg',
        'xmltv_id': '39.freeview.co.uk',
        'enabled': False,
        'order': 23
    },
    'home': {
        'resolver': '/resources/lib/channels/uk/discoveryplus:get_live_url',
        'label': 'HGTV',
        'thumb': 'channels/uk/hgtv.png',
        'fanart': 'channels/uk/hgtv_fanart.jpg',
        'xmltv_id': '44.freeview.co.uk',
        'enabled': False,
        'order': 24
    },
    'quest': {
        'resolver': '/resources/lib/channels/uk/discoveryplus:get_live_url',
        'label': 'Quest',
        'thumb': 'channels/uk/questtv.png',
        'fanart': 'channels/uk/questtv_fanart.jpg',
        'xmltv_id': '12.freeview.co.uk',
        'enabled': False,
        'order': 25
    },
    'quest-red': {
        'resolver': '/resources/lib/channels/uk/discoveryplus:get_live_url',
        'label': 'Quest RED',
        'thumb': 'channels/uk/questred.png',
        'fanart': 'channels/uk/questred_fanart.jpg',
        'xmltv_id': '40.freeview.co.uk',
        'enabled': False,
        'order': 26
    },
    'C5': {
        'resolver': '/resources/lib/channels/uk/my5:get_live_url',
        'label': 'Channel 5 from My5',
        'thumb': 'channels/uk/five.png',
        'fanart': 'channels/uk/five_fanart.jpg',
        'xmltv_id': '5.freeview.co.uk',
        'enabled': True,
        'order': 27
    },
    'C6': {
        'resolver': '/resources/lib/channels/uk/my5:get_live_url',
        'label': '5 Star from My5',
        'thumb': 'channels/uk/fivestar.png',
        'fanart': 'channels/uk/fivestar_fanart.jpg',
        'xmltv_id': '32.freeview.co.uk',
        'enabled': True,
        'order': 28
    },
    'C7': {
        'resolver': '/resources/lib/channels/uk/my5:get_live_url',
        'label': '5 USA from My5',
        'thumb': 'channels/uk/fiveusa.png',
        'fanart': 'channels/uk/fiveusa_fanart.jpg',
        'xmltv_id': '21.freeview.co.uk',
        'enabled': True,
        'order': 29
    },
    'C0': {
        'resolver': '/resources/lib/channels/uk/my5:get_live_url',
        'label': '5 Action from My5',
        'thumb': 'channels/uk/5action.png',
        'fanart': 'channels/uk/5action_fanart.jpg',
        'xmltv_id': '33.freeview.co.uk',
        'enabled': True,
        'order': 30
    },
    'C8': {
        'resolver': '/resources/lib/channels/uk/my5:get_live_url',
        'label': '5 Select from My5',
        'thumb': 'channels/uk/5select.png',
        'fanart': 'channels/uk/5select_fanart.jpg',
        'xmltv_id': '46.freeview.co.uk',
        'enabled': True,
        'order': 31
    },
}
