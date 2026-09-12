# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import urlquick

from codequick import Resolver

from resources.lib import resolver_proxy, web_utils

SNRT_API = 'https://snrtlive.atlashoster.net/api/feeds-by-category'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_windows_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    params = {
        "lang": "fr",
        "category": 3,
    }
    json_data = urlquick.get(SNRT_API, params=params, headers=GENERIC_HEADERS, max_age=-1).json()
    for item in json_data:
        if item_id == str(item['id']):
            m3u8_url = item['url']
            return resolver_proxy.get_easybroadcast_m3u8_stream(plugin, m3u8_url, True)
    return None
