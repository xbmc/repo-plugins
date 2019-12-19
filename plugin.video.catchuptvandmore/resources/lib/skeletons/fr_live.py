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
from codequick import Script
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
        'thumb': 'channels/fr/tf1.png',
        'fanart': 'channels/fr/tf1_fanart.jpg',
        'module': 'resources.lib.channels.fr.mytf1',
        'xmltv_id': 'C192.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 1
    },
    'tmc': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/tmc.png',
        'fanart': 'channels/fr/tmc_fanart.jpg',
        'module': 'resources.lib.channels.fr.mytf1',
        'xmltv_id': 'C195.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 10
    },
    'tf1-series-films': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/tf1seriesfilms.png',
        'fanart': 'channels/fr/tf1seriesfilms_fanart.jpg',
        'module': 'resources.lib.channels.fr.mytf1',
        'xmltv_id': 'C1404.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 20
    },
    'tfx': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/tfx.png',
        'fanart': 'channels/fr/tfx_fanart.jpg',
        'module': 'resources.lib.channels.fr.mytf1',
        'xmltv_id': 'C446.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 11
    },
    'rtl2': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/rtl2.png',
        'fanart': 'channels/fr/rtl2_fanart.jpg',
        'module': 'resources.lib.channels.fr.6play',
        'm3u_group': 'Radio'
    },
    'fun_radio': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/funradio.png',
        'fanart': 'channels/fr/funradio_fanart.jpg',
        'module': 'resources.lib.channels.fr.6play',
        'm3u_group': 'Radio'
    },
    'viaoccitanie': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/viaoccitanie.png',
        'fanart': 'channels/fr/viaoccitanie_fanart.jpg',
        'module': 'resources.lib.channels.fr.via',
        'm3u_group': 'Région'
    },
    'lci': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/lci.png',
        'fanart': 'channels/fr/lci_fanart.jpg',
        'module': 'resources.lib.channels.fr.lci',
        'xmltv_id': 'C112.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 26
    },
    'antennereunion': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/antennereunion.png',
        'fanart': 'channels/fr/antennereunion_fanart.jpg',
        'module': 'resources.lib.channels.fr.antennereunion',
        'm3u_group': 'Région'
    },
    'gulli': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/gulli.png',
        'fanart': 'channels/fr/gulli_fanart.jpg',
        'module': 'resources.lib.channels.fr.gulli',
        'xmltv_id': 'C482.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 18
    },
    'canalplus': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/canalplus.png',
        'fanart': 'channels/fr/canalplus_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal',
        'xmltv_id': 'C34.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 4
    },
    'c8': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/c8.png',
        'fanart': 'channels/fr/c8_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal',
        'xmltv_id': 'C445.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 8
    },
    'cstar': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/cstar.png',
        'fanart': 'channels/fr/cstar_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal',
        'xmltv_id': 'C458.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 17
    },
    'france-2': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/france2.png',
        'fanart': 'channels/fr/france2_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetv',
        'xmltv_id': 'C4.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 2
    },
    'france-3': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/france3.png',
        'fanart': 'channels/fr/france3_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetv',
        'xmltv_id': 'C80.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 3
    },
    'france-4': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/france4.png',
        'fanart': 'channels/fr/france4_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetv',
        'xmltv_id': 'C78.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 14
    },
    'france-5': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/france5.png',
        'fanart': 'channels/fr/france5_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetv',
        'xmltv_id': 'C47.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 5
    },
    'france-o': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/franceo.png',
        'fanart': 'channels/fr/franceo_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetv',
        'xmltv_id': 'C160.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 19
    },
    'lequipe': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/lequipe.png',
        'fanart': 'channels/fr/lequipe_fanart.jpg',
        'module': 'resources.lib.channels.fr.lequipe',
        'xmltv_id': 'C1401.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 21
    },
    'cnews': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/cnews.png',
        'fanart': 'channels/fr/cnews_fanart.jpg',
        'module': 'resources.lib.channels.fr.cnews',
        'xmltv_id': 'C226.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 16
    },
    'rmcdecouverte': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/rmcdecouverte.png',
        'fanart': 'channels/fr/rmcdecouverte_fanart.jpg',
        'module': 'resources.lib.channels.fr.rmcdecouverte',
        'xmltv_id': 'C1400.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 24
    },
    'rmcstory': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/rmcstory.png',
        'fanart': 'channels/fr/rmcstory_fanart.jpg',
        'module': 'resources.lib.channels.fr.rmcstory',
        'xmltv_id': 'C1402.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 23
    },
    'canal10': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/canal10.png',
        'fanart': 'channels/fr/canal10_fanart.jpg',
        'module': 'resources.lib.channels.fr.canal10',
        'm3u_group': 'Région'
    },
    'nrj12': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/nrj12.png',
        'fanart': 'channels/fr/nrj12_fanart.jpg',
        'module': 'resources.lib.channels.fr.nrj',
        'xmltv_id': 'C444.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 12
    },
    'cherie25': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/cherie25.png',
        'fanart': 'channels/fr/cherie25_fanart.jpg',
        'module': 'resources.lib.channels.fr.nrj',
        'xmltv_id': 'C1399.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 25
    },
    'bfmparis': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/bfmparis.png',
        'fanart': 'channels/fr/bfmparis_fanart.jpg',
        'module': 'resources.lib.channels.fr.bfmparis',
        'm3u_group': 'Région'
    },
    'bfmtv': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/bfmtv.png',
        'fanart': 'channels/fr/bfmtv_fanart.jpg',
        'module': 'resources.lib.channels.fr.bfmtv',
        'xmltv_id': 'C481.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 15
    },
    'bfmbusiness': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/bfmbusiness.png',
        'fanart': 'channels/fr/bfmbusiness_fanart.jpg',
        'module': 'resources.lib.channels.fr.bfmtv',
        'xmltv_id': 'C1073.api.telerama.fr',
        'm3u_group': 'Satellite/FAI'
    },
    'gong': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/gong.png',
        'fanart': 'channels/fr/gong_fanart.jpg',
        'module': 'resources.lib.channels.fr.gong',
        'm3u_group': 'Satellite/FAI'
    },
    'la_1ere': {
        'callback':
        'live_bridge',
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
        ]
    },
    'kto': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/kto.png',
        'fanart': 'channels/fr/kto_fanart.jpg',
        'module': 'resources.lib.channels.fr.kto',
        'm3u_group': 'Satellite/FAI'
    },
    'ouatchtv': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/ouatchtv.png',
        'fanart': 'channels/fr/ouatchtv_fanart.jpg',
        'module': 'resources.lib.channels.fr.ouatchtv',
        'm3u_group': 'Satellite/FAI'
    },
    'publicsenat': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/publicsenat.png',
        'fanart': 'channels/fr/publicsenat_fanart.jpg',
        'module': 'resources.lib.channels.fr.publicsenat',
        'xmltv_id': 'C234.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 13
    },
    'lcp': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/lcp.png',
        'fanart': 'channels/fr/lcp_fanart.jpg',
        'module': 'resources.lib.channels.fr.lcp',
        'xmltv_id': 'C234.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 13
    },
    'francetvsport': {
        'callback': 'multi_live_bridge',
        'thumb': 'channels/fr/francetvsport.png',
        'fanart': 'channels/fr/francetvsport_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetvsport',
        'm3u_group': 'Satellite/FAI'
    },
    'franceinfo': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/franceinfo.png',
        'fanart': 'channels/fr/franceinfo_fanart.jpg',
        'module': 'resources.lib.channels.fr.franceinfo',
        'xmltv_id': 'C2111.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 27
    },
    'france3regions': {
        'callback':
        'live_bridge',
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
        ]
    },
    'viaatv': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/viaatv.png',
        'fanart': 'channels/fr/viaatv_fanart.jpg',
        'module': 'resources.lib.channels.fr.via',
        'm3u_group': 'Région'
    },
    'viagrandparis': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/viagrandparis.png',
        'fanart': 'channels/fr/viagrandparis_fanart.jpg',
        'module': 'resources.lib.channels.fr.via',
        'm3u_group': 'Région'
    },
    'tebeo': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/tebeo.png',
        'fanart': 'channels/fr/tebeo_fanart.jpg',
        'module': 'resources.lib.channels.fr.tebeo',
        'm3u_group': 'Région'
    },
    'mb': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/mb.png',
        'fanart': 'channels/fr/mb_fanart.jpg',
        'module': 'resources.lib.channels.fr.6play',
        'xmltv_id': 'C184.api.telerama.fr',
        'm3u_group': 'Satellite/FAI'
    },
    'm6': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/m6.png',
        'fanart': 'channels/fr/m6_fanart.jpg',
        'module': 'resources.lib.channels.fr.6play',
        'xmltv_id': 'C118.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 6
    },
    'w9': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/w9.png',
        'fanart': 'channels/fr/w9_fanart.jpg',
        'module': 'resources.lib.channels.fr.6play',
        'xmltv_id': 'C119.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 9
    },
    '6ter': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/6ter.png',
        'fanart': 'channels/fr/6ter_fanart.jpg',
        'module': 'resources.lib.channels.fr.6play',
        'xmltv_id': 'C1403.api.telerama.fr',
        'm3u_group': 'TNT',
        'm3u_order': 22
    },
    'vialmtv': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/vialmtv.png',
        'fanart': 'channels/fr/vialmtv_fanart.jpg',
        'module': 'resources.lib.channels.fr.via',
        'm3u_group': 'Région'
    },
    'viamirabelle': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/viamirabelle.png',
        'fanart': 'channels/fr/viamirabelle_fanart.jpg',
        'module': 'resources.lib.channels.fr.via',
        'm3u_group': 'Région'
    },
    'viavosges': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/viavosges.png',
        'fanart': 'channels/fr/viavosges_fanart.jpg',
        'module': 'resources.lib.channels.fr.via',
        'm3u_group': 'Région'
    },
    'tl7': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/tl7.png',
        'fanart': 'channels/fr/tl7_fanart.jpg',
        'module': 'resources.lib.channels.fr.tl7',
        'm3u_group': 'Région'
    },
    'luckyjack': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/luckyjack.png',
        'fanart': 'channels/fr/luckyjack_fanart.jpg',
        'module': 'resources.lib.channels.fr.abweb',
        'm3u_group': 'Satellite/FAI'
    },
    'mblivetv': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/mblivetv.png',
        'fanart': 'channels/fr/mblivetv_fanart.jpg',
        'module': 'resources.lib.channels.fr.mblivetv',
        'm3u_group': 'Satellite/FAI'
    },
    'tv8montblanc': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/tv8montblanc.png',
        'fanart': 'channels/fr/tv8montblanc_fanart.jpg',
        'module': 'resources.lib.channels.fr.tv8montblanc',
        'm3u_group': 'Région'
    },
    'alsace20': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/alsace20.png',
        'fanart': 'channels/fr/alsace20_fanart.jpg',
        'module': 'resources.lib.channels.fr.alsace20',
        'm3u_group': 'Région'
    },
    'tvpifr': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/tvpifr.png',
        'fanart': 'channels/fr/tvpifr_fanart.jpg',
        'module': 'resources.lib.channels.fr.tvpifr',
        'm3u_group': 'Région'
    },
    'idf1': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/idf1.png',
        'fanart': 'channels/fr/idf1_fanart.jpg',
        'module': 'resources.lib.channels.fr.idf1',
        'm3u_group': 'Région'
    },
    'azurtv': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/azurtv.png',
        'fanart': 'channels/fr/azurtv_fanart.jpg',
        'module': 'resources.lib.channels.fr.azurtv',
        'm3u_group': 'Région'
    },
    'biptv': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/biptv.png',
        'fanart': 'channels/fr/biptv_fanart.jpg',
        'module': 'resources.lib.channels.fr.biptv',
        'm3u_group': 'Région'
    },
    'grandlilletv': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/grandlilletv.png',
        'fanart': 'channels/fr/grandlilletv_fanart.jpg',
        'module': 'resources.lib.channels.fr.grandlilletv',
        'm3u_group': 'Région'
    },
    'grandlitorraltv': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/grandlitorraltv.png',
        'fanart': 'channels/fr/grandlitorraltv_fanart.jpg',
        'module': 'resources.lib.channels.fr.grandlitorraltv',
        'm3u_group': 'Région'
    },
    'lachainenormande': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/lachainenormande.png',
        'fanart': 'channels/fr/lachainenormande_fanart.jpg',
        'module': 'resources.lib.channels.fr.lachainenormande',
        'm3u_group': 'Région'
    },
    'sportenfrance': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/sportenfrance.png',
        'fanart': 'channels/fr/sportenfrance_fanart.jpg',
        'module': 'resources.lib.channels.fr.sportenfrance',
        'm3u_group': 'Satellite/FAI'
    },
    'provenceazurtv': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/provenceazurtv.png',
        'fanart': 'channels/fr/provenceazurtv_fanart.jpg',
        'module': 'resources.lib.channels.fr.azurtv',
        'm3u_group': 'Région'
    },
    'tebesud': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/tebesud.png',
        'fanart': 'channels/fr/tebesud_fanart.jpg',
        'module': 'resources.lib.channels.fr.tebeo',
        'm3u_group': 'Région'
    },
    'viamatele': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/viamatele.png',
        'fanart': 'channels/fr/viamatele_fanart.jpg',
        'module': 'resources.lib.channels.fr.via',
        'm3u_group': 'Région'
    },
    'telegrenoble': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/telegrenoble.png',
        'fanart': 'channels/fr/telegrenoble_fanart.jpg',
        'module': 'resources.lib.channels.fr.telegrenoble',
        'm3u_group': 'Région'
    },
    'telenantes': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/telenantes.png',
        'fanart': 'channels/fr/telenantes_fanart.jpg',
        'module': 'resources.lib.channels.fr.telenantes',
        'm3u_group': 'Région'
    },
    'bfmlyon': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/bfmlyon.png',
        'fanart': 'channels/fr/bfmlyon_fanart.jpg',
        'module': 'resources.lib.channels.fr.bfmlyon',
        'm3u_group': 'Région'
    },
    'tlc': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/tlc.png',
        'fanart': 'channels/fr/tlc_fanart.jpg',
        'module': 'resources.lib.channels.fr.tlc',
        'm3u_group': 'Région'
    },
    'tvvendee': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/tvvendee.png',
        'fanart': 'channels/fr/tvvendee_fanart.jpg',
        'module': 'resources.lib.channels.fr.tvvendee',
        'm3u_group': 'Région'
    },
    'tv7bordeaux': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/tv7bordeaux.png',
        'fanart': 'channels/fr/tv7bordeaux_fanart.jpg',
        'module': 'resources.lib.channels.fr.tv7bordeaux',
        'm3u_group': 'Région'
    },
    'tvt': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/tvt.png',
        'fanart': 'channels/fr/tvt_fanart.jpg',
        'module': 'resources.lib.channels.fr.tvt',
        'm3u_group': 'Région'
    },
    'tvr': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/tvr.png',
        'fanart': 'channels/fr/tvr_fanart.jpg',
        'module': 'resources.lib.channels.fr.tvr',
        'm3u_group': 'Région'
    },
    'weo': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/weo.png',
        'fanart': 'channels/fr/weo_fanart.jpg',
        'module': 'resources.lib.channels.fr.weo',
        'm3u_group': 'Région'
    },
    'dicitv': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/dicitv.png',
        'fanart': 'channels/fr/dicitv_fanart.jpg',
        'module': 'resources.lib.channels.fr.dicitv',
        'm3u_group': 'Région'
    },
    'franceinter': {
        'callback': 'live_bridge',
        'thumb': 'channels/fr/franceinter.png',
        'fanart': 'channels/fr/franceinter_fanart.jpg',
        'module': 'resources.lib.channels.fr.franceinter',
        'm3u_group': 'Radio'
    }
}
