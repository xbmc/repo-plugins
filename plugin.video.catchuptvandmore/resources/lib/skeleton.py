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

ROOT = {
    'live_tv': {
        'callback': 'generic_menu',
        'thumb': ['live_tv.png']
    },
    'replay': {
        'callback': 'generic_menu',
        'thumb': ['replay.png']
    },
    'websites': {
        'callback': 'generic_menu',
        'thumb': ['websites.png']
    }
}


LIVE_TV = {
    'fr_live': {
        'callback': 'tv_guide_menu' if Script.setting.get_boolean('tv_guide') else 'generic_menu',
        'thumb': ['channels', 'fr.png']
    },
    'be_live': {
        'callback': 'tv_guide_menu' if Script.setting.get_boolean('tv_guide') else 'generic_menu',
        'thumb': ['channels', 'be.png']
    },
    'ca_live': {
        'callback': 'generic_menu',
        'thumb': ['channels', 'ca.png']
    },
    'ch_live': {
        'callback': 'generic_menu',
        'thumb': ['channels', 'ch.png']
    },
    'uk_live': {
        'callback': 'generic_menu',
        'thumb': ['channels', 'uk.png']
    },
    'wo_live': {
        'callback': 'generic_menu',
        'thumb': ['channels', 'wo.png']
    },
    'us_live': {
        'callback': 'generic_menu',
        'thumb': ['channels', 'us.png']
    },
    'pl_live': {
        'callback': 'generic_menu',
        'thumb': ['channels', 'pl.png']
    },
    'es_live': {
        'callback': 'generic_menu',
        'thumb': ['channels', 'es.png']
    },
    'jp_live': {
        'callback': 'generic_menu',
        'thumb': ['channels', 'jp.png']
    },
    'tn_live': {
        'callback': 'generic_menu',
        'thumb': ['channels', 'tn.png']
    },
    'it_live': {
        'callback': 'generic_menu',
        'thumb': ['channels', 'it.png']
    }
}


REPLAY = {
    'be_replay': {
        'callback': 'generic_menu',
        'thumb': ['channels', 'be.png']
    },
    'ca_replay': {
        'callback': 'generic_menu',
        'thumb': ['channels', 'ca.png']
    },
    'fr_replay': {
        'callback': 'generic_menu',
        'thumb': ['channels', 'fr.png']
    },
    'jp_replay': {
        'callback': 'generic_menu',
        'thumb': ['channels', 'jp.png']
    },
    'ch_replay': {
        'callback': 'generic_menu',
        'thumb': ['channels', 'ch.png']
    },
    'uk_replay': {
        'callback': 'generic_menu',
        'thumb': ['channels', 'uk.png']
    },
    'wo_replay': {
        'callback': 'generic_menu',
        'thumb': ['channels', 'wo.png']
    },
    'us_replay': {
        'callback': 'generic_menu',
        'thumb': ['channels', 'us.png']
    },
    'es_replay': {
        'callback': 'generic_menu',
        'thumb': ['channels', 'es.png']
    },
    'it_replay': {
        'callback': 'generic_menu',
        'thumb': ['channels', 'it.png']
    }
}


FR_LIVE = {
    'tf1': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'tf1.png'],
        'fanart': ['channels', 'fr', 'tf1_fanart.jpg'],
        'module': 'resources.lib.channels.fr.mytf1'
    },
    'tmc': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'tmc.png'],
        'fanart': ['channels', 'fr', 'tmc_fanart.jpg'],
        'module': 'resources.lib.channels.fr.mytf1'
    },
    'tf1-series-films': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'tf1-series-films.png'],
        'fanart': ['channels', 'fr', 'tf1-series-films_fanart.jpg'],
        'module': 'resources.lib.channels.fr.mytf1'
    },
    'tfx': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'tfx.png'],
        'fanart': ['channels', 'fr', 'tfx_fanart.jpg'],
        'module': 'resources.lib.channels.fr.mytf1'
    },
    'rtl2': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'rtl2.png'],
        'fanart': ['channels', 'fr', 'rtl2_fanart.jpg'],
        'module': 'resources.lib.channels.fr.6play'
    },
    'fun_radio': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'fun_radio.png'],
        'fanart': ['channels', 'fr', 'fun_radio_fanart.jpg'],
        'module': 'resources.lib.channels.fr.6play'
    },
    'virginradiotv': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'virginradiotv.png'],
        'fanart': ['channels', 'fr', 'virginradiotv_fanart.jpg'],
        'module': 'resources.lib.channels.fr.virginradiotv'
    },
    'viaoccitanie': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'viaoccitanie.png'],
        'fanart': ['channels', 'fr', 'viaoccitanie_fanart.jpg'],
        'module': 'resources.lib.channels.fr.via'
    },
    'lci': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'lci.png'],
        'fanart': ['channels', 'fr', 'lci_fanart.jpg'],
        'module': 'resources.lib.channels.fr.lci'
    },
    'antennereunion': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'antennereunion.png'],
        'fanart': ['channels', 'fr', 'antennereunion_fanart.jpg'],
        'module': 'resources.lib.channels.fr.antennereunion'
    },
    'gulli': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'gulli.png'],
        'fanart': ['channels', 'fr', 'gulli_fanart.jpg'],
        'module': 'resources.lib.channels.fr.gulli'
    },
    'canalplus': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'canalplus.png'],
        'fanart': ['channels', 'fr', 'canalplus_fanart.jpg'],
        'module': 'resources.lib.channels.fr.mycanal'
    },
    'c8': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'c8.png'],
        'fanart': ['channels', 'fr', 'c8_fanart.jpg'],
        'module': 'resources.lib.channels.fr.mycanal'
    },
    'cstar': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'cstar.png'],
        'fanart': ['channels', 'fr', 'cstar_fanart.jpg'],
        'module': 'resources.lib.channels.fr.mycanal'
    },
    'france-2': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'france-2.png'],
        'fanart': ['channels', 'fr', 'france-2_fanart.jpg'],
        'module': 'resources.lib.channels.fr.francetv'
    },
    'france-3': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'france-3.png'],
        'fanart': ['channels', 'fr', 'france-3_fanart.jpg'],
        'module': 'resources.lib.channels.fr.francetv'
    },
    'france-4': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'france-4.png'],
        'fanart': ['channels', 'fr', 'france-4_fanart.jpg'],
        'module': 'resources.lib.channels.fr.francetv'
    },
    'france-5': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'france-5.png'],
        'fanart': ['channels', 'fr', 'france-5_fanart.jpg'],
        'module': 'resources.lib.channels.fr.francetv'
    },
    'france-o': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'france-o.png'],
        'fanart': ['channels', 'fr', 'france-o_fanart.jpg'],
        'module': 'resources.lib.channels.fr.francetv'
    },
    'lequipe': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'lequipe.png'],
        'fanart': ['channels', 'fr', 'lequipe_fanart.jpg'],
        'module': 'resources.lib.channels.fr.lequipe'
    },
    'cnews': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'cnews.png'],
        'fanart': ['channels', 'fr', 'cnews_fanart.jpg'],
        'module': 'resources.lib.channels.fr.cnews'
    },
    'rmcdecouverte': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'rmcdecouverte.png'],
        'fanart': ['channels', 'fr', 'rmcdecouverte_fanart.jpg'],
        'module': 'resources.lib.channels.fr.rmcdecouverte'
    },
    'rmcstory': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'rmcstory.png'],
        'fanart': ['channels', 'fr', 'rmcstory_fanart.jpg'],
        'module': 'resources.lib.channels.fr.rmcstory'
    },
    'canal10': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'canal10.png'],
        'fanart': ['channels', 'fr', 'canal10_fanart.jpg'],
        'module': 'resources.lib.channels.fr.canal10'
    },
    'nrj12': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'nrj12.png'],
        'fanart': ['channels', 'fr', 'nrj12_fanart.jpg'],
        'module': 'resources.lib.channels.fr.nrj'
    },
    'cherie25': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'cherie25.png'],
        'fanart': ['channels', 'fr', 'cherie25_fanart.jpg'],
        'module': 'resources.lib.channels.fr.nrj'
    },
    'bfmparis': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'bfmparis.png'],
        'fanart': ['channels', 'fr', 'bfmparis_fanart.jpg'],
        'module': 'resources.lib.channels.fr.bfmparis'
    },
    'bfmtv': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'bfmtv.png'],
        'fanart': ['channels', 'fr', 'bfmtv_fanart.jpg'],
        'module': 'resources.lib.channels.fr.bfmtv'
    },
    'bfmbusiness': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'bfmbusiness.png'],
        'fanart': ['channels', 'fr', 'bfmbusiness_fanart.jpg'],
        'module': 'resources.lib.channels.fr.bfmtv'
    },
    'gong': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'gong.png'],
        'fanart': ['channels', 'fr', 'gong_fanart.jpg'],
        'module': 'resources.lib.channels.fr.gong'
    },
    'la_1ere': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'la_1ere.png'],
        'fanart': ['channels', 'fr', 'la_1ere_fanart.jpg'],
        'module': 'resources.lib.channels.fr.la_1ere'
    },
    'kto': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'kto.png'],
        'fanart': ['channels', 'fr', 'kto_fanart.jpg'],
        'module': 'resources.lib.channels.fr.kto'
    },
    'ouatchtv': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'ouatchtv.png'],
        'fanart': ['channels', 'fr', 'ouatchtv_fanart.jpg'],
        'module': 'resources.lib.channels.fr.ouatchtv'
    },
    'publicsenat': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'publicsenat.png'],
        'fanart': ['channels', 'fr', 'publicsenat_fanart.jpg'],
        'module': 'resources.lib.channels.fr.publicsenat'
    },
    'lcp': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'lcp.png'],
        'fanart': ['channels', 'fr', 'lcp_fanart.jpg'],
        'module': 'resources.lib.channels.fr.lcp'
    },
    'francetvsport': {
        'callback': 'multi_live_bridge',
        'thumb': ['channels', 'fr', 'francetvsport.png'],
        'fanart': ['channels', 'fr', 'francetvsport_fanart.jpg'],
        'module': 'resources.lib.channels.fr.francetvsport'
    },
    'franceinfo': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'franceinfo.png'],
        'fanart': ['channels', 'fr', 'franceinfo_fanart.jpg'],
        'module': 'resources.lib.channels.fr.franceinfo'
    },
    'france3regions': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'france3regions.png'],
        'fanart': ['channels', 'fr', 'france3regions_fanart.jpg'],
        'module': 'resources.lib.channels.fr.france3regions'
    },
    'viaatv': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'viaatv.png'],
        'fanart': ['channels', 'fr', 'viaatv_fanart.jpg'],
        'module': 'resources.lib.channels.fr.via'
    },
    'viagrandparis': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'viagrandparis.png'],
        'fanart': ['channels', 'fr', 'viagrandparis_fanart.jpg'],
        'module': 'resources.lib.channels.fr.via'
    },
    'via93': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'via93.png'],
        'fanart': ['channels', 'fr', 'via93_fanart.jpg'],
        'module': 'resources.lib.channels.fr.via'
    },
    'tebeo': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'fr', 'tebeo.png'],
        'fanart': ['channels', 'fr', 'tebeo_fanart.jpg'],
        'module': 'resources.lib.channels.fr.tebeo'
    }
}

