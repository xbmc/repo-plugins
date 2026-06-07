# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

# noinspection PyUnresolvedReferences
from codequick import Resolver

import urlquick
import json

from resources.lib import resolver_proxy, web_utils

# TODO
# Add Videos, Replays ?

URL_ROOT = 'https://news.ntv.co.jp'
URL_LIVE = URL_ROOT + '/live'
URL_TOKEN = URL_ROOT + '/api/generate-pta'
VIDEO_LIVE = 'https://n24-cdn-live-x.ntv.co.jp/ch01/index.m3u8'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    headers = {
        'referer': URL_LIVE,
        'User-Agent': web_utils.get_random_ua()
    }

    resp = urlquick.get(URL_TOKEN, headers=headers, max_age=-1)
    json_parser = json.loads(resp.text)
    pta = json_parser['pta']
    video_url = VIDEO_LIVE + '?pta=%s' % pta

    return resolver_proxy.get_stream_with_quality(plugin, video_url)
