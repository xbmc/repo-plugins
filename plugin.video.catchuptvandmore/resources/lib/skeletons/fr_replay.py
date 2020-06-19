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
        'callback': 'replay_bridge',
        'label': 'TF1',
        'thumb': 'channels/fr/tf1.png',
        'fanart': 'channels/fr/tf1_fanart.jpg',
        'module': 'resources.lib.channels.fr.mytf1',
        'enabled': True,
        'order': 1
    },
    'france-2': {
        'callback': 'replay_bridge',
        'label': 'France 2',
        'thumb': 'channels/fr/france2.png',
        'fanart': 'channels/fr/france2_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetv',
        'enabled': True,
        'order': 2
    },
    'france-3': {
        'callback': 'replay_bridge',
        'label': 'France 3',
        'thumb': 'channels/fr/france3.png',
        'fanart': 'channels/fr/france3_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetv',
        'enabled': True,
        'order': 3
    },
    'canalplus': {
        'callback': 'replay_bridge',
        'label': 'Canal +',
        'thumb': 'channels/fr/canalplus.png',
        'fanart': 'channels/fr/canalplus_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal',
        'enabled': True,
        'order': 4
    },
    'france-5': {
        'callback': 'replay_bridge',
        'label': 'France 5',
        'thumb': 'channels/fr/france5.png',
        'fanart': 'channels/fr/france5_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetv',
        'enabled': True,
        'order': 5
    },
    'm6': {
        'callback': 'replay_bridge',
        'label': 'M6',
        'thumb': 'channels/fr/m6.png',
        'fanart': 'channels/fr/m6_fanart.jpg',
        'module': 'resources.lib.channels.fr.6play',
        'enabled': True,
        'order': 6
    },
    'c8': {
        'callback': 'replay_bridge',
        'label': 'C8',
        'thumb': 'channels/fr/c8.png',
        'fanart': 'channels/fr/c8_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal',
        'enabled': True,
        'order': 7
    },
    'w9': {
        'callback': 'replay_bridge',
        'label': 'W9',
        'thumb': 'channels/fr/w9.png',
        'fanart': 'channels/fr/w9_fanart.jpg',
        'module': 'resources.lib.channels.fr.6play',
        'enabled': True,
        'order': 8
    },
    'tmc': {
        'callback': 'replay_bridge',
        'label': 'TMC',
        'thumb': 'channels/fr/tmc.png',
        'fanart': 'channels/fr/tmc_fanart.jpg',
        'module': 'resources.lib.channels.fr.mytf1',
        'enabled': True,
        'order': 9
    },
    'tfx': {
        'callback': 'replay_bridge',
        'label': 'TFX',
        'thumb': 'channels/fr/tfx.png',
        'fanart': 'channels/fr/tfx_fanart.jpg',
        'module': 'resources.lib.channels.fr.mytf1',
        'enabled': True,
        'order': 10
    },
    'nrj12': {
        'callback': 'replay_bridge',
        'label': 'NRJ 12',
        'thumb': 'channels/fr/nrj12.png',
        'fanart': 'channels/fr/nrj12_fanart.jpg',
        'module': 'resources.lib.channels.fr.nrj',
        'enabled': True,
        'order': 11
    },
    'france-4': {
        'callback': 'replay_bridge',
        'label': 'France 4',
        'thumb': 'channels/fr/france4.png',
        'fanart': 'channels/fr/france4_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetv',
        'enabled': True,
        'order': 12
    },
    'bfmtv': {
        'callback': 'replay_bridge',
        'label': 'BFM TV',
        'thumb': 'channels/fr/bfmtv.png',
        'fanart': 'channels/fr/bfmtv_fanart.jpg',
        'module': 'resources.lib.channels.fr.bfmtv',
        'enabled': True,
        'order': 13
    },
    'cnews': {
        'callback': 'replay_bridge',
        'label': 'CNews',
        'thumb': 'channels/fr/cnews.png',
        'fanart': 'channels/fr/cnews_fanart.jpg',
        'module': 'resources.lib.channels.fr.cnews',
        'enabled': True,
        'order': 14
    },
    'cstar': {
        'callback': 'replay_bridge',
        'label': 'CStar',
        'thumb': 'channels/fr/cstar.png',
        'fanart': 'channels/fr/cstar_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal',
        'enabled': True,
        'order': 15
    },
    'gulli': {
        'callback': 'replay_bridge',
        'label': 'Gulli',
        'thumb': 'channels/fr/gulli.png',
        'fanart': 'channels/fr/gulli_fanart.jpg',
        'module': 'resources.lib.channels.fr.gulli',
        'enabled': True,
        'order': 16
    },
    'france-o': {
        'callback': 'replay_bridge',
        'label': 'France Ô',
        'thumb': 'channels/fr/franceo.png',
        'fanart': 'channels/fr/franceo_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetv',
        'enabled': True,
        'order': 17
    },
    'tf1-series-films': {
        'callback': 'replay_bridge',
        'label': 'TF1 Séries Films',
        'thumb': 'channels/fr/tf1seriesfilms.png',
        'fanart': 'channels/fr/tf1seriesfilms_fanart.jpg',
        'module': 'resources.lib.channels.fr.mytf1',
        'enabled': True,
        'order': 18
    },
    'lequipe': {
        'callback': 'replay_bridge',
        'label': 'L\'Équipe',
        'thumb': 'channels/fr/lequipe.png',
        'fanart': 'channels/fr/lequipe_fanart.jpg',
        'module': 'resources.lib.channels.fr.lequipe',
        'enabled': True,
        'order': 19
    },
    '6ter': {
        'callback': 'replay_bridge',
        'label': '6ter',
        'thumb': 'channels/fr/6ter.png',
        'fanart': 'channels/fr/6ter_fanart.jpg',
        'module': 'resources.lib.channels.fr.6play',
        'enabled': True,
        'order': 20
    },
    'rmcstory': {
        'callback': 'replay_bridge',
        'label': 'RMC Story',
        'thumb': 'channels/fr/rmcstory.png',
        'fanart': 'channels/fr/rmcstory_fanart.jpg',
        'module': 'resources.lib.channels.fr.rmc',
        'enabled': True,
        'order': 21
    },
    'cherie25': {
        'callback': 'replay_bridge',
        'label': 'Chérie 25',
        'thumb': 'channels/fr/cherie25.png',
        'fanart': 'channels/fr/cherie25_fanart.jpg',
        'module': 'resources.lib.channels.fr.nrj',
        'enabled': True,
        'order': 22
    },
    'la_1ere': {
        'callback': 'replay_bridge',
        'label': 'La 1ère (' + utils.ensure_unicode(Script.setting['la_1ere.language']) + ')',
        'thumb': 'channels/fr/la1ere.png',
        'fanart': 'channels/fr/la1ere_fanart.jpg',
        'module': 'resources.lib.channels.fr.la_1ere',
        'enabled': True,
        'order': 23
    },
    'franceinfo': {
        'callback': 'replay_bridge',
        'label': 'France Info',
        'thumb': 'channels/fr/franceinfo.png',
        'fanart': 'channels/fr/franceinfo_fanart.jpg',
        'module': 'resources.lib.channels.fr.franceinfo',
        'enabled': True,
        'order': 24
    },
    'bfmbusiness': {
        'callback': 'replay_bridge',
        'label': 'BFM Business',
        'thumb': 'channels/fr/bfmbusiness.png',
        'fanart': 'channels/fr/bfmbusiness_fanart.jpg',
        'module': 'resources.lib.channels.fr.bfmtv',
        'enabled': True,
        'order': 25
    },
    'rmc': {
        'callback': 'replay_bridge',
        'label': 'RMC',
        'thumb': 'channels/fr/rmc.png',
        'fanart': 'channels/fr/rmc_fanart.jpg',
        'module': 'resources.lib.channels.fr.bfmtv',
        'enabled': True,
        'order': 26
    },
    '01net': {
        'callback': 'replay_bridge',
        'label': '01Net TV',
        'thumb': 'channels/fr/01net.png',
        'fanart': 'channels/fr/01net_fanart.jpg',
        'module': 'resources.lib.channels.fr.bfmtv',
        'enabled': True,
        'order': 27
    },
    'lci': {
        'callback': 'replay_bridge',
        'label': 'LCI',
        'thumb': 'channels/fr/lci.png',
        'fanart': 'channels/fr/lci_fanart.jpg',
        'module': 'resources.lib.channels.fr.lci',
        'enabled': True,
        'order': 30
    },
    'lcp': {
        'callback': 'replay_bridge',
        'label': 'LCP Assemblée Nationale',
        'thumb': 'channels/fr/lcp.png',
        'fanart': 'channels/fr/lcp_fanart.jpg',
        'module': 'resources.lib.channels.fr.lcp',
        'enabled': True,
        'order': 31
    },
    'rmcdecouverte': {
        'callback': 'replay_bridge',
        'label': 'RMC Découverte',
        'thumb': 'channels/fr/rmcdecouverte.png',
        'fanart': 'channels/fr/rmcdecouverte_fanart.jpg',
        'module': 'resources.lib.channels.fr.rmc',
        'enabled': True,
        'order': 32
    },
    'publicsenat': {
        'callback': 'replay_bridge',
        'label': 'Public Sénat',
        'thumb': 'channels/fr/publicsenat.png',
        'fanart': 'channels/fr/publicsenat_fanart.jpg',
        'module': 'resources.lib.channels.fr.publicsenat',
        'enabled': True,
        'order': 39
    },
    'france3regions': {
        'callback': 'replay_bridge',
        'label': 'France 3 Régions (' + utils.ensure_unicode(Script.setting['france3regions.language']) + ')',
        'thumb': 'channels/fr/france3regions.png',
        'fanart': 'channels/fr/france3regions_fanart.jpg',
        'module': 'resources.lib.channels.fr.france3regions',
        'enabled': True,
        'order': 40
    },
    'francetvsport': {
        'callback': 'replay_bridge',
        'label': 'France TV Sport (francetv)',
        'thumb': 'channels/fr/francetvsport.png',
        'fanart': 'channels/fr/francetvsport_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetvsport',
        'enabled': True,
        'order': 41
    },
    'histoire': {
        'callback': 'replay_bridge',
        'label': 'Histoire',
        'thumb': 'channels/fr/histoire.png',
        'fanart': 'channels/fr/histoire_fanart.jpg',
        'module': 'resources.lib.channels.fr.tf1thematiques',
        'enabled': True,
        'order': 42
    },
    'tvbreizh': {
        'callback': 'replay_bridge',
        'label': 'TV Breizh',
        'thumb': 'channels/fr/tvbreizh.png',
        'fanart': 'channels/fr/tvbreizh_fanart.jpg',
        'module': 'resources.lib.channels.fr.tf1thematiques',
        'enabled': True,
        'order': 43
    },
    'ushuaiatv': {
        'callback': 'replay_bridge',
        'label': 'Ushuaïa TV',
        'thumb': 'channels/fr/ushuaiatv.png',
        'fanart': 'channels/fr/ushuaiatv_fanart.jpg',
        'module': 'resources.lib.channels.fr.tf1thematiques',
        'enabled': True,
        'order': 44
    },
    'seasons': {
        'callback': 'replay_bridge',
        'label': 'Seasons',
        'thumb': 'channels/fr/seasons.png',
        'fanart': 'channels/fr/seasons_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal',
        'enabled': True,
        'order': 47
    },
    'comedie': {
        'callback': 'replay_bridge',
        'label': 'Comédie +',
        'thumb': 'channels/fr/comedie.png',
        'fanart': 'channels/fr/comedie_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal',
        'enabled': True,
        'order': 48
    },
    'les-chaines-planete': {
        'callback': 'replay_bridge',
        'label': 'Les chaînes planètes +',
        'thumb': 'channels/fr/leschainesplanete.png',
        'fanart': 'channels/fr/leschainesplanete_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal',
        'enabled': True,
        'order': 49
    },
    'golfplus': {
        'callback': 'replay_bridge',
        'label': 'Golf +',
        'thumb': 'channels/fr/golfplus.png',
        'fanart': 'channels/fr/golfplus_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal',
        'enabled': True,
        'order': 50
    },
    'cineplus': {
        'callback': 'replay_bridge',
        'label': 'Ciné +',
        'thumb': 'channels/fr/cineplus.png',
        'fanart': 'channels/fr/cineplus_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal',
        'enabled': True,
        'order': 51
    },
    'infosportplus': {
        'callback': 'replay_bridge',
        'label': 'INFOSPORT+',
        'thumb': 'channels/fr/infosportplus.png',
        'fanart': 'channels/fr/infosportplus_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal',
        'enabled': True,
        'order': 52
    },
    'gameone': {
        'callback': 'replay_bridge',
        'label': 'Game One',
        'thumb': 'channels/fr/gameone.png',
        'fanart': 'channels/fr/gameone_fanart.jpg',
        'module': 'resources.lib.channels.fr.gameone',
        'enabled': True,
        'order': 53
    },
    'lumni': {
        'callback': 'replay_bridge',
        'label': 'Lumni (francetv)',
        'thumb': 'channels/fr/lumni.png',
        'fanart': 'channels/fr/lumni_fanart.jpg',
        'module': 'resources.lib.channels.fr.lumni',
        'enabled': True,
        'order': 54
    },
    'gong': {
        'callback': 'replay_bridge',
        'label': 'Gong',
        'thumb': 'channels/fr/gong.png',
        'fanart': 'channels/fr/gong_fanart.jpg',
        'module': 'resources.lib.channels.fr.gong',
        'enabled': True,
        'order': 55
    },
    'bfmparis': {
        'callback': 'replay_bridge',
        'label': 'BFM Paris',
        'thumb': 'channels/fr/bfmparis.png',
        'fanart': 'channels/fr/bfmparis_fanart.jpg',
        'module': 'resources.lib.channels.fr.bfmregion',
        'enabled': True,
        'order': 56
    },
    'fun_radio': {
        'callback': 'replay_bridge',
        'label': 'Fun Radio',
        'thumb': 'channels/fr/funradio.png',
        'fanart': 'channels/fr/funradio_fanart.jpg',
        'module': 'resources.lib.channels.fr.6play',
        'enabled': True,
        'order': 58
    },
    'slash': {
        'callback': 'replay_bridge',
        'label': 'France tv slash',
        'thumb': 'channels/fr/slash.png',
        'fanart': 'channels/fr/slash_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetv',
        'enabled': True,
        'order': 60
    },
    'polar-plus': {
        'callback': 'replay_bridge',
        'label': 'Polar+',
        'thumb': 'channels/fr/polarplus.png',
        'fanart': 'channels/fr/polarplus_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal',
        'enabled': True,
        'order': 61
    },
    'kto': {
        'callback': 'replay_bridge',
        'label': 'KTO',
        'thumb': 'channels/fr/kto.png',
        'fanart': 'channels/fr/kto_fanart.jpg',
        'module': 'resources.lib.channels.fr.kto',
        'enabled': True,
        'order': 64
    },
    'antennereunion': {
        'callback': 'replay_bridge',
        'label': 'Antenne Réunion',
        'thumb': 'channels/fr/antennereunion.png',
        'fanart': 'channels/fr/antennereunion_fanart.jpg',
        'module': 'resources.lib.channels.fr.antennereunion',
        'enabled': True,
        'order': 65
    },
    'ouatchtv': {
        'callback': 'replay_bridge',
        'label': 'Ouatch TV',
        'thumb': 'channels/fr/ouatchtv.png',
        'fanart': 'channels/fr/ouatchtv_fanart.jpg',
        'module': 'resources.lib.channels.fr.ouatchtv',
        'enabled': True,
        'order': 67
    },
    'rtl2': {
        'callback': 'replay_bridge',
        'label': 'RTL 2',
        'thumb': 'channels/fr/rtl2.png',
        'fanart': 'channels/fr/rtl2_fanart.jpg',
        'module': 'resources.lib.channels.fr.6play',
        'enabled': True,
        'order': 69
    },
    'lachainemeteo': {
        'callback': 'replay_bridge',
        'label': 'La Chaîne Météo',
        'thumb': 'channels/fr/lachainemeteo.png',
        'fanart': 'channels/fr/lachainemeteo_fanart.jpg',
        'module': 'resources.lib.channels.fr.lachainemeteo',
        'enabled': True,
        'order': 70
    },
    'j_one': {
        'callback': 'replay_bridge',
        'label': 'J-One',
        'thumb': 'channels/fr/jone.png',
        'fanart': 'channels/fr/jone_fanart.jpg',
        'module': 'resources.lib.channels.fr.j_one',
        'enabled': True,
        'order': 71
    },
    'via93': {
        'callback': 'replay_bridge',
        'label': 'vià93',
        'thumb': 'channels/fr/via93.png',
        'fanart': 'channels/fr/via93_fanart.jpg',
        'module': 'resources.lib.channels.fr.via',
        'enabled': True,
        'order': 74
    },
    'jack': {
        'callback': 'replay_bridge',
        'label': 'Jack (mycanal)',
        'thumb': 'channels/fr/jack.png',
        'fanart': 'channels/fr/jack_fanart.jpg',
        'module': 'resources.lib.channels.fr.jack',
        'enabled': True,
        'order': 75
    },
    'caledonia': {
        'callback': 'replay_bridge',
        'label': 'Caledonia',
        'thumb': 'channels/fr/caledonia.png',
        'fanart': 'channels/fr/caledonia_fanart.jpg',
        'module': 'resources.lib.channels.fr.caledonia',
        'enabled': True,
        'order': 76
    },
    'tebeo': {
        'callback': 'replay_bridge',
        'label': 'Tébéo',
        'thumb': 'channels/fr/tebeo.png',
        'fanart': 'channels/fr/tebeo_fanart.jpg',
        'module': 'resources.lib.channels.fr.tebeo',
        'enabled': True,
        'order': 77
    },
    'tl7': {
        'callback': 'replay_bridge',
        'label': 'Télévision Loire 7',
        'thumb': 'channels/fr/tl7.png',
        'fanart': 'channels/fr/tl7_fanart.jpg',
        'module': 'resources.lib.channels.fr.tl7',
        'enabled': True,
        'order': 82
    },
    'mblivetv': {
        'callback': 'replay_bridge',
        'label': 'Mont Blanc Live TV',
        'thumb': 'channels/fr/mblivetv.png',
        'fanart': 'channels/fr/mblivetv_fanart.jpg',
        'module': 'resources.lib.channels.fr.mblivetv',
        'enabled': True,
        'order': 84
    },
    'tv8montblanc': {
        'callback': 'replay_bridge',
        'label': '8 Mont-Blanc',
        'thumb': 'channels/fr/tv8montblanc.png',
        'fanart': 'channels/fr/tv8montblanc_fanart.jpg',
        'module': 'resources.lib.channels.fr.tv8montblanc',
        'enabled': True,
        'order': 85
    },
    'luxetv': {
        'callback': 'replay_bridge',
        'label': 'Luxe.TV',
        'thumb': 'channels/fr/luxetv.png',
        'fanart': 'channels/fr/luxetv_fanart.jpg',
        'module': 'resources.lib.channels.fr.luxetv',
        'enabled': True,
        'order': 86
    },
    'alsace20': {
        'callback': 'replay_bridge',
        'label': 'Alsace 20',
        'thumb': 'channels/fr/alsace20.png',
        'fanart': 'channels/fr/alsace20_fanart.jpg',
        'module': 'resources.lib.channels.fr.alsace20',
        'enabled': True,
        'order': 87
    },
    'francetvspectaclesetculture': {
        'callback': 'replay_bridge',
        'label': 'Spectacles et Culture (francetv)',
        'thumb': 'channels/fr/francetvspectaclesetculture.png',
        'fanart': 'channels/fr/francetvspectaclesetculture_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetvspectaclesetculture',
        'enabled': True,
        'order': 88
    },
    'tvpifr': {
        'callback': 'replay_bridge',
        'label': 'TVPI télévision d\'ici',
        'thumb': 'channels/fr/tvpifr.png',
        'fanart': 'channels/fr/tvpifr_fanart.jpg',
        'module': 'resources.lib.channels.fr.tvpifr',
        'enabled': True,
        'order': 89
    },
    'cliquetv': {
        'callback': 'replay_bridge',
        'label': 'Clique TV',
        'thumb': 'channels/fr/cliquetv.png',
        'fanart': 'channels/fr/cliquetv_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal',
        'enabled': True,
        'order': 90
    },
    'piwiplus': {
        'callback': 'replay_bridge',
        'label': 'Piwi +',
        'thumb': 'channels/fr/piwiplus.png',
        'fanart': 'channels/fr/piwiplus_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal',
        'enabled': True,
        'order': 91
    },
    'teletoonplus': {
        'callback': 'replay_bridge',
        'label': 'TéléToon +',
        'thumb': 'channels/fr/teletoonplus.png',
        'fanart': 'channels/fr/teletoonplus_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal',
        'enabled': True,
        'order': 92
    },
    'paramountchannel_fr': {
        'callback': 'replay_bridge',
        'label': 'Paramount Channel (FR)',
        'thumb': 'channels/fr/paramountchannel_fr.png',
        'fanart': 'channels/fr/paramountchannel_fr_fanart.jpg',
        'module': 'resources.lib.channels.fr.paramountchannel_fr',
        'enabled': True,
        'order': 93
    },
    'mtv_fr': {
        'callback': 'replay_bridge',
        'label': 'MTV (FR)',
        'thumb': 'channels/fr/mtv_fr.png',
        'fanart': 'channels/fr/mtv_fr_fanart.jpg',
        'module': 'resources.lib.channels.fr.mtv_fr',
        'enabled': True,
        'order': 94
    },
    'bfmlille': {
        'callback': 'replay_bridge',
        'label': 'BFM Lille',
        'thumb': 'channels/fr/bfmlille.png',
        'fanart': 'channels/fr/bfmlille_fanart.jpg',
        'module': 'resources.lib.channels.fr.bfmregion',
        'enabled': True,
        'order': 98
    },
    'bfmgrandlittoral': {
        'callback': 'replay_bridge',
        'label': 'BFM Littoral',
        'thumb': 'channels/fr/bfmgrandlittoral.png',
        'fanart': 'channels/fr/bfmgrandlittoral_fanart.jpg',
        'module': 'resources.lib.channels.fr.bfmregion',
        'enabled': True,
        'order': 99
    },
    'tebesud': {
        'callback': 'replay_bridge',
        'label': 'TébéSud',
        'thumb': 'channels/fr/tebesud.png',
        'fanart': 'channels/fr/tebesud_fanart.jpg',
        'module': 'resources.lib.channels.fr.tebeo',
        'enabled': True,
        'order': 103
    },
    'telegrenoble': {
        'callback': 'replay_bridge',
        'label': 'TéléGrenoble',
        'thumb': 'channels/fr/telegrenoble.png',
        'fanart': 'channels/fr/telegrenoble_fanart.jpg',
        'module': 'resources.lib.channels.fr.telegrenoble',
        'enabled': True,
        'order': 105
    },
    'bfmlyon': {
        'callback': 'replay_bridge',
        'label': 'BFM Lyon',
        'thumb': 'channels/fr/bfmlyon.png',
        'fanart': 'channels/fr/bfmlyon_fanart.jpg',
        'module': 'resources.lib.channels.fr.bfmregion',
        'enabled': True,
        'order': 107
    },
    'enfants': {
        'callback': 'replay_bridge',
        'label': 'Okoo (France TV)',
        'thumb': 'channels/fr/okoo.png',
        'fanart': 'channels/fr/okoo_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetv',
        'enabled': True,
        'order': 117
    },
    'courses': {
        'callback': 'replay_bridge',
        'label': 'M6 Courses (6play)',
        'thumb': 'channels/fr/m6courses.png',
        'fanart': 'channels/fr/m6courses_fanart.jpg',
        'module': 'resources.lib.channels.fr.6play',
        'enabled': True,
        'order': 119
    },
    '100foot': {
        'callback': 'replay_bridge',
        'label': '100% Foot (6play)',
        'thumb': 'channels/fr/100foot.png',
        'fanart': 'channels/fr/100foot_fanart.jpg',
        'module': 'resources.lib.channels.fr.6play',
        'enabled': False,
        'order': 121
    }
}