TN_LIVE = {
    'watania1': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'tn', 'watania1.png'],
        'fanart': ['channels', 'tn', 'watania1_fanart.jpg'],
        'module': 'resources.lib.channels.tn.watania'
    },
    'watania2': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'tn', 'watania2.png'],
        'fanart': ['channels', 'tn', 'watania2_fanart.jpg'],
        'module': 'resources.lib.channels.tn.watania'
    },
    'nessma': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'tn', 'nessma.png'],
        'fanart': ['channels', 'tn', 'nessma_fanart.jpg'],
        'module': 'resources.lib.channels.tn.nessma'
    }
}

PL_LIVE = {
    'tvp3': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'pl', 'tvp3.png'],
        'fanart': ['channels', 'pl', 'tvp3_fanart.jpg'],
        'module': 'resources.lib.channels.pl.tvp'
    },
    'tvpinfo': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'pl', 'tvpinfo.png'],
        'fanart': ['channels', 'pl', 'tvpinfo_fanart.jpg'],
        'module': 'resources.lib.channels.pl.tvp'
    },
    'tvppolonia': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'pl', 'tvppolonia.png'],
        'fanart': ['channels', 'pl', 'tvppolonia_fanart.jpg'],
        'module': 'resources.lib.channels.pl.tvp'
    }
}

ES_LIVE = {
    'realmadridtv': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'es', 'realmadridtv.png'],
        'fanart': ['channels', 'es', 'realmadridtv_fanart.jpg'],
        'module': 'resources.lib.channels.es.realmadridtv'
    },
    'antena3': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'es', 'antena3.png'],
        'fanart': ['channels', 'es', 'antena3_fanart.jpg'],
        'module': 'resources.lib.channels.es.atresplayer'
    },
    'lasexta': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'es', 'lasexta.png'],
        'fanart': ['channels', 'es', 'lasexta_fanart.jpg'],
        'module': 'resources.lib.channels.es.atresplayer'
    },
    'neox': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'es', 'neox.png'],
        'fanart': ['channels', 'es', 'neox_fanart.jpg'],
        'module': 'resources.lib.channels.es.atresplayer'
    },
    'nova': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'es', 'nova.png'],
        'fanart': ['channels', 'es', 'nova_fanart.jpg'],
        'module': 'resources.lib.channels.es.atresplayer'
    },
    'mega': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'es', 'mega.png'],
        'fanart': ['channels', 'es', 'mega_fanart.jpg'],
        'module': 'resources.lib.channels.es.atresplayer'
    },
    'atreseries': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'es', 'atreseries.png'],
        'fanart': ['channels', 'es', 'atreseries_fanart.jpg'],
        'module': 'resources.lib.channels.es.atresplayer'
    },
    'telecinco': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'es', 'telecinco.png'],
        'fanart': ['channels', 'es', 'telecinco_fanart.jpg'],
        'module': 'resources.lib.channels.es.mitele'
    },
    'cuatro': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'es', 'cuatro.png'],
        'fanart': ['channels', 'es', 'cuatro_fanart.jpg'],
        'module': 'resources.lib.channels.es.mitele'
    },
    'fdf': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'es', 'fdf.png'],
        'fanart': ['channels', 'es', 'fdf_fanart.jpg'],
        'module': 'resources.lib.channels.es.mitele'
    },
    'boing': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'es', 'boing.png'],
        'fanart': ['channels', 'es', 'boing_fanart.jpg'],
        'module': 'resources.lib.channels.es.mitele'
    },
    'energy': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'es', 'energy.png'],
        'fanart': ['channels', 'es', 'energy_fanart.jpg'],
        'module': 'resources.lib.channels.es.mitele'
    },
    'divinity': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'es', 'divinity.png'],
        'fanart': ['channels', 'es', 'divinity_fanart.jpg'],
        'module': 'resources.lib.channels.es.mitele'
    },
    'bemad': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'es', 'bemad.png'],
        'fanart': ['channels', 'es', 'bemad_fanart.jpg'],
        'module': 'resources.lib.channels.es.mitele'
    }
}

