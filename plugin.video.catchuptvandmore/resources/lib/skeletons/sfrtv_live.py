# -*- coding: utf-8 -*-

from __future__ import unicode_literals

# This dictionary is not really needed to list the live channels because the list is dynamically generated to keep
# only the active channels for the account.
# It is necessary to have the EPG by setting the xmltv id and also to have a higher-quality thumb.
# That's why a lot of code is commented out, this information is precisely what's missing for the commented channels.

menu = {
    'NEUF_TF1': {
        'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
        'label': 'TF1',
        'thumb': 'channels/fr/tf1.png',
        'fanart': 'channels/fr/tf1_fanart.jpg',
        'xmltv_id': 'C192.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 1,
        'enabled': True,
        'order': 1
    },
    'NEUF_FRANCE2': {
        'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
        'label': 'France 2',
        'thumb': 'channels/fr/france2.png',
        'fanart': 'channels/fr/france2_fanart.jpg',
        'xmltv_id': 'C4.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 2,
        'enabled': True,
        'order': 2
    },
    'NEUF_FRANCE3': {
        'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
        'label': 'France 3',
        'thumb': 'channels/fr/france3.png',
        'fanart': 'channels/fr/france3_fanart.jpg',
        'xmltv_id': 'C80.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 3,
        'enabled': True,
        'order': 3
    },
    'NEUF_FRANCE5': {
        'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
        'label': 'France 5',
        'thumb': 'channels/fr/france5.png',
        'fanart': 'channels/fr/france5_fanart.jpg',
        'xmltv_id': 'C47.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 5,
        'enabled': True,
        'order': 5
    },
    'NEUF_M6': {
        'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
        'label': 'M6',
        'thumb': 'channels/fr/m6.png',
        'fanart': 'channels/fr/m6_fanart.jpg',
        'xmltv_id': 'C118.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 6,
        'enabled': True,
        'order': 6
    },
    'NEUF_ARTE': {
        'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
        'label': 'Arte',
        'thumb': 'channels/fr/arte.png',
        'fanart': 'channels/fr/arte_fanart.jpg',
        'xmltv_id': 'C111.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 7,
        'enabled': True,
        'order': 7
    },
    'NEUF_DIRECT8': {
        'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
        'label': 'C8',
        'thumb': 'channels/fr/c8.png',
        'fanart': 'channels/fr/c8_fanart.jpg',
        'xmltv_id': 'C445.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 8,
        'enabled': True,
        'order': 8
    },
    'NEUF_W9': {
        'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
        'label': 'W9',
        'thumb': 'channels/fr/w9.png',
        'fanart': 'channels/fr/w9_fanart.jpg',
        'xmltv_id': 'C119.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 9,
        'enabled': True,
        'order': 9
    },
    'NEUF_TMC': {
        'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
        'label': 'TMC',
        'thumb': 'channels/fr/tmc.png',
        'fanart': 'channels/fr/tmc_fanart.jpg',
        'xmltv_id': 'C195.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 10,
        'enabled': True,
        'order': 10
    },
    'NEUF_NT1': {
        'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
        'label': 'TFX',
        'thumb': 'channels/fr/tfx.png',
        'fanart': 'channels/fr/tfx_fanart.jpg',
        'xmltv_id': 'C446.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 11,
        'enabled': True,
        'order': 11
    },
    'NEUF_NRJ12': {
        'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
        'label': 'NRJ12',
        'thumb': 'channels/fr/nrj12.png',
        'fanart': 'channels/fr/nrj12_fanart.jpg',
        'xmltv_id': 'C444.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 12,
        'enabled': True,
        'order': 12
    },
    'NEUF_LCP': {
        'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
        'label': 'LCP',
        'thumb': 'channels/fr/lcp.png',
        'fanart': 'channels/fr/lcp_fanart.jpg',
        'xmltv_id': 'C234.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 13,
        'enabled': True,
        'order': 13
    },
    'NEUF_FRANCE4': {
        'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
        'label': 'France 4',
        'thumb': 'channels/fr/france4.png',
        'fanart': 'channels/fr/france4_fanart.jpg',
        'xmltv_id': 'C78.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 14,
        'enabled': True,
        'order': 14
    },
    'NEUF_BFMTV': {
        'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
        'label': 'BFM TV',
        'thumb': 'channels/fr/bfmtv.png',
        'fanart': 'channels/fr/bfmtv_fanart.jpg',
        'xmltv_id': 'C481.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 15,
        'enabled': True,
        'order': 15
    },
    'NEUF_ITELE': {
        'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
        'label': 'CNews',
        'thumb': 'channels/fr/cnews.png',
        'fanart': 'channels/fr/cnews_fanart.jpg',
        'xmltv_id': 'C226.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 16,
        'enabled': True,
        'order': 16
    },
    'NEUF_VIRGIN17': {
        'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
        'label': 'CStar',
        'thumb': 'channels/fr/cstar.png',
        'fanart': 'channels/fr/cstar_fanart.jpg',
        'xmltv_id': 'C458.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 17,
        'enabled': True,
        'order': 17
    },
    'NEUF_GULLI': {
        'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
        'label': 'Gulli',
        'thumb': 'channels/fr/gulli.png',
        'fanart': 'channels/fr/gulli_fanart.jpg',
        'xmltv_id': 'C482.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 18,
        'enabled': True,
        'order': 18
    },
    'NEUF_HD1': {
        'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
        'label': 'TF1 Séries-Films',
        'thumb': 'channels/fr/tf1seriesfilms.png',
        'fanart': 'channels/fr/tf1seriesfilms_fanart.jpg',
        'xmltv_id': 'C1404.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 20,
        'enabled': True,
        'order': 20
    },
    'NEUF_LEQUIPETV': {
        'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
        'label': 'La chaine l’Équipe',
        'thumb': 'channels/fr/lequipe.png',
        'fanart': 'channels/fr/lequipe_fanart.jpg',
        'xmltv_id': 'C1401.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 21,
        'enabled': True,
        'order': 21
    },
    'NEUF_6TER': {
        'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
        'label': '6ter',
        'thumb': 'channels/fr/6ter.png',
        'fanart': 'channels/fr/6ter_fanart.jpg',
        'xmltv_id': 'C1403.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 22,
        'enabled': True,
        'order': 22
    },
    'NEUF_NUM23': {
        'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
        'label': 'RMC STORY',
        'thumb': 'channels/fr/rmcstory.png',
        'fanart': 'channels/fr/rmcstory_fanart.jpg',
        'xmltv_id': 'C1402.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 23,
        'enabled': True,
        'order': 23
    },
    'NEUF_RMCDEC': {
        'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
        'label': 'RMC Découverte',
        'thumb': 'channels/fr/rmcdecouverte.png',
        'fanart': 'channels/fr/rmcdecouverte_fanart.jpg',
        'xmltv_id': 'C1400.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 24,
        'enabled': True,
        'order': 24
    },
    'NEUF_CHERIE25': {
        'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
        'label': 'Chérie 25',
        'thumb': 'channels/fr/cherie25.png',
        'fanart': 'channels/fr/cherie25_fanart.jpg',
        'xmltv_id': 'C1399.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 25,
        'enabled': True,
        'order': 25
    },
    'NEUF_LCI': {
        'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
        'label': 'LCI',
        'thumb': 'channels/fr/lci.png',
        'fanart': 'channels/fr/lci_fanart.jpg',
        'xmltv_id': 'C112.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 26,
        'enabled': True,
        'order': 26
    },
    'NEUF_FRANCEINFO': {
        'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
        'label': 'franceinfo:',
        'thumb': 'channels/fr/franceinfo.png',
        'fanart': 'channels/fr/franceinfo_fanart.jpg',
        'xmltv_id': 'C2111.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 27,
        'enabled': True,
        'order': 27
    },
    'NEUF_GUYSEN': {
        'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
        'label': 'i24 news',
        'thumb': 'channels/fr/i24news.png',
        'fanart': 'channels/fr/i24news_fanart.jpg',
        'xmltv_id': 'C781.api.telerama.fr',
        'm3u_group': 'Satellite/FAI',
        'm3u_order': 28,
        'enabled': True,
        'order': 28
    },
    'NEUF_BFMBUSINESS': {
        'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
        'label': 'BFM Business',
        'thumb': 'channels/fr/bfmbusiness.png',
        'fanart': 'channels/fr/bfmbusiness_fanart.jpg',
        'xmltv_id': 'C1073.api.telerama.fr',
        'm3u_group': 'Satellite/FAI',
        'm3u_order': 31,
        'enabled': True,
        'order': 31
    },
    'NEUF_01NET': {
        'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
        'label': 'TECH & CO',
        'thumb': 'channels/fr/01net.png',
        'fanart': 'channels/fr/01net_fanart.jpg',
        'm3u_group': 'Satellite/FAI',
        'm3u_order': 32,
        'enabled': True,
        'order': 32
    },
}
