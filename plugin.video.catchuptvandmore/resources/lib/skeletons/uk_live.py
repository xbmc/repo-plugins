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
        'xmltv_id': '1013.tvguide.co.uk',
        'enabled': True,
        'order': 1
    },
    'dave': {
        'resolver': '/resources/lib/channels/uk/uktvplay:get_live_url',
        'label': 'Dave',
        'thumb': 'channels/uk/dave.png',
        'fanart': 'channels/uk/dave_fanart.jpg',
        'xmltv_id': '432.tvguide.co.uk',
        'enabled': True,
        'order': 2
    },
    'yesterday': {
        'resolver': '/resources/lib/channels/uk/uktvplay:get_live_url',
        'label': 'Yesterday',
        'thumb': 'channels/uk/yesterday.png',
        'fanart': 'channels/uk/yesterday_fanart.jpg',
        'xmltv_id': '320.tvguide.co.uk',
        'enabled': True,
        'order': 3
    },
    'drama': {
        'resolver': '/resources/lib/channels/uk/uktvplay:get_live_url',
        'label': 'Drama',
        'thumb': 'channels/uk/drama.png',
        'fanart': 'channels/uk/drama_fanart.jpg',
        'xmltv_id': '871.tvguide.co.uk',
        'enabled': True,
        'order': 4
    },
    'skynews': {
        'resolver': '/resources/lib/channels/uk/sky:get_live_url',
        'label': 'Sky News',
        'thumb': 'channels/uk/skynews.png',
        'fanart': 'channels/uk/skynews_fanart.jpg',
        'xmltv_id': '257.tvguide.co.uk',
        'enabled': True,
        'order': 5
    },
    'stv': {
        'resolver': '/resources/lib/channels/uk/stv:get_live_url',
        'label': 'STV',
        'thumb': 'channels/uk/stv.png',
        'fanart': 'channels/uk/stv_fanart.jpg',
        'xmltv_id': '178.tvguide.co.uk',
        'enabled': True,
        'order': 6
    },
    'kerrang': {
        'resolver': '/resources/lib/channels/uk/boxplus:get_live_url',
        'label': 'Kerrang',
        'thumb': 'channels/uk/kerrang.png',
        'fanart': 'channels/uk/kerrang_fanart.jpg',
        'xmltv_id': '1207.tvguide.co.uk',
        'enabled': True,
        'order': 7
    },
    'magic': {
        'resolver': '/resources/lib/channels/uk/boxplus:get_live_url',
        'label': 'Magic',
        'thumb': 'channels/uk/magic.png',
        'fanart': 'channels/uk/magic_fanart.jpg',
        'xmltv_id': '185.tvguide.co.uk',
        'enabled': True,
        'order': 8
    },
    'kiss': {
        'resolver': '/resources/lib/channels/uk/boxplus:get_live_url',
        'label': 'Kiss',
        'thumb': 'channels/uk/kiss.png',
        'fanart': 'channels/uk/kiss_fanart.jpg',
        'xmltv_id': '182.tvguide.co.uk',
        'enabled': True,
        'order': 9
    },
    'the-box': {
        'resolver': '/resources/lib/channels/uk/boxplus:get_live_url',
        'label': 'The Box',
        'thumb': 'channels/uk/thebox.png',
        'fanart': 'channels/uk/thebox_fanart.jpg',
        'xmltv_id': '279.tvguide.co.uk',
        'enabled': True,
        'order': 10
    },
    'box-hits': {
        'resolver': '/resources/lib/channels/uk/boxplus:get_live_url',
        'label': 'Box Hits',
        'thumb': 'channels/uk/boxhits.png',
        'fanart': 'channels/uk/boxhits_fanart.jpg',
        'xmltv_id': '267.tvguide.co.uk',
        'enabled': True,
        'order': 11
    },
    'box-upfront': {
        'resolver': '/resources/lib/channels/uk/boxplus:get_live_url',
        'label': 'Box Upfront',
        'thumb': 'channels/uk/boxupfront.png',
        'fanart': 'channels/uk/boxupfront_fanart.jpg',
        'enabled': True,
        'order': 12
    },
    'freesports': {
        'resolver': '/resources/lib/channels/uk/stv:get_live_url',
        'label': 'Free Sports',
        'thumb': 'channels/uk/freesports.png',
        'fanart': 'channels/uk/freesports_fanart.jpg',
        'enabled': True,
        'order': 13
    },
    'stv_plusone': {
        'resolver': '/resources/lib/channels/uk/stv:get_live_url',
        'label': 'STV+1',
        'thumb': 'channels/uk/stv_plusone.png',
        'fanart': 'channels/uk/stv_plusone_fanart.jpg',
        'enabled': True,
        'order': 14
    },
    'edgesport': {
        'resolver': '/resources/lib/channels/uk/stv:get_live_url',
        'label': 'EDGE Sport',
        'thumb': 'channels/uk/edgesport.png',
        'fanart': 'channels/uk/edgesport_fanart.jpg',
        'enabled': True,
        'order': 15
    },
    'thepetcollective': {
        'resolver': '/resources/lib/channels/uk/stv:get_live_url',
        'label': 'The Pet Collective',
        'thumb': 'channels/uk/thepetcollective.png',
        'fanart': 'channels/uk/thepetcollective_fanart.jpg',
        'enabled': True,
        'order': 16
    },
    'failarmy': {
        'resolver': '/resources/lib/channels/uk/stv:get_live_url',
        'label': 'Fail Army',
        'thumb': 'channels/uk/failarmy.png',
        'fanart': 'channels/uk/failarmy_fanart.jpg',
        'enabled': True,
        'order': 17
    },
    'qello': {
        'resolver': '/resources/lib/channels/uk/stv:get_live_url',
        'label': 'Qello',
        'thumb': 'channels/uk/qello.png',
        'fanart': 'channels/uk/qello_fanart.jpg',
        'enabled': True,
        'order': 18
    },
    'dust': {
        'resolver': '/resources/lib/channels/uk/stv:get_live_url',
        'label': 'DUST',
        'thumb': 'channels/uk/dust.png',
        'fanart': 'channels/uk/dust_fanart.jpg',
        'enabled': True,
        'order': 20
    },
    'C4': {
        'resolver': '/resources/lib/channels/uk/channel4:get_live_url',
        'label': 'Channel4',
        'thumb': 'channels/uk/channel4.png',
        'fanart': 'channels/uk/channel4_fanart.jpg',
        'enabled': True,
        'order': 21
    },
    'E4': {
        'resolver': '/resources/lib/channels/uk/channel4:get_live_url',
        'label': 'E4',
        'thumb': 'channels/uk/E4.png',
        'fanart': 'channels/uk/E4_fanart.jpg',
        'enabled': True,
        'order': 22
    },
    'M4': {
        'resolver': '/resources/lib/channels/uk/channel4:get_live_url',
        'label': 'More4',
        'thumb': 'channels/uk/More4.png',
        'fanart': 'channels/uk/More4_fanart.jpg',
        'enabled': True,
        'order': 23
    },
    'F4': {
        'resolver': '/resources/lib/channels/uk/channel4:get_live_url',
        'label': 'Film4',
        'thumb': 'channels/uk/Film4.png',
        'fanart': 'channels/uk/Film4_fanart.jpg',
        'enabled': True,
        'order': 24
    },
    '4S': {
        'resolver': '/resources/lib/channels/uk/channel4:get_live_url',
        'label': '4seven',
        'thumb': 'channels/uk/4seven.png',
        'fanart': 'channels/uk/4seven_fanart.jpg',
        'enabled': True,
        'order': 25
    },
    'birminghamlocal': {
        'resolver': '/resources/lib/channels/uk/uklocaltv:get_live_url',
        'label': 'Birmingham Local TV',
        'thumb': 'channels/uk/birminghamlocal.png',
        'fanart': 'channels/uk/birminghamlocal_fanart.jpg',
        'xmltv_id': '1154.tvguide.co.uk',
        'enabled': True,
        'order': 26
    },
    'bristollocal': {
        'resolver': '/resources/lib/channels/uk/uklocaltv:get_live_url',
        'label': 'Bristol Local TV',
        'thumb': 'channels/uk/bristollocal.png',
        'fanart': 'channels/uk/bristollocal_fanart.jpg',
        'xmltv_id': '1157.tvguide.co.uk',
        'enabled': True,
        'order': 27
    },
    'cardifflocal': {
        'resolver': '/resources/lib/channels/uk/uklocaltv:get_live_url',
        'label': 'Cardiff Local TV',
        'thumb': 'channels/uk/cardifflocal.png',
        'fanart': 'channels/uk/cardifflocal_fanart.jpg',
        'xmltv_id': '1171.tvguide.co.uk',
        'enabled': True,
        'order': 28
    },
    'leedslocal': {
        'resolver': '/resources/lib/channels/uk/uklocaltv:get_live_url',
        'label': 'Leeds Local TV',
        'thumb': 'channels/uk/leedslocal.png',
        'fanart': 'channels/uk/leedslocal_fanart.jpg',
        'xmltv_id': '1210.tvguide.co.uk',
        'enabled': True,
        'order': 29
    },
    'liverpoollocal': {
        'resolver': '/resources/lib/channels/uk/uklocaltv:get_live_url',
        'label': 'Liverpool Local TV',
        'thumb': 'channels/uk/liverpoollocal.png',
        'fanart': 'channels/uk/liverpoollocal_fanart.jpg',
        'xmltv_id': '1212.tvguide.co.uk',
        'enabled': True,
        'order': 30
    },
    'northwaleslocal': {
        'resolver': '/resources/lib/channels/uk/uklocaltv:get_live_url',
        'label': 'North Wales Local TV',
        'thumb': 'channels/uk/northwaleslocal.png',
        'fanart': 'channels/uk/northwaleslocal_fanart.jpg',
        'enabled': True,
        'order': 31
    },
    'teessidelocal': {
        'resolver': '/resources/lib/channels/uk/uklocaltv:get_live_url',
        'label': 'Teesside Local TV',
        'thumb': 'channels/uk/teessidelocal.png',
        'fanart': 'channels/uk/teessidelocal_fanart.jpg',
        'enabled': True,
        'order': 32
    },
    'twlocal': {
        'resolver': '/resources/lib/channels/uk/uklocaltv:get_live_url',
        'label': 'Tyne & Wear Local TV',
        'thumb': 'channels/uk/twlocal.png',
        'fanart': 'channels/uk/twlocal_fanart.jpg',
        'xmltv_id': '1255.tvguide.co.uk',
        'enabled': True,
        'order': 33
    },
    'really': {
        'resolver': '/resources/lib/channels/uk/discoveryplus:get_live_url',
        'label': 'Really',
        'thumb': 'channels/uk/really.png',
        'fanart': 'channels/uk/really_fanart.jpg',
        'xmltv_id': '422.tvguide.co.uk',
        'enabled': False,
        'order': 34
    },
    'food-network': {
        'resolver': '/resources/lib/channels/uk/discoveryplus:get_live_url',
        'label': 'Food Network',
        'thumb': 'channels/uk/foodnetwork.png',
        'fanart': 'channels/uk/foodnetwork_fanart.jpg',
        'xmltv_id': '596.tvguide.co.uk',
        'enabled': False,
        'order': 35
    },
    'dmax': {
        'resolver': '/resources/lib/channels/uk/discoveryplus:get_live_url',
        'label': 'DMAX',
        'thumb': 'channels/uk/dmax.png',
        'fanart': 'channels/uk/dmax_fanart.jpg',
        'xmltv_id': '454.tvguide.co.uk',
        'enabled': False,
        'order': 36
    },
    'home': {
        'resolver': '/resources/lib/channels/uk/discoveryplus:get_live_url',
        'label': 'HGTV',
        'thumb': 'channels/uk/hgtv.png',
        'fanart': 'channels/uk/hgtv_fanart.jpg',
        'enabled': False,
        'order': 37
    },
    'quest': {
        'resolver': '/resources/lib/channels/uk/discoveryplus:get_live_url',
        'label': 'Quest',
        'thumb': 'channels/uk/questtv.png',
        'fanart': 'channels/uk/questtv_fanart.jpg',
        'xmltv_id': '559.tvguide.co.uk',
        'enabled': False,
        'order': 38
    },
    'quest-red': {
        'resolver': '/resources/lib/channels/uk/discoveryplus:get_live_url',
        'label': 'Quest RED',
        'thumb': 'channels/uk/questred.png',
        'fanart': 'channels/uk/questred_fanart.jpg',
        'xmltv_id': '1014.tvguide.co.uk',
        'enabled': False,
        'order': 39
    },
    'C5': {
        'resolver': '/resources/lib/channels/uk/my5:get_live_url',
        'label': 'Channel 5 from My5',
        'thumb': 'channels/uk/five.png',
        'fanart': 'channels/uk/five_fanart.jpg',
        'enabled': True,
        'order': 40
    },
    'C6': {
        'resolver': '/resources/lib/channels/uk/my5:get_live_url',
        'label': '5 Star from My5',
        'thumb': 'channels/uk/fivestar.png',
        'fanart': 'channels/uk/fivestar_fanart.jpg',
        'enabled': True,
        'order': 41
    },
    'C7': {
        'resolver': '/resources/lib/channels/uk/my5:get_live_url',
        'label': '5 USA from My5',
        'thumb': 'channels/uk/fiveusa.png',
        'fanart': 'channels/uk/fiveusa_fanart.jpg',
        'enabled': True,
        'order': 42
    },
    'C0': {
        'resolver': '/resources/lib/channels/uk/my5:get_live_url',
        'label': '5 Action from My5',
        'thumb': 'channels/uk/5action.png',
        'fanart': 'channels/uk/5action_fanart.jpg',
        'enabled': True,
        'order': 43
    },
    'C8': {
        'resolver': '/resources/lib/channels/uk/my5:get_live_url',
        'label': '5 Select from My5',
        'thumb': 'channels/uk/5select.png',
        'fanart': 'channels/uk/5select_fanart.jpg',
        'enabled': True,
        'order': 44
    },
}