WO_LIVE = {
    'tivi5monde': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'wo', 'tivi5monde.png'],
        'fanart': ['channels', 'wo', 'tivi5monde_fanart.jpg'],
        'module': 'resources.lib.channels.wo.tivi5monde'
    },
    'tv5mondefbs': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'wo', 'tv5mondefbs.png'],
        'fanart': ['channels', 'wo', 'tv5mondefbs_fanart.jpg'],
        'module': 'resources.lib.channels.wo.tv5monde'
    },
    'tv5mondeinfo': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'wo', 'tv5mondeinfo.png'],
        'fanart': ['channels', 'wo', 'tv5mondeinfo_fanart.jpg'],
        'module': 'resources.lib.channels.wo.tv5monde'
    },
    'euronews': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'wo', 'euronews.png'],
        'fanart': ['channels', 'wo', 'euronews_fanart.jpg'],
        'module': 'resources.lib.channels.wo.euronews'
    },
    'arte': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'wo', 'arte.png'],
        'fanart': ['channels', 'wo', 'arte_fanart.jpg'],
        'module': 'resources.lib.channels.wo.arte'
    },
    'arirang': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'wo', 'arirang.png'],
        'fanart': ['channels', 'wo', 'arirang_fanart.jpg'],
        'module': 'resources.lib.channels.wo.arirang'
    },
    'afriquemedia': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'wo', 'afriquemedia.png'],
        'fanart': ['channels', 'wo', 'afriquemedia_fanart.jpg'],
        'module': 'resources.lib.channels.wo.afriquemedia'
    },
    'dw': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'wo', 'dw.png'],
        'fanart': ['channels', 'wo', 'dw_fanart.jpg'],
        'module': 'resources.lib.channels.wo.dw'
    },
    'icirdi': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'wo', 'icirdi.png'],
        'fanart': ['channels', 'wo', 'icirdi_fanart.jpg'],
        'module': 'resources.lib.channels.wo.icirdi'
    },
    'bvn': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'wo', 'bvn.png'],
        'fanart': ['channels', 'wo', 'bvn_fanart.jpg'],
        'module': 'resources.lib.channels.wo.bvn'
    },
    'france24': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'wo', 'france24.png'],
        'fanart': ['channels', 'wo', 'france24_fanart.jpg'],
        'module': 'resources.lib.channels.wo.france24'
    },
    'qvc': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'wo', 'qvc.png'],
        'fanart': ['channels', 'wo', 'qvc_fanart.jpg'],
        'module': 'resources.lib.channels.wo.qvc'
    },
    'souvenirsfromearth': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'wo', 'souvenirsfromearth.png'],
        'fanart': ['channels', 'wo', 'souvenirsfromearth_fanart.jpg'],
        'module': 'resources.lib.channels.wo.souvenirsfromearth'
    },
    'nhkworld': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'wo', 'nhkworld.png'],
        'fanart': ['channels', 'wo', 'nhkworld_fanart.jpg'],
        'module': 'resources.lib.channels.wo.nhkworld'
    },
    'icitelevision': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'wo', 'icitelevision.png'],
        'fanart': ['channels', 'wo', 'icitelevision_fanart.jpg'],
        'module': 'resources.lib.channels.wo.icitelevision'
    },
    'channelnewsasia': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'wo', 'channelnewsasia.png'],
        'fanart': ['channels', 'wo', 'channelnewsasia_fanart.jpg'],
        'module': 'resources.lib.channels.wo.channelnewsasia'
    },
    'cgtn': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'wo', 'cgtn.png'],
        'fanart': ['channels', 'wo', 'cgtn_fanart.jpg'],
        'module': 'resources.lib.channels.wo.cgtn'
    },
    'cgtndocumentary': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'wo', 'cgtndocumentary.png'],
        'fanart': ['channels', 'wo', 'cgtndocumentary_fanart.jpg'],
        'module': 'resources.lib.channels.wo.cgtn'
    },
    'paramountchannel': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'wo', 'paramountchannel.png'],
        'fanart': ['channels', 'wo', 'paramountchannel_fanart.jpg'],
        'module': 'resources.lib.channels.wo.paramountchannel'
    }
}

JP_LIVE = {
    'japanetshoppingdx': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'jp', 'japanetshoppingdx.png'],
        'fanart': ['channels', 'jp', 'japanetshoppingdx_fanart.jpg'],
        'module': 'resources.lib.channels.jp.japanetshoppingdx'
    },
    'ntvnews24': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'jp', 'ntvnews24.png'],
        'fanart': ['channels', 'jp', 'ntvnews24_fanart.jpg'],
        'module': 'resources.lib.channels.jp.ntvnews24'
    }
}

UK_LIVE = {
    'blaze': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'uk', 'blaze.png'],
        'fanart': ['channels', 'uk', 'blaze_fanart.jpg'],
        'module': 'resources.lib.channels.uk.blaze'
    },
    'skynews': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'uk', 'skynews.png'],
        'fanart': ['channels', 'uk', 'skynews_fanart.jpg'],
        'module': 'resources.lib.channels.uk.sky'
    },
    'stv': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'uk', 'stv.png'],
        'fanart': ['channels', 'uk', 'stv_fanart.jpg'],
        'module': 'resources.lib.channels.uk.stv'
    },
    'kerrang': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'uk', 'kerrang.png'],
        'fanart': ['channels', 'uk', 'kerrang_fanart.jpg'],
        'module': 'resources.lib.channels.uk.boxplus'
    },
    'magic': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'uk', 'magic.png'],
        'fanart': ['channels', 'uk', 'magic_fanart.jpg'],
        'module': 'resources.lib.channels.uk.boxplus'
    },
    'kiss': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'uk', 'kiss.png'],
        'fanart': ['channels', 'uk', 'kiss_fanart.jpg'],
        'module': 'resources.lib.channels.uk.boxplus'
    },
    'the-box': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'uk', 'the-box.png'],
        'fanart': ['channels', 'uk', 'the-box_fanart.jpg'],
        'module': 'resources.lib.channels.uk.boxplus'
    },
    'box-upfront': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'uk', 'box-upfront.png'],
        'fanart': ['channels', 'uk', 'box-upfront_fanart.jpg'],
        'module': 'resources.lib.channels.uk.boxplus'
    },
    'box-hits': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'uk', 'box-hits.png'],
        'fanart': ['channels', 'uk', 'box-hits_fanart.jpg'],
        'module': 'resources.lib.channels.uk.boxplus'
    }
}

