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
    'euronews': {
        'resolver': '/resources/lib/channels/wo/euronews:get_live_url',
        'label': 'Euronews',
        'thumb':
        'channels/wo/euronews.png',
        'fanart':
        'channels/wo/euronews_fanart.jpg',
        'available_languages': {
            'FR': {
                'xmltv_id': 'C140.api.telerama.fr'
            },
            'EN': {
                'xmltv_id': '140.tvguide.co.uk'
            },
            'AR': {}, 'DE': {},
            'IT': {
                'xmltv_id': 'euronews.rai.it'
            },
            'ES': {},
            'PT': {},
            'RU': {},
            'RO': {},
            'TR': {},
            'FA': {},
            'GR': {},
            'HU': {},
            'BG': {}
        },
        'enabled': True,
        'order': 1
    },
    'arte': {
        'resolver': '/resources/lib/channels/wo/arte:get_live_url',
        'label': 'Arte',
        'thumb': 'channels/wo/arte.png',
        'fanart': 'channels/wo/arte_fanart.jpg',
        'available_languages': {
            'FR': {
                'xmltv_id': 'C111.api.telerama.fr',
                'm3u_group': 'France TNT',
                'm3u_order': 7
            },
            'DE': {}
        },
        'enabled': True,
        'order': 2
    },
    'france24': {
        'resolver': '/resources/lib/channels/wo/france24:get_live_url',
        'label': 'France 24',
        'thumb': 'channels/wo/france24.png',
        'fanart': 'channels/wo/france24_fanart.jpg',
        'available_languages': {
            'FR': {
                'xmltv_id': 'C529.api.telerama.fr'
            },
            'EN': {
                'xmltv_id': '1183.tvguide.co.uk'
            },
            'AR': {}, 'ES': {}
        },
        'enabled': True,
        'order': 3
    },
    'nhkworld': {
        'resolver': '/resources/lib/channels/wo/nhkworld:get_live_url',
        'label': 'NHK World',
        'thumb': 'channels/wo/nhkworld.png',
        'fanart': 'channels/wo/nhkworld_fanart.jpg',
        'available_languages': {'Outside Japan': {}, 'In Japan': {}},
        'enabled': True,
        'order': 4
    },
    'tivi5monde': {
        'resolver': '/resources/lib/channels/wo/tivi5monde:get_live_url',
        'label': 'Tivi 5Monde',
        'thumb': 'channels/wo/tivi5monde.png',
        'fanart': 'channels/wo/tivi5monde_fanart.jpg',
        'enabled': True,
        'order': 5
    },
    'bvn': {
        'resolver': '/resources/lib/channels/wo/bvn:get_live_url',
        'label': 'BVN',
        'thumb': 'channels/wo/bvn.png',
        'fanart': 'channels/wo/bvn_fanart.jpg',
        'enabled': True,
        'order': 6
    },
    'icitelevision': {
        'resolver': '/resources/lib/channels/wo/icitelevision:get_live_url',
        'label': 'ICI Télévision',
        'thumb': 'channels/wo/icitelevision.png',
        'fanart': 'channels/wo/icitelevision_fanart.jpg',
        'enabled': True,
        'order': 7
    },
    'arirang': {
        'resolver': '/resources/lib/channels/wo/arirang:get_live_url',
        'label': 'Arirang (아리랑)',
        'thumb': 'channels/wo/arirang.png',
        'fanart': 'channels/wo/arirang_fanart.jpg',
        'enabled': True,
        'order': 8
    },
    'dw': {
        'resolver': '/resources/lib/channels/wo/dw:get_live_url',
        'label': 'DW',
        'thumb': 'channels/wo/dw.png',
        'fanart': 'channels/wo/dw_fanart.jpg',
        'available_languages': {
            'EN': {'xmltv_id': 'C61.api.telerama.fr'},
            'AR': {}, 'ES': {}, 'DE': {}
        },
        'enabled': True,
        'order': 9
    },
    'eptw': {
        'resolver': '/resources/lib/channels/wo/eptworld:get_live_url',
        'label': 'EPT World',
        'thumb': 'channels/wo/eptworld.png',
        'fanart': 'channels/wo/eptworld.png',
        'enabled': True,
        'order': 10
    },
    'qvc': {
        'resolver': '/resources/lib/channels/wo/qvc:get_live_url',
        'label': 'QVC',
        'thumb': 'channels/wo/qvc.png',
        'fanart': 'channels/wo/qvc_fanart.jpg',
        'available_languages': {'JP': {}, 'DE': {}, 'IT': {}, 'UK': {}, 'US': {}},
        'enabled': True,
        'order': 11
    },
    'cgtn': {
        'resolver': '/resources/lib/channels/wo/cgtn:get_live_url',
        'label': 'CGTN',
        'thumb': 'channels/wo/cgtn.png',
        'fanart': 'channels/wo/cgtn_fanart.jpg',
        'available_languages': {'FR': {}, 'EN': {}, 'AR': {}, 'ES': {}, 'RU': {}},
        'enabled': True,
        'order': 12
    },
    'cgtndocumentary': {
        'resolver': '/resources/lib/channels/wo/cgtn:get_live_url',
        'label': 'CGTN Documentary',
        'thumb': 'channels/wo/cgtndocumentary.png',
        'fanart': 'channels/wo/cgtndocumentary_fanart.jpg',
        'enabled': True,
        'order': 13
    },
    'afriquemedia': {
        'resolver': '/resources/lib/channels/wo/afriquemedia:get_live_url',
        'label': 'Afrique Media',
        'thumb': 'channels/wo/afriquemedia.png',
        'fanart': 'channels/wo/afriquemedia_fanart.jpg',
        'enabled': True,
        'order': 14
    },
    'tv5mondefbs': {
        'resolver': '/resources/lib/channels/wo/tv5monde:get_live_url',
        'label': 'TV5Monde France Belgique Suisse',
        'thumb': 'channels/wo/tv5mondefbs.png',
        'fanart': 'channels/wo/tv5mondefbs_fanart.jpg',
        'xmltv_id': 'C205.api.telerama.fr',
        'enabled': True,
        'order': 15
    },
    'tv5mondeinfo': {
        'resolver': '/resources/lib/channels/wo/tv5monde:get_live_url',
        'label': 'TV5Monde Info',
        'thumb': 'channels/wo/tv5mondeinfo.png',
        'fanart': 'channels/wo/tv5mondeinfo_fanart.jpg',
        'enabled': True,
        'order': 16
    },
    'channelnewsasia': {
        'resolver': '/resources/lib/channels/wo/channelnewsasia:get_live_url',
        'label': 'Channel NewsAsia',
        'thumb': 'channels/wo/channelnewsasia.png',
        'fanart': 'channels/wo/channelnewsasia_fanart.jpg',
        'enabled': True,
        'order': 17
    },
    'rt': {
        'resolver': '/resources/lib/channels/wo/rt:get_live_url',
        'label': 'RT',
        'thumb': 'channels/wo/rt.png',
        'fanart': 'channels/wo/rt_fanart.jpg',
        'available_languages': {
            'FR': {},
            'EN': {
                'xmltv_id': '853.tvguide.co.uk'
            },
            'AR': {}, 'ES': {}
        },
        'enabled': True,
        'order': 18
    },
    'africa24': {
        'resolver': '/resources/lib/channels/wo/africa24:get_live_url',
        'label': 'Africa 24',
        'thumb': 'channels/wo/africa24.png',
        'fanart': 'channels/wo/africa24_fanart.jpg',
        'enabled': True,
        'order': 19
    },
    'aljazeera': {
        'resolver': '/resources/lib/channels/wo/aljazeera:get_live_url',
        'label': 'Aljazeera',
        'thumb': 'channels/wo/aljazeera.png',
        'fanart': 'channels/wo/aljazeera_fanart.png',
        'enabled': True,
        'order': 20
    }
}
