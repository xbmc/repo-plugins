# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2016  SylvainCecchetto

    This file is part of Catch-up TV & More.

    Catch-up TV & More is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Catch-up TV & More is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with Catch-up TV & More; if not, write to the Free Software Foundation,
    Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals
from codequick import Script, utils
"""
The following dictionaries describe
the addon's tree architecture.
* Key: item id
* Value: item infos
    - callback: Callback function to run once this item is selected
    - thumb: Item thumb path relative to "media" folder
    - fanart: Item fanart path relative to "meia" folder
    - module: Item module to load in order to work (like 6play.py)
"""

menu = {
    'tf1': {
        'callback': 'live_bridge',
        'label': 'TF1',
        'thumb': 'channels/fr/tf1.png',
        'fanart': 'channels/fr/tf1_fanart.jpg',
        'module': 'resources.lib.channels.fr.mytf1',
        'xmltv_id': 'C192.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 1,
        'enabled': True,
        'order': 1
    },
    'france-2': {
        'callback': 'live_bridge',
        'label': 'France 2',
        'thumb': 'channels/fr/france2.png',
        'fanart': 'channels/fr/france2_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetv',
        'xmltv_id': 'C4.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 2,
        'enabled': True,
        'order': 2
    },
    'france-3': {
        'callback': 'live_bridge',
        'label': 'France 3',
        'thumb': 'channels/fr/france3.png',
        'fanart': 'channels/fr/france3_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetv',
        'xmltv_id': 'C80.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 3,
        'enabled': True,
        'order': 3
    },
    'canalplus': {
        'callback': 'live_bridge',
        'label': 'Canal +',
        'thumb': 'channels/fr/canalplus.png',
        'fanart': 'channels/fr/canalplus_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal',
        'xmltv_id': 'C34.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 4,
        'enabled': True,
        'order': 4
    },
    'france-5': {
        'callback': 'live_bridge',
        'label': 'France 5',
        'thumb': 'channels/fr/france5.png',
        'fanart': 'channels/fr/france5_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetv',
        'xmltv_id': 'C47.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 5,
        'enabled': True,
        'order': 5
    },
    'm6': {
        'callback': 'live_bridge',
        'label': 'M6',
        'thumb': 'channels/fr/m6.png',
        'fanart': 'channels/fr/m6_fanart.jpg',
        'module': 'resources.lib.channels.fr.6play',
        'xmltv_id': 'C118.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 6,
        'enabled': True,
        'order': 6
    },
    'c8': {
        'callback': 'live_bridge',
        'label': 'C8',
        'thumb': 'channels/fr/c8.png',
        'fanart': 'channels/fr/c8_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal',
        'xmltv_id': 'C445.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 8,
        'enabled': True,
        'order': 7
    },
    'w9': {
        'callback': 'live_bridge',
        'label': 'W9',
        'thumb': 'channels/fr/w9.png',
        'fanart': 'channels/fr/w9_fanart.jpg',
        'module': 'resources.lib.channels.fr.6play',
        'xmltv_id': 'C119.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 9,
        'enabled': True,
        'order': 8
    },
    'tmc': {
        'callback': 'live_bridge',
        'label': 'TMC',
        'thumb': 'channels/fr/tmc.png',
        'fanart': 'channels/fr/tmc_fanart.jpg',
        'module': 'resources.lib.channels.fr.mytf1',
        'xmltv_id': 'C195.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 10,
        'enabled': True,
        'order': 9
    },
    'tfx': {
        'callback': 'live_bridge',
        'label': 'TFX',
        'thumb': 'channels/fr/tfx.png',
        'fanart': 'channels/fr/tfx_fanart.jpg',
        'module': 'resources.lib.channels.fr.mytf1',
        'xmltv_id': 'C446.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 11,
        'enabled': True,
        'order': 10
    },
    'nrj12': {
        'callback': 'live_bridge',
        'label': 'NRJ 12',
        'thumb': 'channels/fr/nrj12.png',
        'fanart': 'channels/fr/nrj12_fanart.jpg',
        'module': 'resources.lib.channels.fr.nrj',
        'xmltv_id': 'C444.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 12,
        'enabled': True,
        'order': 11
    },
    'france-4': {
        'callback': 'live_bridge',
        'label': 'France 4',
        'thumb': 'channels/fr/france4.png',
        'fanart': 'channels/fr/france4_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetv',
        'xmltv_id': 'C78.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 14,
        'enabled': True,
        'order': 12
    },
    'bfmtv': {
        'callback': 'live_bridge',
        'label': 'BFM TV',
        'thumb': 'channels/fr/bfmtv.png',
        'fanart': 'channels/fr/bfmtv_fanart.jpg',
        'module': 'resources.lib.channels.fr.bfmtv',
        'xmltv_id': 'C481.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 15,
        'enabled': True,
        'order': 13
    },
    'cnews': {
        'callback': 'live_bridge',
        'label': 'CNews',
        'thumb': 'channels/fr/cnews.png',
        'fanart': 'channels/fr/cnews_fanart.jpg',
        'module': 'resources.lib.channels.fr.cnews',
        'xmltv_id': 'C226.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 16,
        'enabled': True,
        'order': 14
    },
    'cstar': {
        'callback': 'live_bridge',
        'label': 'CStar',
        'thumb': 'channels/fr/cstar.png',
        'fanart': 'channels/fr/cstar_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal',
        'xmltv_id': 'C458.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 17,
        'enabled': True,
        'order': 15
    },
    'gulli': {
        'callback': 'live_bridge',
        'label': 'Gulli',
        'thumb': 'channels/fr/gulli.png',
        'fanart': 'channels/fr/gulli_fanart.jpg',
        'module': 'resources.lib.channels.fr.gulli',
        'xmltv_id': 'C482.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 18,
        'enabled': True,
        'order': 16
    },
    'france-o': {
        'callback': 'live_bridge',
        'label': 'France Ô',
        'thumb': 'channels/fr/franceo.png',
        'fanart': 'channels/fr/franceo_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetv',
        'xmltv_id': 'C160.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 19,
        'enabled': True,
        'order': 17
    },
    'tf1-series-films': {
        'callback': 'live_bridge',
        'label': 'TF1 Séries Films',
        'thumb': 'channels/fr/tf1seriesfilms.png',
        'fanart': 'channels/fr/tf1seriesfilms_fanart.jpg',
        'module': 'resources.lib.channels.fr.mytf1',
        'xmltv_id': 'C1404.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 20,
        'enabled': True,
        'order': 18
    },
    'lequipe': {
        'callback': 'live_bridge',
        'label': 'L\'Équipe',
        'thumb': 'channels/fr/lequipe.png',
        'fanart': 'channels/fr/lequipe_fanart.jpg',
        'module': 'resources.lib.channels.fr.lequipe',
        'xmltv_id': 'C1401.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 21,
        'enabled': True,
        'order': 19
    },
    '6ter': {
        'callback': 'live_bridge',
        'label': '6ter',
        'thumb': 'channels/fr/6ter.png',
        'fanart': 'channels/fr/6ter_fanart.jpg',
        'module': 'resources.lib.channels.fr.6play',
        'xmltv_id': 'C1403.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 22,
        'enabled': True,
        'order': 20
    },
    'rmcstory': {
        'callback': 'live_bridge',
        'label': 'RMC Story',
        'thumb': 'channels/fr/rmcstory.png',
        'fanart': 'channels/fr/rmcstory_fanart.jpg',
        'module': 'resources.lib.channels.fr.rmc',
        'xmltv_id': 'C1402.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 23,
        'enabled': True,
        'order': 21
    },
    'cherie25': {
        'callback': 'live_bridge',
        'label': 'Chérie 25',
        'thumb': 'channels/fr/cherie25.png',
        'fanart': 'channels/fr/cherie25_fanart.jpg',
        'module': 'resources.lib.channels.fr.nrj',
        'xmltv_id': 'C1399.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 25,
        'enabled': True,
        'order': 22
    },
    'la_1ere': {
        'callback':
        'live_bridge',
        'label': 'La 1ère (' + utils.ensure_unicode(Script.setting['la_1ere.language']) + ')',
        'thumb':
        'channels/fr/la1ere.png',
        'fanart':
        'channels/fr/la1ere_fanart.jpg',
        'module':
        'resources.lib.channels.fr.la_1ere',
        'm3u_group':
        'Région',
        'available_languages': [
            "Guadeloupe", "Guyane", "Martinique", "Mayotte",
            "Nouvelle Calédonie", "Polynésie", "Réunion",
            "St-Pierre et Miquelon", "Wallis et Futuna"
        ],
        'enabled': True,
        'order': 23
    },
    'franceinfo': {
        'callback': 'live_bridge',
        'label': 'France Info',
        'thumb': 'channels/fr/franceinfo.png',
        'fanart': 'channels/fr/franceinfo_fanart.jpg',
        'module': 'resources.lib.channels.fr.franceinfo',
        'xmltv_id': 'C2111.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 27,
        'enabled': True,
        'order': 24
    },
    'bfmbusiness': {
        'callback': 'live_bridge',
        'label': 'BFM Business',
        'thumb': 'channels/fr/bfmbusiness.png',
        'fanart': 'channels/fr/bfmbusiness_fanart.jpg',
        'module': 'resources.lib.channels.fr.bfmtv',
        'xmltv_id': 'C1073.api.telerama.fr',
        'm3u_group': 'Satellite/FAI',
        'enabled': True,
        'order': 25
    },
    'lci': {
        'callback': 'live_bridge',
        'label': 'LCI',
        'thumb': 'channels/fr/lci.png',
        'fanart': 'channels/fr/lci_fanart.jpg',
        'module': 'resources.lib.channels.fr.lci',
        'xmltv_id': 'C112.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 26,
        'enabled': True,
        'order': 30
    },
    'lcp': {
        'callback': 'live_bridge',
        'label': 'LCP Assemblée Nationale',
        'thumb': 'channels/fr/lcp.png',
        'fanart': 'channels/fr/lcp_fanart.jpg',
        'module': 'resources.lib.channels.fr.lcp',
        'xmltv_id': 'C234.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 13,
        'enabled': True,
        'order': 31
    },
    'rmcdecouverte': {
        'callback': 'live_bridge',
        'label': 'RMC Découverte',
        'thumb': 'channels/fr/rmcdecouverte.png',
        'fanart': 'channels/fr/rmcdecouverte_fanart.jpg',
        'module': 'resources.lib.channels.fr.rmc',
        'xmltv_id': 'C1400.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 24,
        'enabled': True,
        'order': 32
    },
    'publicsenat': {
        'callback': 'live_bridge',
        'label': 'Public Sénat',
        'thumb': 'channels/fr/publicsenat.png',
        'fanart': 'channels/fr/publicsenat_fanart.jpg',
        'module': 'resources.lib.channels.fr.publicsenat',
        'xmltv_id': 'C234.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 13,
        'enabled': True,
        'order': 39
    },
    'france3regions': {
        'callback':
        'live_bridge',
        'label': 'France 3 Régions (' + utils.ensure_unicode(Script.setting['france3regions.language']) + ')',
        'thumb':
        'channels/fr/france3regions.png',
        'fanart':
        'channels/fr/france3regions_fanart.jpg',
        'module':
        'resources.lib.channels.fr.france3regions',
        'm3u_group':
        'Région',
        'available_languages': [
            'Alpes', 'Alsace', 'Aquitaine', 'Auvergne', 'Bourgogne',
            'Bretagne', 'Centre-Val de Loire', 'Chapagne-Ardenne', 'Corse',
            "Côte d'Azur", 'Franche-Compté', 'Languedoc-Roussillon',
            'Limousin', 'Lorraine', 'Midi-Pyrénées', 'Nord-Pas-de-Calais',
            'Basse-Normandie', 'Haute-Normandie', 'Paris Île-de-France',
            'Pays de la Loire', 'Picardie', 'Poitou-Charentes',
            'Provence-Alpes', 'Rhône-Alpes', 'Nouvelle-Aquitaine'
        ],
        'enabled': True,
        'order': 40
    },
    'francetvsport': {
        'callback': 'multi_live_bridge',
        'label': 'France TV Sport (francetv)',
        'thumb': 'channels/fr/francetvsport.png',
        'fanart': 'channels/fr/francetvsport_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetvsport',
        'm3u_group': 'Satellite/FAI',
        'enabled': True,
        'order': 41
    },
    'gong': {
        'callback': 'live_bridge',
        'label': 'Gong',
        'thumb': 'channels/fr/gong.png',
        'fanart': 'channels/fr/gong_fanart.jpg',
        'module': 'resources.lib.channels.fr.gong',
        'm3u_group': 'Satellite/FAI',
        'enabled': True,
        'order': 55
    },
    'bfmparis': {
        'callback': 'live_bridge',
        'label': 'BFM Paris',
        'thumb': 'channels/fr/bfmparis.png',
        'fanart': 'channels/fr/bfmparis_fanart.jpg',
        'module': 'resources.lib.channels.fr.bfmregion',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 56
    },
    'fun_radio': {
        'callback': 'live_bridge',
        'label': 'Fun Radio',
        'thumb': 'channels/fr/funradio.png',
        'fanart': 'channels/fr/funradio_fanart.jpg',
        'module': 'resources.lib.channels.fr.6play',
        'm3u_group': 'Radio',
        'enabled': True,
        'order': 58
    },
    'kto': {
        'callback': 'live_bridge',
        'label': 'KTO',
        'thumb': 'channels/fr/kto.png',
        'fanart': 'channels/fr/kto_fanart.jpg',
        'module': 'resources.lib.channels.fr.kto',
        'm3u_group': 'Satellite/FAI',
        'enabled': True,
        'order': 64
    },
    'antennereunion': {
        'callback': 'live_bridge',
        'label': 'Antenne Réunion',
        'thumb': 'channels/fr/antennereunion.png',
        'fanart': 'channels/fr/antennereunion_fanart.jpg',
        'module': 'resources.lib.channels.fr.antennereunion',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 65
    },
    'viaoccitanie': {
        'callback': 'live_bridge',
        'label': 'viàOccitanie',
        'thumb': 'channels/fr/viaoccitanie.png',
        'fanart': 'channels/fr/viaoccitanie_fanart.jpg',
        'module': 'resources.lib.channels.fr.via',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 66
    },
    'ouatchtv': {
        'callback': 'live_bridge',
        'label': 'Ouatch TV',
        'thumb': 'channels/fr/ouatchtv.png',
        'fanart': 'channels/fr/ouatchtv_fanart.jpg',
        'module': 'resources.lib.channels.fr.ouatchtv',
        'm3u_group': 'Satellite/FAI',
        'enabled': True,
        'order': 67
    },
    'canal10': {
        'callback': 'live_bridge',
        'label': 'Canal 10',
        'thumb': 'channels/fr/canal10.png',
        'fanart': 'channels/fr/canal10_fanart.jpg',
        'module': 'resources.lib.channels.fr.canal10',
        'm3u_group': 'Région',
        'enabled': False,
        'order': 68
    },
    'rtl2': {
        'callback': 'live_bridge',
        'label': 'RTL 2',
        'thumb': 'channels/fr/rtl2.png',
        'fanart': 'channels/fr/rtl2_fanart.jpg',
        'module': 'resources.lib.channels.fr.6play',
        'm3u_group': 'Radio',
        'enabled': True,
        'order': 69
    },
    'viaatv': {
        'callback': 'live_bridge',
        'label': 'viàATV',
        'thumb': 'channels/fr/viaatv.png',
        'fanart': 'channels/fr/viaatv_fanart.jpg',
        'module': 'resources.lib.channels.fr.via',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 72
    },
    'viagrandparis': {
        'callback': 'live_bridge',
        'label': 'viàGrandParis',
        'thumb': 'channels/fr/viagrandparis.png',
        'fanart': 'channels/fr/viagrandparis_fanart.jpg',
        'module': 'resources.lib.channels.fr.via',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 73
    },
    'tebeo': {
        'callback': 'live_bridge',
        'label': 'Tébéo',
        'thumb': 'channels/fr/tebeo.png',
        'fanart': 'channels/fr/tebeo_fanart.jpg',
        'module': 'resources.lib.channels.fr.tebeo',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 77
    },
    'mb': {
        'callback': 'live_bridge',
        'label': 'M6 Boutique',
        'thumb': 'channels/fr/mb.png',
        'fanart': 'channels/fr/mb_fanart.jpg',
        'module': 'resources.lib.channels.fr.6play',
        'xmltv_id': 'C184.api.telerama.fr',
        'm3u_group': 'Satellite/FAI',
        'enabled': True,
        'order': 78
    },
    'vialmtv': {
        'callback': 'live_bridge',
        'label': 'viàLMTv Sarthe',
        'thumb': 'channels/fr/vialmtv.png',
        'fanart': 'channels/fr/vialmtv_fanart.jpg',
        'module': 'resources.lib.channels.fr.via',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 79
    },
    'viamirabelle': {
        'callback': 'live_bridge',
        'label': 'viàMirabelle',
        'thumb': 'channels/fr/viamirabelle.png',
        'fanart': 'channels/fr/viamirabelle_fanart.jpg',
        'module': 'resources.lib.channels.fr.via',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 80
    },
    'viavosges': {
        'callback': 'live_bridge',
        'label': 'viàVosges',
        'thumb': 'channels/fr/viavosges.png',
        'fanart': 'channels/fr/viavosges_fanart.jpg',
        'module': 'resources.lib.channels.fr.via',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 81
    },
    'tl7': {
        'callback': 'live_bridge',
        'label': 'Télévision Loire 7',
        'thumb': 'channels/fr/tl7.png',
        'fanart': 'channels/fr/tl7_fanart.jpg',
        'module': 'resources.lib.channels.fr.tl7',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 82
    },
    'luckyjack': {
        'callback': 'live_bridge',
        'label': 'Lucky Jack',
        'thumb': 'channels/fr/luckyjack.png',
        'fanart': 'channels/fr/luckyjack_fanart.jpg',
        'module': 'resources.lib.channels.fr.abweb',
        'm3u_group': 'Satellite/FAI',
        'enabled': True,
        'order': 83
    },
    'mblivetv': {
        'callback': 'live_bridge',
        'label': 'Mont Blanc Live TV',
        'thumb': 'channels/fr/mblivetv.png',
        'fanart': 'channels/fr/mblivetv_fanart.jpg',
        'module': 'resources.lib.channels.fr.mblivetv',
        'm3u_group': 'Satellite/FAI',
        'enabled': True,
        'order': 84
    },
    'tv8montblanc': {
        'callback': 'live_bridge',
        'label': '8 Mont-Blanc',
        'thumb': 'channels/fr/tv8montblanc.png',
        'fanart': 'channels/fr/tv8montblanc_fanart.jpg',
        'module': 'resources.lib.channels.fr.tv8montblanc',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 85
    },
    'alsace20': {
        'callback': 'live_bridge',
        'label': 'Alsace 20',
        'thumb': 'channels/fr/alsace20.png',
        'fanart': 'channels/fr/alsace20_fanart.jpg',
        'module': 'resources.lib.channels.fr.alsace20',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 87
    },
    'tvpifr': {
        'callback': 'live_bridge',
        'label': 'TVPI télévision d\'ici',
        'thumb': 'channels/fr/tvpifr.png',
        'fanart': 'channels/fr/tvpifr_fanart.jpg',
        'module': 'resources.lib.channels.fr.tvpifr',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 89
    },
    'idf1': {
        'callback': 'live_bridge',
        'label': 'IDF 1',
        'thumb': 'channels/fr/idf1.png',
        'fanart': 'channels/fr/idf1_fanart.jpg',
        'module': 'resources.lib.channels.fr.idf1',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 95
    },
    'azurtv': {
        'callback': 'live_bridge',
        'label': 'Azur TV',
        'thumb': 'channels/fr/azurtv.png',
        'fanart': 'channels/fr/azurtv_fanart.jpg',
        'module': 'resources.lib.channels.fr.azurtv',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 96
    },
    'biptv': {
        'callback': 'live_bridge',
        'label': 'BIP TV',
        'thumb': 'channels/fr/biptv.png',
        'fanart': 'channels/fr/biptv_fanart.jpg',
        'module': 'resources.lib.channels.fr.biptv',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 97
    },
    'bfmlille': {
        'callback': 'live_bridge',
        'label': 'BFM Lille',
        'thumb': 'channels/fr/bfmlille.png',
        'fanart': 'channels/fr/bfmlille_fanart.jpg',
        'module': 'resources.lib.channels.fr.bfmregion',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 98
    },
    'bfmgrandlittoral': {
        'callback': 'live_bridge',
        'label': 'BFM Littoral',
        'thumb': 'channels/fr/bfmgrandlittoral.png',
        'fanart': 'channels/fr/bfmgrandlittoral_fanart.jpg',
        'module': 'resources.lib.channels.fr.bfmregion',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 99
    },
    'lachainenormande': {
        'callback': 'live_bridge',
        'label': 'La Chaine Normande',
        'thumb': 'channels/fr/lachainenormande.png',
        'fanart': 'channels/fr/lachainenormande_fanart.jpg',
        'module': 'resources.lib.channels.fr.lachainenormande',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 100
    },
    'sportenfrance': {
        'callback': 'live_bridge',
        'label': 'Sport en France',
        'thumb': 'channels/fr/sportenfrance.png',
        'fanart': 'channels/fr/sportenfrance_fanart.jpg',
        'module': 'resources.lib.channels.fr.sportenfrance',
        'm3u_group': 'Satellite/FAI',
        'enabled': True,
        'order': 101
    },
    'provenceazurtv': {
        'callback': 'live_bridge',
        'label': 'Provence Azur TV',
        'thumb': 'channels/fr/provenceazurtv.png',
        'fanart': 'channels/fr/provenceazurtv_fanart.jpg',
        'module': 'resources.lib.channels.fr.azurtv',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 102
    },
    'tebesud': {
        'callback': 'live_bridge',
        'label': 'TébéSud',
        'thumb': 'channels/fr/tebesud.png',
        'fanart': 'channels/fr/tebesud_fanart.jpg',
        'module': 'resources.lib.channels.fr.tebeo',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 103
    },
    'telegrenoble': {
        'callback': 'live_bridge',
        'label': 'TéléGrenoble',
        'thumb': 'channels/fr/telegrenoble.png',
        'fanart': 'channels/fr/telegrenoble_fanart.jpg',
        'module': 'resources.lib.channels.fr.telegrenoble',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 105
    },
    'telenantes': {
        'callback': 'live_bridge',
        'label': 'TéléNantes',
        'thumb': 'channels/fr/telenantes.png',
        'fanart': 'channels/fr/telenantes_fanart.jpg',
        'module': 'resources.lib.channels.fr.telenantes',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 106
    },
    'bfmlyon': {
        'callback': 'live_bridge',
        'label': 'BFM Lyon',
        'thumb': 'channels/fr/bfmlyon.png',
        'fanart': 'channels/fr/bfmlyon_fanart.jpg',
        'module': 'resources.lib.channels.fr.bfmregion',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 107
    },
    'tlc': {
        'callback': 'live_bridge',
        'label': 'TLC',
        'thumb': 'channels/fr/tlc.png',
        'fanart': 'channels/fr/tlc_fanart.jpg',
        'module': 'resources.lib.channels.fr.tlc',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 108
    },
    'tvvendee': {
        'callback': 'live_bridge',
        'label': 'TV Vendée',
        'thumb': 'channels/fr/tvvendee.png',
        'fanart': 'channels/fr/tvvendee_fanart.jpg',
        'module': 'resources.lib.channels.fr.tvvendee',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 109
    },
    'tv7bordeaux': {
        'callback': 'live_bridge',
        'label': 'TV7 Bordeaux',
        'thumb': 'channels/fr/tv7bordeaux.png',
        'fanart': 'channels/fr/tv7bordeaux_fanart.jpg',
        'module': 'resources.lib.channels.fr.tv7bordeaux',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 110
    },
    'tvt': {
        'callback': 'live_bridge',
        'label': 'TVT Val de Loire',
        'thumb': 'channels/fr/tvt.png',
        'fanart': 'channels/fr/tvt_fanart.jpg',
        'module': 'resources.lib.channels.fr.tvt',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 111
    },
    'tvr': {
        'callback': 'live_bridge',
        'label': 'TVR',
        'thumb': 'channels/fr/tvr.png',
        'fanart': 'channels/fr/tvr_fanart.jpg',
        'module': 'resources.lib.channels.fr.tvr',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 112
    },
    'weo': {
        'callback': 'live_bridge',
        'label': 'Wéo TV',
        'thumb': 'channels/fr/weo.png',
        'fanart': 'channels/fr/weo_fanart.jpg',
        'module': 'resources.lib.channels.fr.weo',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 113
    },
    'dicitv': {
        'callback': 'live_bridge',
        'label': 'DiCi TV',
        'thumb': 'channels/fr/dicitv.png',
        'fanart': 'channels/fr/dicitv_fanart.jpg',
        'module': 'resources.lib.channels.fr.dicitv',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 114
    },
    'viamatele': {
        'callback': 'live_bridge',
        'label': 'viàMaTélé',
        'thumb': 'channels/fr/viamatele.png',
        'fanart': 'channels/fr/viamatele_fanart.jpg',
        'module': 'resources.lib.channels.fr.via',
        'm3u_group': 'Région',
        'enabled': True,
        'order': 115
    },
    'franceinter': {
        'callback': 'live_bridge',
        'label': 'France Inter',
        'thumb': 'channels/fr/franceinter.png',
        'fanart': 'channels/fr/franceinter_fanart.jpg',
        'module': 'resources.lib.channels.fr.franceinter',
        'm3u_group': 'Radio',
        'enabled': True,
        'order': 116
    },
    'rtl': {
        'callback': 'live_bridge',
        'label': 'RTL',
        'thumb': 'channels/fr/rtl.png',
        'fanart': 'channels/fr/rtl_fanart.jpg',
        'module': 'resources.lib.channels.fr.rtl',
        'm3u_group': 'Radio',
        'enabled': True,
        'order': 118
    },
    'europe1': {
        'callback': 'live_bridge',
        'label': 'Europe 1',
        'thumb': 'channels/fr/europe1.png',
        'fanart': 'channels/fr/europe1_fanart.jpg',
        'module': 'resources.lib.channels.fr.europe1',
        'm3u_group': 'Radio',
        'enabled': True,
        'order': 120
    }
}