BE_LIVE = {
    'bx1': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'be', 'bx1.png'],
        'fanart': ['channels', 'be', 'bx1_fanart.jpg'],
        'module': 'resources.lib.channels.be.bx1'
    },
    'nrjhitstvbe': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'be', 'nrjhitstvbe.png'],
        'fanart': ['channels', 'be', 'nrjhitstvbe_fanart.jpg'],
        'module': 'resources.lib.channels.be.nrjhitstvbe'
    },
    'auvio': {
        'callback': 'multi_live_bridge',
        'thumb': ['channels', 'be', 'auvio.png'],
        'fanart': ['channels', 'be', 'auvio_fanart.jpg'],
        'module': 'resources.lib.channels.be.rtbf'
    },
    'rtc': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'be', 'rtc.png'],
        'fanart': ['channels', 'be', 'rtc_fanart.jpg'],
        'module': 'resources.lib.channels.be.rtc'
    },
    'telemb': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'be', 'telemb.png'],
        'fanart': ['channels', 'be', 'telemb_fanart.jpg'],
        'module': 'resources.lib.channels.be.telemb'
    },
    'tvlux': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'be', 'tvlux.png'],
        'fanart': ['channels', 'be', 'tvlux_fanart.jpg'],
        'module': 'resources.lib.channels.be.tvlux'
    },
    'een': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'be', 'een.png'],
        'fanart': ['channels', 'be', 'een_fanart.jpg'],
        'module': 'resources.lib.channels.be.vrt'
    },
    'canvas': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'be', 'canvas.png'],
        'fanart': ['channels', 'be', 'canvas_fanart.jpg'],
        'module': 'resources.lib.channels.be.vrt'
    },
    'ketnet': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'be', 'ketnet.png'],
        'fanart': ['channels', 'be', 'ketnet_fanart.jpg'],
        'module': 'resources.lib.channels.be.vrt'
    }
}

CA_LIVE = {
    'ntvca': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'ca', 'ntvca.png'],
        'fanart': ['channels', 'ca', 'ntvca_fanart.jpg'],
        'module': 'resources.lib.channels.ca.ntvca'
    },
    'tva': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'ca', 'tva.png'],
        'fanart': ['channels', 'ca', 'tva_fanart.jpg'],
        'module': 'resources.lib.channels.ca.tva'
    },
    'telequebec': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'ca', 'telequebec.png'],
        'fanart': ['channels', 'ca', 'telequebec_fanart.jpg'],
        'module': 'resources.lib.channels.ca.telequebec'
    },
    'icitele': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'ca', 'icitele.png'],
        'fanart': ['channels', 'ca', 'icitele_fanart.jpg'],
        'module': 'resources.lib.channels.ca.icitele'
    }
}

CH_LIVE = {
    'rtsun': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'ch', 'rtsun.png'],
        'fanart': ['channels', 'ch', 'rtsun_fanart.jpg'],
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'rtsdeux': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'ch', 'rtsdeux.png'],
        'fanart': ['channels', 'ch', 'rtsdeux_fanart.jpg'],
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'rtsinfo': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'ch', 'rtsinfo.png'],
        'fanart': ['channels', 'ch', 'rtsinfo_fanart.jpg'],
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'rtscouleur3': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'ch', 'rtscouleur3.png'],
        'fanart': ['channels', 'ch', 'rtscouleur3_fanart.jpg'],
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'rsila1': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'ch', 'rsila1.png'],
        'fanart': ['channels', 'ch', 'rsila1_fanart.jpg'],
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'rsila2': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'ch', 'rsila2.png'],
        'fanart': ['channels', 'ch', 'rsila2_fanart.jpg'],
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'srf1': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'ch', 'srf1.png'],
        'fanart': ['channels', 'ch', 'srf1_fanart.jpg'],
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'srfinfo': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'ch', 'srfinfo.png'],
        'fanart': ['channels', 'ch', 'srfinfo_fanart.jpg'],
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'srfzwei': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'ch', 'srfzwei.png'],
        'fanart': ['channels', 'ch', 'srfzwei_fanart.jpg'],
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'rtraufsrf1': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'ch', 'rtraufsrf1.png'],
        'fanart': ['channels', 'ch', 'rtraufsrf1_fanart.jpg'],
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'rtraufsrfinfo': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'ch', 'rtraufsrfinfo.png'],
        'fanart': ['channels', 'ch', 'rtraufsrfinfo_fanart.jpg'],
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'rtraufsrf2': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'ch', 'rtraufsrf2.png'],
        'fanart': ['channels', 'ch', 'rtraufsrf2_fanart.jpg'],
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'rougetv': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'ch', 'rougetv.png'],
        'fanart': ['channels', 'ch', 'rougetv_fanart.jpg'],
        'module': 'resources.lib.channels.ch.rougetv'
    },
    'teleticino': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'ch', 'teleticino.png'],
        'fanart': ['channels', 'ch', 'teleticino_fanart.jpg'],
        'module': 'resources.lib.channels.ch.teleticino'
    }
}

US_LIVE = {
    'pbskids': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'us', 'pbskids.png'],
        'fanart': ['channels', 'us', 'pbskids_fanart.jpg'],
        'module': 'resources.lib.channels.us.pbskids'
    },
    'tbd': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'us', 'tbd.png'],
        'fanart': ['channels', 'us', 'tbd_fanart.jpg'],
        'module': 'resources.lib.channels.us.tbd'
    },
    'cbsnews': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'us', 'cbsnews.png'],
        'fanart': ['channels', 'us', 'cbsnews_fanart.jpg'],
        'module': 'resources.lib.channels.us.cbsnews'
    },
    'abcnews': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'us', 'abcnews.png'],
        'fanart': ['channels', 'us', 'abcnews_fanart.jpg'],
        'module': 'resources.lib.channels.us.abcnews'
    }
}

IT_LIVE = {
    'la7': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'it', 'la7.png'],
        'fanart': ['channels', 'it', 'la7_fanart.jpg'],
        'module': 'resources.lib.channels.it.la7'
    },
    'rainews24': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'it', 'rainews24.png'],
        'fanart': ['channels', 'it', 'rainews24_fanart.jpg'],
        'module': 'resources.lib.channels.it.raiplay'
    },
    'rai1': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'it', 'rai1.png'],
        'fanart': ['channels', 'it', 'rai1_fanart.jpg'],
        'module': 'resources.lib.channels.it.raiplay'
    },
    'rai2': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'it', 'rai2.png'],
        'fanart': ['channels', 'it', 'rai2_fanart.jpg'],
        'module': 'resources.lib.channels.it.raiplay'
    },
    'rai3': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'it', 'rai3.png'],
        'fanart': ['channels', 'it', 'rai3_fanart.jpg'],
        'module': 'resources.lib.channels.it.raiplay'
    },
    'rai4': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'it', 'rai4.png'],
        'fanart': ['channels', 'it', 'rai4_fanart.jpg'],
        'module': 'resources.lib.channels.it.raiplay'
    },
    'rai5': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'it', 'rai5.png'],
        'fanart': ['channels', 'it', 'rai5_fanart.jpg'],
        'module': 'resources.lib.channels.it.raiplay'
    },
    'raisportpiuhd': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'it', 'raisportpiuhd.png'],
        'fanart': ['channels', 'it', 'raisportpiuhd_fanart.jpg'],
        'module': 'resources.lib.channels.it.raiplay'
    },
    'raimovie': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'it', 'raimovie.png'],
        'fanart': ['channels', 'it', 'raimovie_fanart.jpg'],
        'module': 'resources.lib.channels.it.raiplay'
    },
    'raipremium': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'it', 'raipremium.png'],
        'fanart': ['channels', 'it', 'raipremium_fanart.jpg'],
        'module': 'resources.lib.channels.it.raiplay'
    },
    'raiyoyo': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'it', 'raiyoyo.png'],
        'fanart': ['channels', 'it', 'raiyoyo_fanart.jpg'],
        'module': 'resources.lib.channels.it.raiplay'
    },
    'raigulp': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'it', 'raigulp.png'],
        'fanart': ['channels', 'it', 'raigulp_fanart.jpg'],
        'module': 'resources.lib.channels.it.raiplay'
    },
    'raistoria': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'it', 'raistoria.png'],
        'fanart': ['channels', 'it', 'raistoria_fanart.jpg'],
        'module': 'resources.lib.channels.it.raiplay'
    },
    'raiscuola': {
        'callback': 'live_bridge',
        'thumb': ['channels', 'it', 'raiscuola.png'],
        'fanart': ['channels', 'it', 'raiscuola_fanart.jpg'],
        'module': 'resources.lib.channels.it.raiplay'
    }
}

