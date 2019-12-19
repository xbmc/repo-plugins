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
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/tf1.png',
        'fanart': 'channels/fr/tf1_fanart.jpg',
        'module': 'resources.lib.channels.fr.mytf1'
    },
    'tmc': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/tmc.png',
        'fanart': 'channels/fr/tmc_fanart.jpg',
        'module': 'resources.lib.channels.fr.mytf1'
    },
    'tf1-series-films': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/tf1seriesfilms.png',
        'fanart': 'channels/fr/tf1seriesfilms_fanart.jpg',
        'module': 'resources.lib.channels.fr.mytf1'
    },
    'tfx': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/tfx.png',
        'fanart': 'channels/fr/tfx_fanart.jpg',
        'module': 'resources.lib.channels.fr.mytf1'
    },
    'm6': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/m6.png',
        'fanart': 'channels/fr/m6_fanart.jpg',
        'module': 'resources.lib.channels.fr.6play'
    },
    'w9': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/w9.png',
        'fanart': 'channels/fr/w9_fanart.jpg',
        'module': 'resources.lib.channels.fr.6play'
    },
    '6ter': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/6ter.png',
        'fanart': 'channels/fr/6ter_fanart.jpg',
        'module': 'resources.lib.channels.fr.6play'
    },
    'rtl2': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/rtl2.png',
        'fanart': 'channels/fr/rtl2_fanart.jpg',
        'module': 'resources.lib.channels.fr.6play'
    },
    'fun_radio': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/funradio.png',
        'fanart': 'channels/fr/funradio_fanart.jpg',
        'module': 'resources.lib.channels.fr.6play'
    },
    'lci': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/lci.png',
        'fanart': 'channels/fr/lci_fanart.jpg',
        'module': 'resources.lib.channels.fr.lci'
    },
    'gulli': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/gulli.png',
        'fanart': 'channels/fr/gulli_fanart.jpg',
        'module': 'resources.lib.channels.fr.gulli'
    },
    'canalplus': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/canalplus.png',
        'fanart': 'channels/fr/canalplus_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal'
    },
    'c8': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/c8.png',
        'fanart': 'channels/fr/c8_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal'
    },
    'cstar': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/cstar.png',
        'fanart': 'channels/fr/cstar_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal'
    },
    'seasons': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/seasons.png',
        'fanart': 'channels/fr/seasons_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal'
    },
    'comedie': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/comedie.png',
        'fanart': 'channels/fr/comedie_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal'
    },
    'les-chaines-planete': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/leschainesplanete.png',
        'fanart': 'channels/fr/leschainesplanete_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal'
    },
    'golfplus': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/golfplus.png',
        'fanart': 'channels/fr/golfplus_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal'
    },
    'cineplus': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/cineplus.png',
        'fanart': 'channels/fr/cineplus_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal'
    },
    'infosportplus': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/infosportplus.png',
        'fanart': 'channels/fr/infosportplus_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal'
    },
    'polar-plus': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/polarplus.png',
        'fanart': 'channels/fr/polarplus_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal'
    },
    'france-2': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/france2.png',
        'fanart': 'channels/fr/france2_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetv'
    },
    'france-3': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/france3.png',
        'fanart': 'channels/fr/france3_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetv'
    },
    'france-4': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/france4.png',
        'fanart': 'channels/fr/france4_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetv'
    },
    'france-5': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/france5.png',
        'fanart': 'channels/fr/france5_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetv'
    },
    'france-o': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/franceo.png',
        'fanart': 'channels/fr/franceo_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetv'
    },
    'lequipe': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/lequipe.png',
        'fanart': 'channels/fr/lequipe_fanart.jpg',
        'module': 'resources.lib.channels.fr.lequipe'
    },
    'cnews': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/cnews.png',
        'fanart': 'channels/fr/cnews_fanart.jpg',
        'module': 'resources.lib.channels.fr.cnews'
    },
    'rmcdecouverte': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/rmcdecouverte.png',
        'fanart': 'channels/fr/rmcdecouverte_fanart.jpg',
        'module': 'resources.lib.channels.fr.rmcdecouverte'
    },
    'rmcstory': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/rmcstory.png',
        'fanart': 'channels/fr/rmcstory_fanart.jpg',
        'module': 'resources.lib.channels.fr.rmcstory'
    },
    'nrj12': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/nrj12.png',
        'fanart': 'channels/fr/nrj12_fanart.jpg',
        'module': 'resources.lib.channels.fr.nrj'
    },
    'cherie25': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/cherie25.png',
        'fanart': 'channels/fr/cherie25_fanart.jpg',
        'module': 'resources.lib.channels.fr.nrj'
    },
    'lachainemeteo': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/lachainemeteo.png',
        'fanart': 'channels/fr/lachainemeteo_fanart.jpg',
        'module': 'resources.lib.channels.fr.lachainemeteo'
    },
    'histoire': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/histoire.png',
        'fanart': 'channels/fr/histoire_fanart.jpg',
        'module': 'resources.lib.channels.fr.tf1thematiques'
    },
    'tvbreizh': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/tvbreizh.png',
        'fanart': 'channels/fr/tvbreizh_fanart.jpg',
        'module': 'resources.lib.channels.fr.tf1thematiques'
    },
    'ushuaiatv': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/ushuaiatv.png',
        'fanart': 'channels/fr/ushuaiatv_fanart.jpg',
        'module': 'resources.lib.channels.fr.tf1thematiques'
    },
    'slash': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/slash.png',
        'fanart': 'channels/fr/slash_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetv'
    },
    'bfmparis': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/bfmparis.png',
        'fanart': 'channels/fr/bfmparis_fanart.jpg',
        'module': 'resources.lib.channels.fr.bfmparis'
    },
    'bfmtv': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/bfmtv.png',
        'fanart': 'channels/fr/bfmtv_fanart.jpg',
        'module': 'resources.lib.channels.fr.bfmtv'
    },
    'bfmbusiness': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/bfmbusiness.png',
        'fanart': 'channels/fr/bfmbusiness_fanart.jpg',
        'module': 'resources.lib.channels.fr.bfmtv'
    },
    'rmc': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/rmc.png',
        'fanart': 'channels/fr/rmc_fanart.jpg',
        'module': 'resources.lib.channels.fr.bfmtv'
    },
    '01net': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/01net.png',
        'fanart': 'channels/fr/01net_fanart.jpg',
        'module': 'resources.lib.channels.fr.bfmtv'
    },
    'gong': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/gong.png',
        'fanart': 'channels/fr/gong_fanart.jpg',
        'module': 'resources.lib.channels.fr.gong'
    },
    'la_1ere': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/la1ere.png',
        'fanart': 'channels/fr/la1ere_fanart.jpg',
        'module': 'resources.lib.channels.fr.la_1ere'
    },
    'kto': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/kto.png',
        'fanart': 'channels/fr/kto_fanart.jpg',
        'module': 'resources.lib.channels.fr.kto'
    },
    'ouatchtv': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/ouatchtv.png',
        'fanart': 'channels/fr/ouatchtv_fanart.jpg',
        'module': 'resources.lib.channels.fr.ouatchtv'
    },
    'publicsenat': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/publicsenat.png',
        'fanart': 'channels/fr/publicsenat_fanart.jpg',
        'module': 'resources.lib.channels.fr.publicsenat'
    },
    'lcp': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/lcp.png',
        'fanart': 'channels/fr/lcp_fanart.jpg',
        'module': 'resources.lib.channels.fr.lcp'
    },
    'gameone': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/gameone.png',
        'fanart': 'channels/fr/gameone_fanart.jpg',
        'module': 'resources.lib.channels.fr.gameone'
    },
    'francetvsport': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/francetvsport.png',
        'fanart': 'channels/fr/francetvsport_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetvsport'
    },
    'franceinfo': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/franceinfo.png',
        'fanart': 'channels/fr/franceinfo_fanart.jpg',
        'module': 'resources.lib.channels.fr.franceinfo'
    },
    'france3regions': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/france3regions.png',
        'fanart': 'channels/fr/france3regions_fanart.jpg',
        'module': 'resources.lib.channels.fr.france3regions'
    },
    'francetvspectaclesetculture': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/francetvspectaclesetculture.png',
        'fanart': 'channels/fr/francetvspectaclesetculture_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetvspectaclesetculture'
    },
    'francetveducation': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/francetveducation.png',
        'fanart': 'channels/fr/francetveducation_fanart.jpg',
        'module': 'resources.lib.channels.fr.francetveducation'
    },
    'irl': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/irl.png',
        'fanart': 'channels/fr/irl_fanart.jpg',
        'module': 'resources.lib.channels.fr.nouvellesecritures'
    },
    'studio-4': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/studio4.png',
        'fanart': 'channels/fr/studio4_fanart.jpg',
        'module': 'resources.lib.channels.fr.nouvellesecritures'
    },
    'jack': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/jack.png',
        'fanart': 'channels/fr/jack_fanart.jpg',
        'module': 'resources.lib.channels.fr.jack'
    },
    'antennereunion': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/antennereunion.png',
        'fanart': 'channels/fr/antennereunion_fanart.jpg',
        'module': 'resources.lib.channels.fr.antennereunion'
    },
    'caledonia': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/caledonia.png',
        'fanart': 'channels/fr/caledonia_fanart.jpg',
        'module': 'resources.lib.channels.fr.caledonia'
    },
    'tebeo': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/tebeo.png',
        'fanart': 'channels/fr/tebeo_fanart.jpg',
        'module': 'resources.lib.channels.fr.tebeo'
    },
    'via93': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/via93.png',
        'fanart': 'channels/fr/via93_fanart.jpg',
        'module': 'resources.lib.channels.fr.via'
    },
    'tl7': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/tl7.png',
        'fanart': 'channels/fr/tl7_fanart.jpg',
        'module': 'resources.lib.channels.fr.tl7'
    },
    'mblivetv': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/mblivetv.png',
        'fanart': 'channels/fr/mblivetv_fanart.jpg',
        'module': 'resources.lib.channels.fr.mblivetv'
    },
    'tv8montblanc': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/tv8montblanc.png',
        'fanart': 'channels/fr/tv8montblanc_fanart.jpg',
        'module': 'resources.lib.channels.fr.tv8montblanc'
    },
    'luxetv': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/luxetv.png',
        'fanart': 'channels/fr/luxetv_fanart.jpg',
        'module': 'resources.lib.channels.fr.luxetv'
    },
    'alsace20': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/alsace20.png',
        'fanart': 'channels/fr/alsace20_fanart.jpg',
        'module': 'resources.lib.channels.fr.alsace20'
    },
    'tvpifr': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/tvpifr.png',
        'fanart': 'channels/fr/tvpifr_fanart.jpg',
        'module': 'resources.lib.channels.fr.tvpifr'
    },
    'cliquetv': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/cliquetv.png',
        'fanart': 'channels/fr/cliquetv_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal'
    },
    'piwiplus': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/piwiplus.png',
        'fanart': 'channels/fr/piwiplus_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal'
    },
    'teletoonplus': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/teletoonplus.png',
        'fanart': 'channels/fr/teletoonplus_fanart.jpg',
        'module': 'resources.lib.channels.fr.mycanal'
    },
    'paramountchannel_fr': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/paramountchannel_fr.png',
        'fanart': 'channels/fr/paramountchannel_fr_fanart.jpg',
        'module': 'resources.lib.channels.fr.paramountchannel_fr'
    },
    'mtv_fr': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/mtv_fr.png',
        'fanart': 'channels/fr/mtv_fr_fanart.jpg',
        'module': 'resources.lib.channels.fr.mtv_fr'
    },
    'j_one': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/jone.png',
        'fanart': 'channels/fr/jone_fanart.jpg',
        'module': 'resources.lib.channels.fr.j_one'
    },
    'tebesud': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/tebesud.png',
        'fanart': 'channels/fr/tebesud_fanart.jpg',
        'module': 'resources.lib.channels.fr.tebeo'
    },
    'bfmlyon': {
        'callback': 'replay_bridge',
        'thumb': 'channels/fr/bfmlyon.png',
        'fanart': 'channels/fr/bfmlyon_fanart.jpg',
        'module': 'resources.lib.channels.fr.bfmlyon'
    }
}
