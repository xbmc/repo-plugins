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
    'rtl_tvi': {
        'resolver': '/resources/lib/channels/be/rtlplaybe:get_live_url',
        'label': 'RTL-TVI',
        'thumb': 'channels/be/rtltvi.png',
        'fanart': 'channels/be/rtltvi_fanart.jpg',
        'xmltv_id': 'C168.api.telerama.fr',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 2
    },
    'plug_rtl': {
        'resolver': '/resources/lib/channels/be/rtlplaybe:get_live_url',
        'label': 'PLUG RTL',
        'thumb': 'channels/be/plugrtl.png',
        'fanart': 'channels/be/plugrtl_fanart.jpg',
        'xmltv_id': 'C377.api.telerama.fr',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 3
    },
    'club_rtl': {
        'resolver': '/resources/lib/channels/be/rtlplaybe:get_live_url',
        'label': 'CLUB RTL',
        'thumb': 'channels/be/clubrtl.png',
        'fanart': 'channels/be/clubrtl_fanart.jpg',
        'xmltv_id': 'C50.api.telerama.fr',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 4
    },
    'telemb': {
        'resolver': '/resources/lib/channels/be/telemb:get_live_url',
        'label': 'Télé MB',
        'thumb': 'channels/be/telemb.png',
        'fanart': 'channels/be/telemb_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 6
    },
    'rtc': {
        'resolver': '/resources/lib/channels/be/rtc:get_live_url',
        'label': 'RTC Télé Liège',
        'thumb': 'channels/be/rtc.png',
        'fanart': 'channels/be/rtc_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 7
    },
    'auvio': {
        'route': '/resources/lib/channels/be/rtbf:list_lives',
        'label': 'RTBF Auvio',
        'thumb': 'channels/be/auvio.png',
        'fanart': 'channels/be/auvio_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 8
    },
    'tvlux': {
        'resolver': '/resources/lib/channels/be/tvlux:get_live_url',
        'label': 'TV Lux',
        'thumb': 'channels/be/tvlux.png',
        'fanart': 'channels/be/tvlux_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 9
    },
    'rtl_info': {
        'resolver': '/resources/lib/channels/be/rtlplaybe:get_live_url',
        'label': 'RTL INFO',
        'thumb': 'channels/be/rtlinfo.png',
        'fanart': 'channels/be/rtlinfo_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 10
    },
    'bel_rtl': {
        'resolver': '/resources/lib/channels/be/rtlplaybe:get_live_url',
        'label': 'BEL RTL',
        'thumb': 'channels/be/belrtl.png',
        'fanart': 'channels/be/belrtl_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 11
    },
    'contact': {
        'resolver': '/resources/lib/channels/be/rtlplaybe:get_live_url',
        'label': 'Contact',
        'thumb': 'channels/be/contact.png',
        'fanart': 'channels/be/contact_fanart.jpg',
        'm3u_group': 'Belgique fr Radio',
        'enabled': True,
        'order': 12
    },
    'bx1': {
        'resolver': '/resources/lib/channels/be/bx1:get_live_url',
        'label': 'BX1',
        'thumb': 'channels/be/bx1.png',
        'fanart': 'channels/be/bx1_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 13
    },
    'een': {
        'resolver': '/resources/lib/channels/be/vrt:get_live_url',
        'label': 'Één',
        'thumb': 'channels/be/een.png',
        'fanart': 'channels/be/een_fanart.jpg',
        'xmltv_id': 'C23.api.telerama.fr',
        'm3u_group': 'België nl',
        'enabled': True,
        'order': 14
    },
    'canvas': {
        'resolver': '/resources/lib/channels/be/vrt:get_live_url',
        'label': 'Canvas',
        'thumb': 'channels/be/canvas.png',
        'fanart': 'channels/be/canvas_fanart.jpg',
        'm3u_group': 'België nl',
        'enabled': True,
        'order': 15
    },
    'ketnet': {
        'resolver': '/resources/lib/channels/be/vrt:get_live_url',
        'label': 'Ketnet',
        'thumb': 'channels/be/ketnet.png',
        'fanart': 'channels/be/ketnet_fanart.jpg',
        'xmltv_id': 'C1280.api.telerama.fr',
        'm3u_group': 'België nl',
        'enabled': True,
        'order': 16
    },
    'nrjhitstvbe': {
        'resolver': '/resources/lib/channels/be/nrjhitstvbe:get_live_url',
        'label': 'NRJ Hits TV',
        'thumb': 'channels/be/nrjhitstvbe.png',
        'fanart': 'channels/be/nrjhitstvbe_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 17
    },
    'rtl_sport': {
        'resolver': '/resources/lib/channels/be/rtlplaybe:get_live_url',
        'label': 'RTL Sport',
        'thumb': 'channels/be/rtlsport.png',
        'fanart': 'channels/be/rtlsport_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 18
    },
    'tvcom': {
        'resolver': '/resources/lib/channels/be/tvcom:get_live_url',
        'label': 'TV Com',
        'thumb': 'channels/be/tvcom.png',
        'fanart': 'channels/be/tvcom_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 19
    },
    'bouke': {
        'resolver': '/resources/lib/channels/be/bouke:get_live_url',
        'label': 'Bouké',
        'thumb': 'channels/be/bouke.png',
        'fanart': 'channels/be/bouke.png',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 20
    },
    'abxplore': {
        'resolver': '/resources/lib/channels/be/abbe:get_live_url',
        'label': 'ABXPLORE',
        'thumb': 'channels/be/abxplore.png',
        'fanart': 'channels/be/abxplore_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 21
    },
    'ab3': {
        'resolver': '/resources/lib/channels/be/abbe:get_live_url',
        'label': 'AB3',
        'thumb': 'channels/be/ab3.png',
        'fanart': 'channels/be/ab3_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 22
    },
    'ln24': {
        'resolver': '/resources/lib/channels/be/ln24:get_live_url',
        'label': 'LN24',
        'thumb': 'channels/be/ln24.png',
        'fanart': 'channels/be/ln24_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 23
    },
    'laune': {
        'resolver': '/resources/lib/channels/be/rtbf:set_live_url',
        'label': 'La Une',
        'thumb': 'channels/be/laune.png',
        'fanart': 'channels/be/laune_fanart.jpg',
        'xmltv_id': 'C164.api.telerama.fr',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 24
    },
    'tipiktv': {
        'resolver': '/resources/lib/channels/be/rtbf:set_live_url',
        'label': 'Tipik',
        'thumb': 'channels/be/tipik.png',
        'fanart': 'channels/be/tipik_fanart.jpg',
        'xmltv_id': 'C187.api.telerama.fr',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 25
    },
    'latrois': {
        'resolver': '/resources/lib/channels/be/rtbf:set_live_url',
        'label': 'La Trois',
        'thumb': 'channels/be/latrois.png',
        'fanart': 'channels/be/latrois_fanart.jpg',
        'xmltv_id': 'C892.api.telerama.fr',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 26
    },
    'tipik': {
        'resolver': '/resources/lib/channels/be/rtbf:set_live_url',
        'label': 'TipikVision',
        'thumb': 'channels/be/tipik.png',
        'fanart': 'channels/be/tipik_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 27
    },
    'actv': {
        'resolver': '/resources/lib/channels/be/actv:get_live_url',
        'label': 'Antenne Centre TV',
        'thumb': 'channels/be/actv.png',
        'fanart': 'channels/be/actv_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 28
    },
    'telesambre': {
        'resolver': '/resources/lib/channels/be/telesambre:get_live_url',
        'label': 'Télésambre',
        'thumb': 'channels/be/telesambre.png',
        'fanart': 'channels/be/telesambre_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 29
    },
    'atv': {
        'resolver': '/resources/lib/channels/be/atv:get_live_url',
        'label': 'ATV (Antwerpen)',
        'thumb': 'channels/be/atv.png',
        'fanart': 'channels/be/atv_fanart.jpg',
        'm3u_group': 'België nl',
        'enabled': True,
        'order': 30,
    },
    'bruzz': {
        'resolver': '/resources/lib/channels/be/bruzz:get_live_url',
        'label': 'BRUZZ (Brussel)',
        'thumb': 'channels/be/bruzz.png',
        'fanart': 'channels/be/bruzz_fanart.jpg',
        'm3u_group': 'België nl',
        'enabled': True,
        'order': 31,
    },
    'focuswtv': {
        'resolver': '/resources/lib/channels/be/focuswtv:get_live_url',
        'label': 'Focus & WTV (West-Vlaanderen)',
        'thumb': 'channels/be/focuswtv.png',
        'fanart': 'channels/be/focuswtv_fanart.jpg',
        'm3u_group': 'België nl',
        'enabled': True,
        'order': 32,
    },
    'robtv': {
        'resolver': '/resources/lib/channels/be/robtv:get_live_url',
        'label': 'ROB-tv (Oost-Brabant)',
        'thumb': 'channels/be/robtv.png',
        'fanart': 'channels/be/robtv_fanart.jpg',
        'm3u_group': 'België nl',
        'enabled': True,
        'order': 33,
    },
    'tvl': {
        'resolver': '/resources/lib/channels/be/tvl:get_live_url',
        'label': 'TVL (Limburg)',
        'thumb': 'channels/be/tvl.png',
        'fanart': 'channels/be/tvl_fanart.jpg',
        'm3u_group': 'België nl',
        'enabled': True,
        'order': 34,
    },
    'tvoost': {
        'resolver': '/resources/lib/channels/be/tvoost:get_live_url',
        'label': 'TV Oost (Oost-Vlaanderen)',
        'thumb': 'channels/be/tvoost.png',
        'fanart': 'channels/be/tvoost_fanart.jpg',
        'm3u_group': 'België nl',
        'enabled': True,
        'order': 35,
    },
    'hln_live': {
        'resolver': '/resources/lib/channels/be/hln:get_live_url',
        'label': 'HLN Live',
        'thumb': 'channels/be/hln_live.png',
        'fanart': 'channels/be/hln_live_fanart.jpg',
        'm3u_group': 'België nl',
        'enabled': True,
        'order': 36,
    },
    'canalzoom': {
        'resolver': '/resources/lib/channels/be/canalzoom:get_live_url',
        'label': 'Canal Zoom',
        'thumb': 'channels/be/canalzoom.png',
        'fanart': 'channels/be/canalzoom.png',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 37,
    },
    'matele': {
        'resolver': '/resources/lib/channels/be/matele:get_live_url',
        'label': 'MATELE',
        'thumb': 'channels/be/matele.png',
        'fanart': 'channels/be/matele.png',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 38,
    },
    'notele': {
        'resolver': '/resources/lib/channels/be/notele:get_live_url',
        'label': 'notélé',
        'thumb': 'channels/be/notele.png',
        'fanart': 'channels/be/notele_fanart.jpg',
        'm3u_group': 'Belgique fr',
        'enabled': True,
        'order': 39,
    },
    'mnm': {
        'resolver': '/resources/lib/channels/be/mnm:get_live_url',
        'label': 'MNM',
        'thumb': 'channels/be/mnm.png',
        'fanart': 'channels/be/mnm.png',
        'm3u_group': 'België nl',
        'enabled': True,
        'order': 40,
    },
    'citymusic': {
        'resolver': '/resources/lib/channels/be/citymusic:get_live_url',
        'label': 'City-Music',
        'thumb': 'channels/be/citymusic.png',
        'fanart': 'channels/be/citymusic.png',
        'm3u_group': 'België nl',
        'enabled': True,
        'order': 41,
    }
}
