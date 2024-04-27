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

root = 'root'

menu = {
    'allocine': {
        'route': '/resources/lib/websites/allocine:website_root',
        'label': 'Allociné',
        'thumb': 'websites/allocine.png',
        'fanart': 'websites/allocine_fanart.jpg',
        'enabled': True,
        'order': 1
    },
    'tetesaclaques': {
        'route': '/resources/lib/websites/tetesaclaques:website_root',
        'label': 'Au pays des Têtes à claques',
        'thumb': 'websites/tetesaclaques.png',
        'fanart': 'websites/tetesaclaques_fanart.jpg',
        'enabled': True,
        'order': 2
    },
    'taratata': {
        'route': '/resources/lib/websites/taratata:website_root',
        'label': 'Taratata',
        'thumb': 'websites/taratata.png',
        'fanart': 'websites/taratata_fanart.jpg',
        'enabled': True,
        'order': 3
    },
    'noob': {
        'route': '/resources/lib/websites/noob:website_root',
        'label': 'Noob TV',
        'thumb': 'websites/noob.png',
        'fanart': 'websites/noob_fanart.jpg',
        'enabled': True,
        'order': 4
    },
    'culturepub': {
        'route': '/resources/lib/websites/culturepub:website_root',
        'label': 'Culturepub',
        'thumb': 'websites/culturepub.png',
        'fanart': 'websites/culturepub_fanart.jpg',
        'enabled': True,
        'order': 5
    },
    'autoplus': {
        'route': '/resources/lib/websites/autoplus:website_root',
        'label': 'Auto Plus',
        'thumb': 'websites/autoplus.png',
        'fanart': 'websites/autoplus_fanart.jpg',
        'enabled': True,
        'order': 6
    },
    'notrehistoirech': {
        'route': '/resources/lib/websites/notrehistoirech:website_root',
        'label': 'Notre Histoire',
        'thumb': 'websites/notrehistoirech.png',
        'fanart': 'websites/notrehistoirech_fanart.jpg',
        'enabled': True,
        'order': 7
    },
    '30millionsdamis': {
        'route': '/resources/lib/websites/30millionsdamis:website_root',
        'label': '30 Millions d\'Amis',
        'thumb': 'websites/30millionsdamis.png',
        'fanart': 'websites/30millionsdamis_fanart.jpg',
        'enabled': True,
        'order': 8
    },
    'elle': {
        'route': '/resources/lib/websites/elle:website_root',
        'label': 'Elle',
        'thumb': 'websites/elle.png',
        'fanart': 'websites/elle_fanart.jpg',
        'enabled': True,
        'order': 9
    },
    'ina': {
        'route': '/resources/lib/websites/ina:website_root',
        'label': 'Ina',
        'thumb': 'websites/ina.png',
        'fanart': 'websites/ina_fanart.jpg',
        'enabled': True,
        'order': 10
    },
    'marmiton': {
        'route': '/resources/lib/websites/marmiton:website_root',
        'label': 'Marmiton',
        'thumb': 'websites/marmiton.png',
        'fanart': 'websites/marmiton_fanart.jpg',
        'enabled': True,
        'order': 11
    },
    'fff': {
        'route': '/resources/lib/websites/fff:website_root',
        'label': 'FFF',
        'thumb': 'websites/nationalfff.png',
        'fanart': 'websites/nationalfff_fanart.jpg',
        'enabled': True,
        'order': 12
    },
    'philharmoniedeparis': {
        'route': '/resources/lib/websites/philharmoniedeparis:website_root',
        'label': 'Philharmonie de Paris',
        'thumb': 'websites/philharmoniedeparis.png',
        'fanart': 'websites/philharmoniedeparis_fanart.jpg',
        'enabled': True,
        'order': 13
    },
    'fosdem': {
        'route': '/resources/lib/websites/fosdem:website_root',
        'label': 'Fosdem',
        'thumb': 'websites/fosdem.png',
        'fanart': 'websites/fosdem_fanart.jpg',
        'enabled': True,
        'order': 14
    },
    'sonuma': {
        'route': '/resources/lib/websites/sonuma:website_root',
        'label': 'sonuma',
        'thumb': 'websites/sonuma.png',
        'fanart': 'websites/sonuma.png',
        'enabled': True,
        'order': 15
    },
    'veely': {
        'route': '/resources/lib/websites/veely:website_root',
        'label': 'veely',
        'thumb': 'websites/veely.png',
        'fanart': 'websites/veely.png',
        'enabled': True,
        'order': 16
    },
    'onf': {
        'route': '/resources/lib/websites/onf:website_root',
        'label': 'Office National du Film du Canada',
        'thumb': 'websites/onf.png',
        'fanart': 'websites/onf_fanart.jpg',
        'enabled': True,
        'order': 17
    },
    'nfb': {
        'route': '/resources/lib/websites/nfb:website_root',
        'label': 'National Film Board Of Canada',
        'thumb': 'websites/nfb.png',
        'fanart': 'websites/nfb_fanart.jpg',
        'enabled': True,
        'order': 18
    },
    'telequebec': {
        'route': '/resources/lib/websites/telequebec:website_root',
        'label': 'Squat Télé Québec',
        'thumb': 'websites/telequebec.png',
        'fanart': 'websites/telequebec_fanart.png',
        'enabled': True,
        'order': 19
    },
    'nytimes': {
        'route': '/resources/lib/websites/nytimes:website_root',
        'label': 'New York Times',
        'thumb': 'websites/nytimes.png',
        'fanart': 'websites/nytimes_fanart.jpg',
        'enabled': True,
        'order': 20
    }
}
