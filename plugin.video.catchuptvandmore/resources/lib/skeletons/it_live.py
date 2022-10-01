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
    },
    'C5': {
        'resolver': '/resources/lib/channels/it/mediaset:get_live_url',
        'label': 'Canale 5',
        'thumb': 'channels/it/canale5.png',
        'fanart': 'channels/it/canale5_fanart.jpg',
        'enabled': True,
        'order': 18
    },
    'I1': {
        'resolver': '/resources/lib/channels/it/mediaset:get_live_url',
        'label': 'Italia 1',
        'thumb': 'channels/it/italia1.png',
        'fanart': 'channels/it/italia1_fanart.jpg',
        'enabled': True,
        'order': 19
    },
    'R4': {
        'resolver': '/resources/lib/channels/it/mediaset:get_live_url',
        'label': 'Rete 4',
        'thumb': 'channels/it/rete4.png',
        'fanart': 'channels/it/rete4_fanart.jpg',
        'enabled': True,
        'order': 20
    },
    'LB': {
        'resolver': '/resources/lib/channels/it/mediaset:get_live_url',
        'label': '20',
        'thumb': 'channels/it/20.png',
        'fanart': 'channels/it/20_fanart.jpg',
        'enabled': True,
        'order': 21
    },
    'KA': {
        'resolver': '/resources/lib/channels/it/mediaset:get_live_url',
        'label': 'La 5',
        'thumb': 'channels/it/la5.png',
        'fanart': 'channels/it/la5_fanart.jpg',
        'enabled': True,
        'order': 22
    },
    'I2': {
        'resolver': '/resources/lib/channels/it/mediaset:get_live_url',
        'label': 'Italia 2',
        'thumb': 'channels/it/italia2.png',
        'fanart': 'channels/it/italia2_fanart.jpg',
        'enabled': True,
        'order': 23
    },
    'B6': {
        'resolver': '/resources/lib/channels/it/mediaset:get_live_url',
        'label': 'Cine34',
        'thumb': 'channels/it/cine34.png',
        'fanart': 'channels/it/cine34_fanart.jpg',
        'enabled': True,
        'order': 24
    },
    'KQ': {
        'resolver': '/resources/lib/channels/it/mediaset:get_live_url',
        'label': 'Mediaset Extra',
        'thumb': 'channels/it/mediasetextra.png',
        'fanart': 'channels/it/mediasetextra_fanart.jpg',
        'enabled': True,
        'order': 25
    },
    'FU': {
        'resolver': '/resources/lib/channels/it/mediaset:get_live_url',
        'label': 'Focus',
        'thumb': 'channels/it/focus.png',
        'fanart': 'channels/it/focus_fanart.jpg',
        'enabled': True,
        'order': 26
    },
    'LT': {
        'resolver': '/resources/lib/channels/it/mediaset:get_live_url',
        'label': 'Top Crime',
        'thumb': 'channels/it/topcrime.png',
        'fanart': 'channels/it/topcrime_fanart.jpg',
        'enabled': True,
        'order': 27
    },
    'KI': {
        'resolver': '/resources/lib/channels/it/mediaset:get_live_url',
        'label': 'Iris',
        'thumb': 'channels/it/iris.png',
        'fanart': 'channels/it/iris_fanart.jpg',
        'enabled': True,
        'order': 28
    },
    'BP': {
        'resolver': '/resources/lib/channels/it/mediaset:get_live_url',
        'label': 'Boing Plus',
        'thumb': 'channels/it/boingplus.png',
        'fanart': 'channels/it/boingplus_fanart.jpg',
        'enabled': True,
        'order': 29
    },
    'LA': {
        'resolver': '/resources/lib/channels/it/mediaset:get_live_url',
        'label': 'Cartoonito',
        'thumb': 'channels/it/cartoonito.png',
        'fanart': 'channels/it/cartoonito_fanart.jpg',
        'enabled': True,
        'order': 30
    },
    'KF': {
        'resolver': '/resources/lib/channels/it/mediaset:get_live_url',
        'label': 'TGCom',
        'thumb': 'channels/it/tgcom.png',
        'fanart': 'channels/it/tgcom_fanart.jpg',
        'enabled': True,
        'order': 31
    },
    'rtl': {
        'route': '/resources/lib/channels/it/rtl:list_lives',
        'label': 'RTL 102.5 Radiovisione',
        'thumb': 'channels/it/rtl-1025-radiovisione.png',
        'fanart': 'channels/it/rtl-1025-radiovisione.png',
        'enabled': True,
        'order': 32
    }
}