FR_REPLAY = {
    'tf1': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'tf1.png'],
        'fanart': ['channels', 'fr', 'tf1_fanart.jpg'],
        'module': 'resources.lib.channels.fr.mytf1'
    },
    'tmc': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'tmc.png'],
        'fanart': ['channels', 'fr', 'tmc_fanart.jpg'],
        'module': 'resources.lib.channels.fr.mytf1'
    },
    'tf1-series-films': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'tf1-series-films.png'],
        'fanart': ['channels', 'fr', 'tf1-series-films_fanart.jpg'],
        'module': 'resources.lib.channels.fr.mytf1'
    },
    'tfx': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'tfx.png'],
        'fanart': ['channels', 'fr', 'tfx_fanart.jpg'],
        'module': 'resources.lib.channels.fr.mytf1'
    },
    'tfou': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'tfou.png'],
        'fanart': ['channels', 'fr', 'tfou_fanart.jpg'],
        'module': 'resources.lib.channels.fr.mytf1'
    },
    'm6': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'm6.png'],
        'fanart': ['channels', 'fr', 'm6_fanart.jpg'],
        'module': 'resources.lib.channels.fr.6play'
    },
    'w9': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'w9.png'],
        'fanart': ['channels', 'fr', 'w9_fanart.jpg'],
        'module': 'resources.lib.channels.fr.6play'
    },
    '6ter': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', '6ter.png'],
        'fanart': ['channels', 'fr', '6ter_fanart.jpg'],
        'module': 'resources.lib.channels.fr.6play'
    },
    'stories': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'stories.png'],
        'fanart': ['channels', 'fr', 'stories_fanart.jpg'],
        'module': 'resources.lib.channels.fr.6play'
    },
    'comedy': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'comedy.png'],
        'fanart': ['channels', 'fr', 'comedy_fanart.jpg'],
        'module': 'resources.lib.channels.fr.6play'
    },
    'rtl2': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'rtl2.png'],
        'fanart': ['channels', 'fr', 'rtl2_fanart.jpg'],
        'module': 'resources.lib.channels.fr.6play'
    },
    'fun_radio': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'fun_radio.png'],
        'fanart': ['channels', 'fr', 'fun_radio_fanart.jpg'],
        'module': 'resources.lib.channels.fr.6play'
    },
    'lci': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'lci.png'],
        'fanart': ['channels', 'fr', 'lci_fanart.jpg'],
        'module': 'resources.lib.channels.fr.lci'
    },
    'gulli': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'gulli.png'],
        'fanart': ['channels', 'fr', 'gulli_fanart.jpg'],
        'module': 'resources.lib.channels.fr.gulli'
    },
    'canalplus': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'canalplus.png'],
        'fanart': ['channels', 'fr', 'canalplus_fanart.jpg'],
        'module': 'resources.lib.channels.fr.mycanal'
    },
    'c8': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'c8.png'],
        'fanart': ['channels', 'fr', 'c8_fanart.jpg'],
        'module': 'resources.lib.channels.fr.mycanal'
    },
    'cstar': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'cstar.png'],
        'fanart': ['channels', 'fr', 'cstar_fanart.jpg'],
        'module': 'resources.lib.channels.fr.mycanal'
    },
    'seasons': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'seasons.png'],
        'fanart': ['channels', 'fr', 'seasons_fanart.jpg'],
        'module': 'resources.lib.channels.fr.mycanal'
    },
    'comedie': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'comedie.png'],
        'fanart': ['channels', 'fr', 'comedie_fanart.jpg'],
        'module': 'resources.lib.channels.fr.mycanal'
    },
    'les-chaines-planete': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'les-chaines-planete.png'],
        'fanart': ['channels', 'fr', 'les-chaines-planete_fanart.jpg'],
        'module': 'resources.lib.channels.fr.mycanal'
    },
    'golfplus': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'golfplus.png'],
        'fanart': ['channels', 'fr', 'golfplus_fanart.jpg'],
        'module': 'resources.lib.channels.fr.mycanal'
    },
    'cineplus': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'cineplus.png'],
        'fanart': ['channels', 'fr', 'cineplus_fanart.jpg'],
        'module': 'resources.lib.channels.fr.mycanal'
    },
    'infosportplus': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'infosportplus.png'],
        'fanart': ['channels', 'fr', 'infosportplus_fanart.jpg'],
        'module': 'resources.lib.channels.fr.mycanal'
    },
    'polar-plus': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'polar-plus.png'],
        'fanart': ['channels', 'fr', 'polar-plus_fanart.jpg'],
        'module': 'resources.lib.channels.fr.mycanal'
    },
    'france-2': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'france-2.png'],
        'fanart': ['channels', 'fr', 'france-2_fanart.jpg'],
        'module': 'resources.lib.channels.fr.francetv'
    },
    'france-3': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'france-3.png'],
        'fanart': ['channels', 'fr', 'france-3_fanart.jpg'],
        'module': 'resources.lib.channels.fr.francetv'
    },
    'france-4': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'france-4.png'],
        'fanart': ['channels', 'fr', 'france-4_fanart.jpg'],
        'module': 'resources.lib.channels.fr.francetv'
    },
    'france-5': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'france-5.png'],
        'fanart': ['channels', 'fr', 'france-5_fanart.jpg'],
        'module': 'resources.lib.channels.fr.francetv'
    },
    'france-o': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'france-o.png'],
        'fanart': ['channels', 'fr', 'france-o_fanart.jpg'],
        'module': 'resources.lib.channels.fr.francetv'
    },
    'lequipe': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'lequipe.png'],
        'fanart': ['channels', 'fr', 'lequipe_fanart.jpg'],
        'module': 'resources.lib.channels.fr.lequipe'
    },
    'cnews': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'cnews.png'],
        'fanart': ['channels', 'fr', 'cnews_fanart.jpg'],
        'module': 'resources.lib.channels.fr.cnews'
    },
    'rmcdecouverte': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'rmcdecouverte.png'],
        'fanart': ['channels', 'fr', 'rmcdecouverte_fanart.jpg'],
        'module': 'resources.lib.channels.fr.rmcdecouverte'
    },
    'rmcstory': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'rmcstory.png'],
        'fanart': ['channels', 'fr', 'rmcstory_fanart.jpg'],
        'module': 'resources.lib.channels.fr.rmcstory'
    },
    'nrj12': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'nrj12.png'],
        'fanart': ['channels', 'fr', 'nrj12_fanart.jpg'],
        'module': 'resources.lib.channels.fr.nrj'
    },
    'cherie25': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'cherie25.png'],
        'fanart': ['channels', 'fr', 'cherie25_fanart.jpg'],
        'module': 'resources.lib.channels.fr.nrj'
    },
    'lachainemeteo': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'lachainemeteo.png'],
        'fanart': ['channels', 'fr', 'lachainemeteo_fanart.jpg'],
        'module': 'resources.lib.channels.fr.lachainemeteo'
    },
    'histoire': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'histoire.png'],
        'fanart': ['channels', 'fr', 'histoire_fanart.jpg'],
        'module': 'resources.lib.channels.fr.tf1thematiques'
    },
    'tvbreizh': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'tvbreizh.png'],
        'fanart': ['channels', 'fr', 'tvbreizh_fanart.jpg'],
        'module': 'resources.lib.channels.fr.tf1thematiques'
    },
    'ushuaiatv': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'ushuaiatv.png'],
        'fanart': ['channels', 'fr', 'ushuaiatv_fanart.jpg'],
        'module': 'resources.lib.channels.fr.tf1thematiques'
    },
    'slash': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'slash.png'],
        'fanart': ['channels', 'fr', 'slash_fanart.jpg'],
        'module': 'resources.lib.channels.fr.francetv'
    },
    'bfmparis': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'bfmparis.png'],
        'fanart': ['channels', 'fr', 'bfmparis_fanart.jpg'],
        'module': 'resources.lib.channels.fr.bfmparis'
    },
    'bfmtv': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'bfmtv.png'],
        'fanart': ['channels', 'fr', 'bfmtv_fanart.jpg'],
        'module': 'resources.lib.channels.fr.bfmtv'
    },
    'bfmbusiness': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'bfmbusiness.png'],
        'fanart': ['channels', 'fr', 'bfmbusiness_fanart.jpg'],
        'module': 'resources.lib.channels.fr.bfmtv'
    },
    'rmc': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'rmc.png'],
        'fanart': ['channels', 'fr', 'rmc_fanart.jpg'],
        'module': 'resources.lib.channels.fr.bfmtv'
    },
    '01net': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', '01net.png'],
        'fanart': ['channels', 'fr', '01net_fanart.jpg'],
        'module': 'resources.lib.channels.fr.bfmtv'
    },
    'gong': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'gong.png'],
        'fanart': ['channels', 'fr', 'gong_fanart.jpg'],
        'module': 'resources.lib.channels.fr.gong'
    },
    'la_1ere': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'la_1ere.png'],
        'fanart': ['channels', 'fr', 'la_1ere_fanart.jpg'],
        'module': 'resources.lib.channels.fr.la_1ere'
    },
    'kto': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'kto.png'],
        'fanart': ['channels', 'fr', 'kto_fanart.jpg'],
        'module': 'resources.lib.channels.fr.kto'
    },
    'ouatchtv': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'ouatchtv.png'],
        'fanart': ['channels', 'fr', 'ouatchtv_fanart.jpg'],
        'module': 'resources.lib.channels.fr.ouatchtv'
    },
    'onzeo': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'onzeo.png'],
        'fanart': ['channels', 'fr', 'onzeo_fanart.jpg'],
        'module': 'resources.lib.channels.fr.onzeo'
    },
    'publicsenat': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'publicsenat.png'],
        'fanart': ['channels', 'fr', 'publicsenat_fanart.jpg'],
        'module': 'resources.lib.channels.fr.publicsenat'
    },
    'lcp': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'lcp.png'],
        'fanart': ['channels', 'fr', 'lcp_fanart.jpg'],
        'module': 'resources.lib.channels.fr.lcp'
    },
    'gameone': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'gameone.png'],
        'fanart': ['channels', 'fr', 'gameone_fanart.jpg'],
        'module': 'resources.lib.channels.fr.gameone'
    },
    'francetvsport': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'francetvsport.png'],
        'fanart': ['channels', 'fr', 'francetvsport_fanart.jpg'],
        'module': 'resources.lib.channels.fr.francetvsport'
    },
    'franceinfo': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'franceinfo.png'],
        'fanart': ['channels', 'fr', 'franceinfo_fanart.jpg'],
        'module': 'resources.lib.channels.fr.franceinfo'
    },
    'france3regions': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'france3regions.png'],
        'fanart': ['channels', 'fr', 'france3regions_fanart.jpg'],
        'module': 'resources.lib.channels.fr.france3regions'
    },
    'culturebox': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'culturebox.png'],
        'fanart': ['channels', 'fr', 'culturebox_fanart.jpg'],
        'module': 'resources.lib.channels.fr.culturebox'
    },
    'francetveducation': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'francetveducation.png'],
        'fanart': ['channels', 'fr', 'francetveducation_fanart.jpg'],
        'module': 'resources.lib.channels.fr.francetveducation'
    },
    'irl': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'irl.png'],
        'fanart': ['channels', 'fr', 'irl_fanart.jpg'],
        'module': 'resources.lib.channels.fr.nouvellesecritures'
    },
    'studio-4': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'studio-4.png'],
        'fanart': ['channels', 'fr', 'studio-4_fanart.jpg'],
        'module': 'resources.lib.channels.fr.nouvellesecritures'
    },
    'j_one': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'j_one.png'],
        'fanart': ['channels', 'fr', 'j_one_fanart.jpg'],
        'module': 'resources.lib.channels.fr.j_one'
    },
    'jack': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'jack.png'],
        'fanart': ['channels', 'fr', 'jack_fanart.jpg'],
        'module': 'resources.lib.channels.fr.jack'
    },
    'antennereunion': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'antennereunion.png'],
        'fanart': ['channels', 'fr', 'antennereunion_fanart.jpg'],
        'module': 'resources.lib.channels.fr.antennereunion'
    },
    'caledonia': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'caledonia.png'],
        'fanart': ['channels', 'fr', 'caledonia_fanart.jpg'],
        'module': 'resources.lib.channels.fr.caledonia'
    },
    'tebeo': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'fr', 'tebeo.png'],
        'fanart': ['channels', 'fr', 'tebeo_fanart.jpg'],
        'module': 'resources.lib.channels.fr.tebeo'
    }
}


