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
    'adis': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'Addis TV',
        'thumb': 'channels/et/adis.png',
        'fanart': 'channels/et/adis_fanart.jpg',
        'enabled': True,
        'order': 1
    },
    'afri': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'Afrihealth',
        'thumb': 'channels/et/afri.png',
        'fanart': 'channels/et/afri_fanart.jpg',
        'enabled': True,
        'order': 2
    },
    'ahadu': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'Ahadu TV',
        'thumb': 'channels/et/ahadu.png',
        'fanart': 'channels/et/ahadu_fanart.jpg',
        'enabled': True,
        'order': 3
    },
    'aleph': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'Aleph TV',
        'thumb': 'channels/et/aleph.png',
        'fanart': 'channels/et/aleph_fanart.jpg',
        'enabled': True,
        'order': 4
    },
    'amma': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'Amhara TV',
        'thumb': 'channels/et/amma.png',
        'fanart': 'channels/et/amma_fanart.jpg',
        'enabled': True,
        'order': 5
    },
    'arts': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'ARTS TV',
        'thumb': 'channels/et/arts.png',
        'fanart': 'channels/et/arts_fanart.jpg',
        'enabled': True,
        'order': 6
    },
    'asham': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'Asham TV',
        'thumb': 'channels/et/asham.png',
        'fanart': 'channels/et/asham_fanart.jpg',
        'enabled': True,
        'order': 7
    },
    'asrat': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'ASRAT MEDIA',
        'thumb': 'channels/et/asrat.png',
        'fanart': 'channels/et/asrat_fanart.jpg',
        'enabled': True,
        'order': 8
    },
    'ava': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'AVA TV',
        'thumb': 'channels/et/ava.png',
        'fanart': 'channels/et/ava_fanart.jpg',
        'enabled': True,
        'order': 9
    },
    'balage': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'Balageru',
        'thumb': 'channels/et/balage.png',
        'fanart': 'channels/et/balage_fanart.jpg',
        'enabled': True,
        'order': 10
    },
    'bisrat': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'Bisrat TV',
        'thumb': 'channels/et/bisrat.png',
        'fanart': 'channels/et/bisrat_fanart.jpg',
        'enabled': True,
        'order': 11
    },
    'dws': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'DW TV',
        'thumb': 'channels/et/dws.png',
        'fanart': 'channels/et/dws_fanart.jpg',
        'enabled': True,
        'order': 12
    },
    'etvm': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'EBC MEZINAGNA',
        'thumb': 'channels/et/etvm.png',
        'fanart': 'channels/et/etvz_fanart.jpg',
        'enabled': True,
        'order': 13
    },
    'etvq': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'EBC QUANQUAWOCH',
        'thumb': 'channels/et/etvq.png',
        'fanart': 'channels/et/etvq_fanart.jpg',
        'enabled': True,
        'order': 14
    },
    'etvz': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'EBC ZENA',
        'thumb': 'channels/et/etvz.png',
        'fanart': 'channels/et/etvz_fanart.jpg',
        'enabled': True,
        'order': 15
    },
    'ectv': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'ECTV',
        'thumb': 'channels/et/ectv.png',
        'fanart': 'channels/et/ectv_fanart.jpg',
        'enabled': True,
        'order': 16
    },
    'eritr': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'Eritrea TV',
        'thumb': 'channels/et/eritr.png',
        'fanart': 'channels/et/eritr_fanart.jpg',
        'enabled': True,
        'order': 17
    },
    'esat': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'ESAT',
        'thumb': 'channels/et/esat.png',
        'fanart': 'channels/et/esat_fanart.jpg',
        'enabled': True,
        'order': 18
    },
    'estv': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'ES TV',
        'thumb': 'channels/et/estv.png',
        'fanart': 'channels/et/estv_fanart.jpg',
        'enabled': True,
        'order': 19
    },
    'fbctv': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'Fana TV',
        'thumb': 'channels/et/fbctv.png',
        'fanart': 'channels/et/fbctv_fanart.jpg',
        'enabled': True,
        'order': 20
    },
    'gloryg': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'Glory of GOD TV',
        'thumb': 'channels/et/gloryg.png',
        'fanart': 'channels/et/gloryg_fanart.jpg',
        'enabled': True,
        'order': 21
    },
    'holys': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'Holy Spirit TV',
        'thumb': 'channels/et/holys.png',
        'fanart': 'channels/et/holys_fanart.jpg',
        'enabled': True,
        'order': 22
    },
    'jtv': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'JTV ETHIOPIA',
        'thumb': 'channels/et/jtv.png',
        'fanart': 'channels/et/jtv_fanart.jpg',
        'enabled': True,
        'order': 23
    },
    'ltv': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'LTV',
        'thumb': 'channels/et/ltv.png',
        'fanart': 'channels/et/ltv_fanart.jpg',
        'enabled': True,
        'order': 24
    },
    'moe': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'MoE',
        'thumb': 'channels/et/moe.png',
        'fanart': 'channels/et/moe_fanart.jpg',
        'enabled': True,
        'order': 25
    },
    'nahoo': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'Nahoo TV',
        'thumb': 'channels/et/nahoo.png',
        'fanart': 'channels/et/nahoo_fanart.jpg',
        'enabled': True,
        'order': 26
    },
    'obn': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'OBN',
        'thumb': 'channels/et/obn.png',
        'fanart': 'channels/et/obn_fanart.jpg',
        'enabled': True,
        'order': 27
    },
    'obs': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'OBS',
        'thumb': 'channels/et/obs.png',
        'fanart': 'channels/et/obs_fanart.jpg',
        'enabled': True,
        'order': 28
    },
    'omn': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'OMN',
        'thumb': 'channels/et/omn.png',
        'fanart': 'channels/et/omn_fanart.jpg',
        'enabled': True,
        'order': 29
    },
    'onn': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'ONN TV',
        'thumb': 'channels/et/onn.png',
        'fanart': 'channels/et/onn_fanart.jpg',
        'enabled': True,
        'order': 30
    },
    'south': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'Southern TV',
        'thumb': 'channels/et/south.png',
        'fanart': 'channels/et/south_fanart.jpg',
        'enabled': True,
        'order': 31
    },
    'tigrai': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'Tigrai TV',
        'thumb': 'channels/et/tigrai.png',
        'fanart': 'channels/et/tigrai_fanart.jpg',
        'enabled': True,
        'order': 32
    },
    'walta': {
        'resolver': '/resources/lib/channels/et/video2b:get_live_url',
        'label': 'Walta TV',
        'thumb': 'channels/et/walta.png',
        'fanart': 'channels/et/walta_fanart.jpg',
        'enabled': True,
        'order': 33
    },
}
