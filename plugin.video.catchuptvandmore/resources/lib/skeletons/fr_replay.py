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
    - route (folder)/resolver (playable URL): Callback function to run once this item is selected
    - thumb: Item thumb path relative to "media" folder
    - fanart: Item fanart path relative to "meia" folder
"""

menu = {
    'mytf1': {
        'route': '/resources/lib/channels/fr/mytf1:mytf1_root',
        'label': 'MYTF1',
        'thumb': 'channels/fr/mytf1.png',
        'fanart': 'channels/fr/mytf1_fanart.jpg',
        'enabled': True,
        'order': 1
    },
    'francetv': {
        'route': '/resources/lib/channels/fr/francetv:francetv_root',
        'label': 'france.tv',
        'thumb': 'channels/fr/francetv.png',
        'fanart': 'channels/fr/francetv_fanart.jpg',
        'enabled': True,
        'order': 2
    },
    'mycanal': {
        'route': '/resources/lib/channels/fr/mycanal:mycanal_root',
        'label': 'myCANAL',
        'thumb': 'channels/fr/mycanal.png',
        'fanart': 'channels/fr/mycanal_fanart.jpg',
        'enabled': True,
        'order': 4
    },
    '6play': {
        'route': '/resources/lib/channels/fr/6play:sixplay_root',
        'label': '6play',
        'thumb': 'channels/fr/6play.png',
        'fanart': 'channels/fr/6play_fanart.jpg',
        'enabled': True,
        'order': 6
    },
    'nrjplay': {
        'route': '/resources/lib/channels/fr/nrj:nrjplay_root',
        'label': 'NRJ Play',
        'thumb': 'channels/fr/nrjplay.png',
        'fanart': 'channels/fr/nrjplay_fanart.jpg',
        'enabled': True,
        'order': 11
    },
    'bfmtv': {
        'route': '/resources/lib/channels/fr/bfmtv:list_programs',
        'label': 'BFM TV',
        'thumb': 'channels/fr/bfmtv.png',
        'fanart': 'channels/fr/bfmtv_fanart.jpg',
        'enabled': True,
        'order': 13
    },
    'cnews': {
        'route': '/resources/lib/channels/fr/cnews:list_categories',
        'label': 'CNews',
        'thumb': 'channels/fr/cnews.png',
        'fanart': 'channels/fr/cnews_fanart.jpg',
        'enabled': True,
        'order': 14
    },
    'gulli': {
        'route': '/resources/lib/channels/fr/gulli:list_categories',
        'label': 'Gulli',
        'thumb': 'channels/fr/gulli.png',
        'fanart': 'channels/fr/gulli_fanart.jpg',
        'enabled': True,
        'order': 16
    },
    'lequipe': {
        'route': '/resources/lib/channels/fr/lequipe:list_programs',
        'label': 'L\'Équipe',
        'thumb': 'channels/fr/lequipe.png',
        'fanart': 'channels/fr/lequipe_fanart.jpg',
        'enabled': True,
        'order': 19
    },
    'rmcstory': {
        'route': '/resources/lib/channels/fr/rmc:list_categories',
        'label': 'RMC Story',
        'thumb': 'channels/fr/rmcstory.png',
        'fanart': 'channels/fr/rmcstory_fanart.jpg',
        'enabled': True,
        'order': 21
    },
    'la_1ere': {
        'route': '/resources/lib/channels/fr/la_1ere:list_programs',
        'label': 'La 1ère (' + utils.ensure_unicode(Script.setting['la_1ere.language']) + ')',
        'thumb': 'channels/fr/la1ere.png',
        'fanart': 'channels/fr/la1ere_fanart.jpg',
        'enabled': False,
        'order': 23
    },
    'franceinfo': {
        'route': '/resources/lib/channels/fr/franceinfo:list_categories',
        'label': 'France Info',
        'thumb': 'channels/fr/franceinfo.png',
        'fanart': 'channels/fr/franceinfo_fanart.jpg',
        'enabled': True,
        'order': 24
    },
    'bfmbusiness': {
        'route': '/resources/lib/channels/fr/bfmtv:list_programs',
        'label': 'BFM Business',
        'thumb': 'channels/fr/bfmbusiness.png',
        'fanart': 'channels/fr/bfmbusiness_fanart.jpg',
        'enabled': True,
        'order': 25
    },
    'rmc': {
        'route': '/resources/lib/channels/fr/bfmtv:list_programs',
        'label': 'RMC',
        'thumb': 'channels/fr/rmc.png',
        'fanart': 'channels/fr/rmc_fanart.jpg',
        'enabled': True,
        'order': 26
    },
    '01net': {
        'route': '/resources/lib/channels/fr/bfmtv:list_programs',
        'label': '01Net TV',
        'thumb': 'channels/fr/01net.png',
        'fanart': 'channels/fr/01net_fanart.jpg',
        'enabled': True,
        'order': 27
    },
    'lci': {
        'route': '/resources/lib/channels/fr/lci:list_programs',
        'label': 'LCI',
        'thumb': 'channels/fr/lci.png',
        'fanart': 'channels/fr/lci_fanart.jpg',
        'enabled': True,
        'order': 30
    },
    'lcp': {
        'route': '/resources/lib/channels/fr/lcp:list_categories',
        'label': 'LCP Assemblée Nationale',
        'thumb': 'channels/fr/lcp.png',
        'fanart': 'channels/fr/lcp_fanart.jpg',
        'enabled': True,
        'order': 31
    },
    'rmcdecouverte': {
        'route': '/resources/lib/channels/fr/rmc:list_categories',
        'label': 'RMC Découverte',
        'thumb': 'channels/fr/rmcdecouverte.png',
        'fanart': 'channels/fr/rmcdecouverte_fanart.jpg',
        'enabled': True,
        'order': 32
    },
    'publicsenat': {
        'route': '/resources/lib/channels/fr/publicsenat:list_categories',
        'label': 'Public Sénat',
        'thumb': 'channels/fr/publicsenat.png',
        'fanart': 'channels/fr/publicsenat_fanart.jpg',
        'enabled': True,
        'order': 39
    },
    'france3regions': {
        'route': '/resources/lib/channels/fr/france3regions:list_programs',
        'label': 'France 3 Régions (' + utils.ensure_unicode(Script.setting['france3regions.language']) + ')',
        'thumb': 'channels/fr/france3regions.png',
        'fanart': 'channels/fr/france3regions_fanart.jpg',
        'enabled': False,
        'order': 40
    },
    'francetvsport': {
        'route': '/resources/lib/channels/fr/francetvsport:list_categories',
        'label': 'France TV Sport (francetv)',
        'thumb': 'channels/fr/francetvsport.png',
        'fanart': 'channels/fr/francetvsport_fanart.jpg',
        'enabled': True,
        'order': 41
    },
    'histoire': {
        'route': '/resources/lib/channels/fr/tf1thematiques:list_categories',
        'label': 'Histoire',
        'thumb': 'channels/fr/histoire.png',
        'fanart': 'channels/fr/histoire_fanart.jpg',
        'enabled': True,
        'order': 42
    },
    'tvbreizh': {
        'route': '/resources/lib/channels/fr/tf1thematiques:list_categories',
        'label': 'TV Breizh',
        'thumb': 'channels/fr/tvbreizh.png',
        'fanart': 'channels/fr/tvbreizh_fanart.jpg',
        'enabled': True,
        'order': 43
    },
    'ushuaiatv': {
        'route': '/resources/lib/channels/fr/tf1thematiques:list_categories',
        'label': 'Ushuaïa TV',
        'thumb': 'channels/fr/ushuaiatv.png',
        'fanart': 'channels/fr/ushuaiatv_fanart.jpg',
        'enabled': True,
        'order': 44
    },
    'gameone': {
        'route': '/resources/lib/channels/fr/gameone:list_programs',
        'label': 'Game One',
        'thumb': 'channels/fr/gameone.png',
        'fanart': 'channels/fr/gameone_fanart.jpg',
        'enabled': True,
        'order': 53
    },
    'lumni': {
        'route': '/resources/lib/channels/fr/lumni:list_categories',
        'label': 'Lumni (francetv)',
        'thumb': 'channels/fr/lumni.png',
        'fanart': 'channels/fr/lumni_fanart.jpg',
        'enabled': True,
        'order': 54
    },
    'gong': {
        'route': '/resources/lib/channels/fr/gong:list_categories',
        'label': 'Gong',
        'thumb': 'channels/fr/gong.png',
        'fanart': 'channels/fr/gong_fanart.jpg',
        'enabled': True,
        'order': 55
    },
    'bfmparis': {
        'route': '/resources/lib/channels/fr/bfmregion:list_categories',
        'label': 'BFM Paris',
        'thumb': 'channels/fr/bfmparis.png',
        'fanart': 'channels/fr/bfmparis_fanart.jpg',
        'enabled': True,
        'order': 56
    },
    'kto': {
        'route': '/resources/lib/channels/fr/kto:list_categories',
        'label': 'KTO',
        'thumb': 'channels/fr/kto.png',
        'fanart': 'channels/fr/kto_fanart.jpg',
        'enabled': True,
        'order': 64
    },
    'antennereunion': {
        'route': '/resources/lib/channels/fr/antennereunion:list_categories',
        'label': 'Antenne Réunion',
        'thumb': 'channels/fr/antennereunion.png',
        'fanart': 'channels/fr/antennereunion_fanart.jpg',
        'enabled': True,
        'order': 65
    },
    'ouatchtv': {
        'route': '/resources/lib/channels/fr/ouatchtv:list_programs',
        'label': 'Ouatch TV',
        'thumb': 'channels/fr/ouatchtv.png',
        'fanart': 'channels/fr/ouatchtv_fanart.jpg',
        'enabled': False,
        'order': 67
    },
    'lachainemeteo': {
        'route': '/resources/lib/channels/fr/lachainemeteo:list_programs',
        'label': 'La Chaîne Météo',
        'thumb': 'channels/fr/lachainemeteo.png',
        'fanart': 'channels/fr/lachainemeteo_fanart.jpg',
        'enabled': True,
        'order': 70
    },
    'j_one': {
        'route': '/resources/lib/channels/fr/j_one:list_videos',
        'label': 'J-One',
        'thumb': 'channels/fr/jone.png',
        'fanart': 'channels/fr/jone_fanart.jpg',
        'enabled': True,
        'order': 71
    },
    'via93': {
        'route': '/resources/lib/channels/fr/via:list_categories',
        'label': 'vià93',
        'thumb': 'channels/fr/via93.png',
        'fanart': 'channels/fr/via93_fanart.jpg',
        'enabled': True,
        'order': 74
    },
    'jack': {
        'route': '/resources/lib/channels/fr/jack:list_programs',
        'label': 'Jack (mycanal)',
        'thumb': 'channels/fr/jack.png',
        'fanart': 'channels/fr/jack_fanart.jpg',
        'enabled': True,
        'order': 75
    },
    'caledonia': {
        'route': '/resources/lib/channels/fr/caledonia:list_programs',
        'label': 'Caledonia',
        'thumb': 'channels/fr/caledonia.png',
        'fanart': 'channels/fr/caledonia_fanart.jpg',
        'enabled': True,
        'order': 76
    },
    'tebeo': {
        'route': '/resources/lib/channels/fr/tebeo:list_categories',
        'label': 'Tébéo',
        'thumb': 'channels/fr/tebeo.png',
        'fanart': 'channels/fr/tebeo_fanart.jpg',
        'enabled': True,
        'order': 77
    },
    'tl7': {
        'route': '/resources/lib/channels/fr/tl7:list_programs',
        'label': 'Télévision Loire 7',
        'thumb': 'channels/fr/tl7.png',
        'fanart': 'channels/fr/tl7_fanart.jpg',
        'enabled': True,
        'order': 82
    },
    'mblivetv': {
        'route': '/resources/lib/channels/fr/mblivetv:list_videos',
        'label': 'Mont Blanc Live TV',
        'thumb': 'channels/fr/mblivetv.png',
        'fanart': 'channels/fr/mblivetv_fanart.jpg',
        'enabled': True,
        'order': 84
    },
    'tv8montblanc': {
        'route': '/resources/lib/channels/fr/tv8montblanc:list_videos',
        'label': '8 Mont-Blanc',
        'thumb': 'channels/fr/tv8montblanc.png',
        'fanart': 'channels/fr/tv8montblanc_fanart.jpg',
        'enabled': True,
        'order': 85
    },
    'luxetv': {
        'route': '/resources/lib/channels/fr/luxetv:list_categories',
        'label': 'Luxe.TV',
        'thumb': 'channels/fr/luxetv.png',
        'fanart': 'channels/fr/luxetv_fanart.jpg',
        'enabled': True,
        'order': 86
    },
    'alsace20': {
        'route': '/resources/lib/channels/fr/alsace20:list_categories',
        'label': 'Alsace 20',
        'thumb': 'channels/fr/alsace20.png',
        'fanart': 'channels/fr/alsace20_fanart.jpg',
        'enabled': True,
        'order': 87
    },
    'tvpifr': {
        'route': '/resources/lib/channels/fr/tvpifr:TOTO',
        'label': 'TVPI télévision d\'ici',
        'thumb': 'channels/fr/tvpifr.png',
        'fanart': 'channels/fr/tvpifr_fanart.jpg',
        'enabled': True,
        'order': 89
    },
    'paramountchannel_fr': {
        'route': '/resources/lib/channels/fr/paramountchannel_fr:list_categories',
        'label': 'Paramount Channel (FR)',
        'thumb': 'channels/fr/paramountchannel_fr.png',
        'fanart': 'channels/fr/paramountchannel_fr_fanart.jpg',
        'enabled': True,
        'order': 93
    },
    'mtv_fr': {
        'route': '/resources/lib/channels/fr/mtv_fr:list_categories',
        'label': 'MTV (FR)',
        'thumb': 'channels/fr/mtv_fr.png',
        'fanart': 'channels/fr/mtv_fr_fanart.jpg',
        'enabled': True,
        'order': 94
    },
    'bfmlille': {
        'route': '/resources/lib/channels/fr/bfmregion:list_categories',
        'label': 'BFM Lille',
        'thumb': 'channels/fr/bfmlille.png',
        'fanart': 'channels/fr/bfmlille_fanart.jpg',
        'enabled': True,
        'order': 98
    },
    'bfmgrandlittoral': {
        'route': '/resources/lib/channels/fr/bfmregion:list_categories',
        'label': 'BFM Littoral',
        'thumb': 'channels/fr/bfmgrandlittoral.png',
        'fanart': 'channels/fr/bfmgrandlittoral_fanart.jpg',
        'enabled': True,
        'order': 99
    },
    'tebesud': {
        'route': '/resources/lib/channels/fr/tebeo:list_categories',
        'label': 'TébéSud',
        'thumb': 'channels/fr/tebesud.png',
        'fanart': 'channels/fr/tebesud_fanart.jpg',
        'enabled': True,
        'order': 103
    },
    'telegrenoble': {
        'route': '/resources/lib/channels/fr/telegrenoble:list_categories',
        'label': 'TéléGrenoble',
        'thumb': 'channels/fr/telegrenoble.png',
        'fanart': 'channels/fr/telegrenoble_fanart.jpg',
        'enabled': True,
        'order': 105
    },
    'bfmlyon': {
        'route': '/resources/lib/channels/fr/bfmregion:list_categories',
        'label': 'BFM Lyon',
        'thumb': 'channels/fr/bfmlyon.png',
        'fanart': 'channels/fr/bfmlyon_fanart.jpg',
        'enabled': True,
        'order': 107
    },
    'equidia': {
        'route': '/resources/lib/channels/fr/equidia:list_categories',
        'label': 'Equidia',
        'thumb': 'channels/fr/equidia.png',
        'fanart': 'channels/fr/equidia_fanart.jpg',
        'enabled': True,
        'order': 122
    },
    'bsmart': {
        'route': '/resources/lib/channels/fr/bsmart:list_categories',
        'label': 'B Smart',
        'thumb': 'channels/fr/bsmart.png',
        'fanart': 'channels/fr/bsmart_fanart.jpg',
        'enabled': True,
        'order': 123
    }
}