UK_REPLAY = {
    'questod': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'uk', 'questod.png'],
        'fanart': ['channels', 'uk', 'questod_fanart.jpg'],
        'module': 'resources.lib.channels.uk.questod'
    },
    'blaze': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'uk', 'blaze.png'],
        'fanart': ['channels', 'uk', 'blaze_fanart.jpg'],
        'module': 'resources.lib.channels.uk.blaze'
    },
    'skynews': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'uk', 'skynews.png'],
        'fanart': ['channels', 'uk', 'skynews_fanart.jpg'],
        'module': 'resources.lib.channels.uk.sky'
    },
    'skysports': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'uk', 'skysports.png'],
        'fanart': ['channels', 'uk', 'skysports_fanart.jpg'],
        'module': 'resources.lib.channels.uk.sky'
    },
    'stv': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'uk', 'stv.png'],
        'fanart': ['channels', 'uk', 'stv_fanart.jpg'],
        'module': 'resources.lib.channels.uk.stv'
    }
}


BE_REPLAY = {
    'rtl_tvi': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'be', 'rtl_tvi.png'],
        'fanart': ['channels', 'be', 'rtl_tvi_fanart.jpg'],
        'module': 'resources.lib.channels.be.rtlplaybe'
    },
    'plug_rtl': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'be', 'plug_rtl.png'],
        'fanart': ['channels', 'be', 'plug_rtl_fanart.jpg'],
        'module': 'resources.lib.channels.be.rtlplaybe'
    },
    'club_rtl': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'be', 'club_rtl.png'],
        'fanart': ['channels', 'be', 'club_rtl_fanart.jpg'],
        'module': 'resources.lib.channels.be.rtlplaybe'
    },
    'rtl_info': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'be', 'rtl_info.png'],
        'fanart': ['channels', 'be', 'rtl_info_fanart.jpg'],
        'module': 'resources.lib.channels.be.rtlplaybe'
    },
    'bel_rtl': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'be', 'bel_rtl.png'],
        'fanart': ['channels', 'be', 'bel_rtl_fanart.jpg'],
        'module': 'resources.lib.channels.be.rtlplaybe'
    },
    'contact': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'be', 'contact.png'],
        'fanart': ['channels', 'be', 'contact_fanart.jpg'],
        'module': 'resources.lib.channels.be.rtlplaybe'
    },
    'rtl_sport': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'be', 'rtl_sport.png'],
        'fanart': ['channels', 'be', 'rtl_sport_fanart.jpg'],
        'module': 'resources.lib.channels.be.rtlplaybe'
    },
    'brf': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'be', 'brf.png'],
        'fanart': ['channels', 'be', 'brf_fanart.jpg'],
        'module': 'resources.lib.channels.be.brf'
    },
    'bx1': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'be', 'bx1.png'],
        'fanart': ['channels', 'be', 'bx1_fanart.jpg'],
        'module': 'resources.lib.channels.be.bx1'
    },
    'nrjhitstvbe': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'be', 'nrjhitstvbe.png'],
        'fanart': ['channels', 'be', 'nrjhitstvbe_fanart.jpg'],
        'module': 'resources.lib.channels.be.nrjhitstvbe'
    },
    'auvio': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'be', 'auvio.png'],
        'fanart': ['channels', 'be', 'auvio_fanart.jpg'],
        'module': 'resources.lib.channels.be.rtbf'
    },
    'rtc': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'be', 'rtc.png'],
        'fanart': ['channels', 'be', 'rtc_fanart.jpg'],
        'module': 'resources.lib.channels.be.rtc'
    },
    'telemb': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'be', 'telemb.png'],
        'fanart': ['channels', 'be', 'telemb_fanart.jpg'],
        'module': 'resources.lib.channels.be.telemb'
    },
    'tvlux': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'be', 'tvlux.png'],
        'fanart': ['channels', 'be', 'tvlux_fanart.jpg'],
        'module': 'resources.lib.channels.be.tvlux'
    },
    'vrt': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'be', 'vrt.png'],
        'fanart': ['channels', 'be', 'vrt_fanart.jpg'],
        'module': 'resources.lib.channels.be.vrt'
    }
}

