# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver
from resources.lib import resolver_proxy, web_utils
import urlquick


# TO DO
# Add Replay

URL_ROOT = 'http://teleticino.ch'

# Live
URL_LIVE = URL_ROOT + '/diretta'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE, headers=GENERIC_HEADERS, max_age=-1)
    list_lives = re.compile(r'file":\s*"(.*?)"').findall(resp.text)
    for stream_datas in list_lives:
        if 'm3u8' in stream_datas:
            video_url = stream_datas
    return resolver_proxy.get_stream_with_quality(plugin, video_url)
