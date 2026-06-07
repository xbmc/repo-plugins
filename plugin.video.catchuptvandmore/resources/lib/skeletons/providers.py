# -*- coding: utf-8 -*-
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

root = 'root'

menu = {
    'sfrtv': {
        'route': '/resources/lib/providers/sfrtv:provider_root',
        'list_channels_function': 'resources.lib.providers.sfrtv:list_live_channels',
        'label': 'SFR TV',
        'thumb': 'providers/sfrtv.png',
        'fanart': 'providers/sfrtv_fanart.jpg',
        'enabled': True,
        'order': 1
    }
}