WO_REPLAY = {
    'tv5mondeafrique': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'wo', 'tv5mondeafrique.png'],
        'fanart': ['channels', 'wo', 'tv5mondeafrique_fanart.jpg'],
        'module': 'resources.lib.channels.wo.tv5mondeafrique'
    },
    'tivi5monde': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'wo', 'tivi5monde.png'],
        'fanart': ['channels', 'wo', 'tivi5monde_fanart.jpg'],
        'module': 'resources.lib.channels.wo.tivi5monde'
    },
    'tv5monde': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'wo', 'tv5monde.png'],
        'fanart': ['channels', 'wo', 'tv5monde_fanart.jpg'],
        'module': 'resources.lib.channels.wo.tv5monde'
    },
    'arte': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'wo', 'arte.png'],
        'fanart': ['channels', 'wo', 'arte_fanart.jpg'],
        'module': 'resources.lib.channels.wo.arte'
    },
    'arirang': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'wo', 'arirang.png'],
        'fanart': ['channels', 'wo', 'arirang_fanart.jpg'],
        'module': 'resources.lib.channels.wo.arirang'
    },
    'afriquemedia': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'wo', 'afriquemedia.png'],
        'fanart': ['channels', 'wo', 'afriquemedia_fanart.jpg'],
        'module': 'resources.lib.channels.wo.afriquemedia'
    },
    'beinsports': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'wo', 'beinsports.png'],
        'fanart': ['channels', 'wo', 'beinsports_fanart.jpg'],
        'module': 'resources.lib.channels.wo.beinsports'
    },
    'bvn': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'wo', 'bvn.png'],
        'fanart': ['channels', 'wo', 'bvn_fanart.jpg'],
        'module': 'resources.lib.channels.wo.bvn'
    },
    'mtv': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'wo', 'mtv.png'],
        'fanart': ['channels', 'wo', 'mtv_fanart.jpg'],
        'module': 'resources.lib.channels.wo.mtv'
    },
    'nhkworld': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'wo', 'nhkworld.png'],
        'fanart': ['channels', 'wo', 'nhkworld_fanart.jpg'],
        'module': 'resources.lib.channels.wo.nhkworld'
    },
    'channelnewsasia': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'wo', 'channelnewsasia.png'],
        'fanart': ['channels', 'wo', 'channelnewsasia_fanart.jpg'],
        'module': 'resources.lib.channels.wo.channelnewsasia'
    },
    'france24': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'wo', 'france24.png'],
        'fanart': ['channels', 'wo', 'france24_fanart.jpg'],
        'module': 'resources.lib.channels.wo.france24'
    }
}

JP_REPLAY = {
    'tbsnews': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'jp', 'tbsnews.png'],
        'fanart': ['channels', 'jp', 'tbsnews_fanart.jpg'],
        'module': 'resources.lib.channels.jp.tbsnews'
    },
    'ntv': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'jp', 'ntv.png'],
        'fanart': ['channels', 'jp', 'ntv_fanart.jpg'],
        'module': 'resources.lib.channels.jp.tver'
    },
    'ex': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'jp', 'ex.png'],
        'fanart': ['channels', 'jp', 'ex_fanart.jpg'],
        'module': 'resources.lib.channels.jp.tver'
    },
    'tbs': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'jp', 'tbs.png'],
        'fanart': ['channels', 'jp', 'tbs_fanart.jpg'],
        'module': 'resources.lib.channels.jp.tver'
    },
    'tx': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'jp', 'tx.png'],
        'fanart': ['channels', 'jp', 'tx_fanart.jpg'],
        'module': 'resources.lib.channels.jp.tver'
    },
    'mbs': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'jp', 'mbs.png'],
        'fanart': ['channels', 'jp', 'mbs_fanart.jpg'],
        'module': 'resources.lib.channels.jp.tver'
    },
    'abc': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'jp', 'abc.png'],
        'fanart': ['channels', 'jp', 'abc_fanart.jpg'],
        'module': 'resources.lib.channels.jp.tver'
    },
    'ytv': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'jp', 'ytv.png'],
        'fanart': ['channels', 'jp', 'ytv_fanart.jpg'],
        'module': 'resources.lib.channels.jp.tver'
    },
    'nhknews': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'jp', 'nhknews.png'],
        'fanart': ['channels', 'jp', 'nhknews_fanart.jpg'],
        'module': 'resources.lib.channels.jp.nhknews'
    },
    'nhklifestyle': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'jp', 'nhklifestyle.png'],
        'fanart': ['channels', 'jp', 'nhklifestyle_fanart.jpg'],
        'module': 'resources.lib.channels.jp.nhklifestyle'
    }
}

