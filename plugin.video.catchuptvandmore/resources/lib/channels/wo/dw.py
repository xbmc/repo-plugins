# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto, 2024 darodi
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import re

import urlquick
# noinspection PyUnresolvedReferences
from codequick import Resolver
# noinspection PyUnresolvedReferences
from codequick import Script, Listitem, Route
# noinspection PyUnresolvedReferences
from codequick.utils import urljoin_partial

from resources.lib import resolver_proxy, web_utils

# TODO
# Replay add emissions
# Add info LIVE TV

URL_ROOT = 'https://www.dw.com'
url_constructor = urljoin_partial(URL_ROOT)

# <source src="https://dwamdstream102.akamaized.net/hls/live/2015525/dwstream102/index.m3u8"
PATTERN_M3U8 = re.compile(r'<source src=\"(.*?m3u8)\"')


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    channels = {
        "EN": "/en/live-tv/channel-english",
        "AR": "/ar/live-tv/channel-arabic",
        "ES": "/es/live-tv/channel-spanish",
        "FR": "/fr/live-tv/channel-english",
        "DE": "/de/live-tv/channel-english",
        "RU": "/ru/live-tv/channel-russian",
    }
    final_language = kwargs.get('language', Script.setting['dw.language'])
    channel = channels[final_language]
    url_live = url_constructor(channel)

    resp = urlquick.get(url_live, headers={"User-Agent": web_utils.get_random_ua()}, max_age=-1)
    m3u8_array = PATTERN_M3U8.findall(resp.text)
    if len(m3u8_array) == 0:
        return False

    return resolver_proxy.get_stream_with_quality(plugin, m3u8_array[0], manifest_type="hls")
