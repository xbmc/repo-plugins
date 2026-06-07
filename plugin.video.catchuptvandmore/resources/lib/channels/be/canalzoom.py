# -*- coding: utf-8 -*-
# Copyright: (c) 2022, darodi
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import re

import urlquick
# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route
# noinspection PyUnresolvedReferences
from codequick.utils import urljoin_partial

from resources.lib import resolver_proxy, web_utils

URL_ROOT = 'https://www.canalzoom.be/'
url_constructor = urljoin_partial(URL_ROOT)

URL_LIVE = url_constructor('direct')

URL_M3U8 = "https://tvlocales-live.freecaster.com/%s/%s.isml/master.m3u8"

# "live_token": "95d2e3af-5ab8-45a9-9dc9-f544d006b5d5",
PATTERN_TOKEN = re.compile(r'"live_token":\s*"(.*?)",')


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    headers = {
        'User-Agent': web_utils.get_random_ua()
    }

    resp = urlquick.get(URL_LIVE, headers=headers, max_age=-1)
    found_items = PATTERN_TOKEN.findall(resp.text)
    if len(found_items) == 0:
        return False
    token = found_items[0]
    url = URL_M3U8 % (token, token)
    return resolver_proxy.get_stream_with_quality(plugin, video_url=url, manifest_type="hls")