CH_REPLAY = {
    'rts': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'ch', 'rts.png'],
        'fanart': ['channels', 'ch', 'rts_fanart.jpg'],
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'rsi': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'ch', 'rsi.png'],
        'fanart': ['channels', 'ch', 'rsi_fanart.jpg'],
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'srf': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'ch', 'srf.png'],
        'fanart': ['channels', 'ch', 'srf_fanart.jpg'],
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'rtr': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'ch', 'rtr.png'],
        'fanart': ['channels', 'ch', 'rtr_fanart.jpg'],
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'swissinfo': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'ch', 'swissinfo.png'],
        'fanart': ['channels', 'ch', 'swissinfo_fanart.jpg'],
        'module': 'resources.lib.channels.ch.srgssr'
    },
    'tvm3': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'ch', 'tvm3.png'],
        'fanart': ['channels', 'ch', 'tvm3_fanart.jpg'],
        'module': 'resources.lib.channels.ch.tvm3'
    },
    'becurioustv': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'ch', 'becurioustv.png'],
        'fanart': ['channels', 'ch', 'becurioustv_fanart.jpg'],
        'module': 'resources.lib.channels.ch.becurioustv'
    }
}

CA_REPLAY = {
    'tva': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'ca', 'tva.png'],
        'fanart': ['channels', 'ca', 'tva_fanart.jpg'],
        'module': 'resources.lib.channels.ca.tva'
    },
    'tv5': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'ca', 'tv5.png'],
        'fanart': ['channels', 'ca', 'tv5_fanart.jpg'],
        'module': 'resources.lib.channels.ca.tv5'
    },
    'unis': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'ca', 'unis.png'],
        'fanart': ['channels', 'ca', 'unis_fanart.jpg'],
        'module': 'resources.lib.channels.ca.unis'
    },
    'telequebec': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'ca', 'telequebec.png'],
        'fanart': ['channels', 'ca', 'telequebec_fanart.jpg'],
        'module': 'resources.lib.channels.ca.telequebec'
    },
    'icitoutv': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'ca', 'icitoutv.png'],
        'fanart': ['channels', 'ca', 'icitoutv_fanart.jpg'],
        'module': 'resources.lib.channels.ca.icitoutv'
    },
    'icitele': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'ca', 'icitele.png'],
        'fanart': ['channels', 'ca', 'icitele_fanart.jpg'],
        'module': 'resources.lib.channels.ca.icitele'
    }
}

US_REPLAY = {
    'tbd': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'us', 'tbd.png'],
        'fanart': ['channels', 'us', 'tbd_fanart.jpg'],
        'module': 'resources.lib.channels.us.tbd'
    },
    'nycmedia': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'us', 'nycmedia.png'],
        'fanart': ['channels', 'us', 'nycmedia_fanart.jpg'],
        'module': 'resources.lib.channels.us.nycmedia'
    },
    'abcnews': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'us', 'abcnews.png'],
        'fanart': ['channels', 'us', 'abcnews_fanart.jpg'],
        'module': 'resources.lib.channels.us.abcnews'
    }
}

ES_REPLAY = {
    'atresplayer': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'es', 'atresplayer.png'],
        'fanart': ['channels', 'es', 'atresplayer_fanart.jpg'],
        'module': 'resources.lib.channels.es.atresplayer'
    }
}

IT_REPLAY = {
    'la7': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'it', 'la7.png'],
        'fanart': ['channels', 'it', 'la7_fanart.jpg'],
        'module': 'resources.lib.channels.it.la7'
    },
    'la7d': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'it', 'la7d.png'],
        'fanart': ['channels', 'it', 'la7d_fanart.jpg'],
        'module': 'resources.lib.channels.it.la7'
    },
    'raiplay': {
        'callback': 'replay_bridge',
        'thumb': ['channels', 'it', 'raiplay.png'],
        'fanart': ['channels', 'it', 'raiplay_fanart.jpg'],
        'module': 'resources.lib.channels.it.raiplay'
    }
}

WEBSITES = {
    'allocine': {
        'callback': 'website_bridge',
        'thumb': ['websites', 'allocine.png'],
        'fanart': ['websites', 'allocine_fanart.jpg'],
        'module': 'resources.lib.websites.allocine'
    },
    'tetesaclaques': {
        'callback': 'website_bridge',
        'thumb': ['websites', 'tetesaclaques.png'],
        'fanart': ['websites', 'tetesaclaques_fanart.jpg'],
        'module': 'resources.lib.websites.tetesaclaques'
    },
    'taratata': {
        'callback': 'website_bridge',
        'thumb': ['websites', 'taratata.png'],
        'fanart': ['websites', 'taratata_fanart.jpg'],
        'module': 'resources.lib.websites.taratata'
    },
    'onf': {
        'callback': 'website_bridge',
        'thumb': ['websites', 'onf.png'],
        'fanart': ['websites', 'onf_fanart.jpg'],
        'module': 'resources.lib.websites.onf'
    },
    'nytimes': {
        'callback': 'website_bridge',
        'thumb': ['websites', 'nytimes.png'],
        'fanart': ['websites', 'nytimes_fanart.jpg'],
        'module': 'resources.lib.websites.nytimes'
    },
    'notrehistoirech': {
        'callback': 'website_bridge',
        'thumb': ['websites', 'notrehistoirech.png'],
        'fanart': ['websites', 'notrehistoirech_fanart.jpg'],
        'module': 'resources.lib.websites.notrehistoirech'
    },
    'noob': {
        'callback': 'website_bridge',
        'thumb': ['websites', 'noob.png'],
        'fanart': ['websites', 'noob_fanart.jpg'],
        'module': 'resources.lib.websites.noob'
    },
    'nfb': {
        'callback': 'website_bridge',
        'thumb': ['websites', 'nfb.png'],
        'fanart': ['websites', 'nfb_fanart.jpg'],
        'module': 'resources.lib.websites.nfb'
    },
    'ina': {
        'callback': 'website_bridge',
        'thumb': ['websites', 'ina.png'],
        'fanart': ['websites', 'ina_fanart.jpg'],
        'module': 'resources.lib.websites.ina'
    },
    'fosdem': {
        'callback': 'website_bridge',
        'thumb': ['websites', 'fosdem.png'],
        'fanart': ['websites', 'fosdem_fanart.jpg'],
        'module': 'resources.lib.websites.fosdem'
    },
    'elle': {
        'callback': 'website_bridge',
        'thumb': ['websites', 'elle.png'],
        'fanart': ['websites', 'elle_fanart.jpg'],
        'module': 'resources.lib.websites.elle'
    },
    'culturepub': {
        'callback': 'website_bridge',
        'thumb': ['websites', 'culturepub.png'],
        'fanart': ['websites', 'culturepub_fanart.jpg'],
        'module': 'resources.lib.websites.culturepub'
    },
    'autoplus': {
        'callback': 'website_bridge',
        'thumb': ['websites', 'autoplus.png'],
        'fanart': ['websites', 'autoplus_fanart.jpg'],
        'module': 'resources.lib.websites.autoplus'
    },
    '30millionsdamis': {
        'callback': 'website_bridge',
        'thumb': ['websites', '30millionsdamis.png'],
        'fanart': ['websites', '30millionsdamis_fanart.jpg'],
        'module': 'resources.lib.websites.30millionsdamis'
    },
    'marmiton': {
        'callback': 'website_bridge',
        'thumb': ['websites', 'marmiton.png'],
        'fanart': ['websites', 'marmiton_fanart.jpg'],
        'module': 'resources.lib.websites.marmiton'
    },
    'lesargonautes': {
        'callback': 'website_bridge',
        'thumb': ['websites', 'lesargonautes.png'],
        'fanart': ['websites', 'lesargonautes_fanart.jpg'],
        'module': 'resources.lib.websites.lesargonautes'
    }
}
