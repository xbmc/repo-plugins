# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Joaopa
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re

from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy, web_utils

URL_ROOT = 'https://qvc.jp'

URL_LIVE = URL_ROOT + '/content/shop-live-tv.html'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_ua()}


# TODO
# Add Videos, Replays


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE, headers=GENERIC_HEADERS, max_age=-1)
    data_json = json.loads(re.compile(r'oLiveStreams\=(.*?)\,live').findall(resp.text)[0])

    video_url = 'https:' + data_json['QVC']['url']

    return resolver_proxy.get_stream_with_quality(plugin, video_url)
