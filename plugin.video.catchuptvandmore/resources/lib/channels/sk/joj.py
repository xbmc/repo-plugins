# -*- coding: utf-8 -*-
# Copyright: (c) 2022, darodi
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import re

import urlquick
# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route, Script
# noinspection PyUnresolvedReferences
from codequick.utils import urljoin_partial, strip_tags

from resources.lib import resolver_proxy

URL_ROOT = {
    "joj": 'https://live.joj.sk/',
    "jojplus": 'https://plus.joj.sk/live/',
    "jojwau": 'https://wau.joj.sk/live/',
    "jojfamily": "https://jojfamily.blesk.cz/live"
}

# <iframe src="https://media.joj.sk/embed/IONkX5a3Bl4?autoplay=1"
PATTERN_EMBEDDED_FRAME = re.compile(r'<iframe src="(https://media.joj.sk/embed/[^"]*)"')

# var src = {
#     "hls": "https://live.cdn.joj.sk/live/joj-index.m3u8?
#     loc=AT&exp=1654031713&hash=b0bd41113cbef77e4a9db805b98ac126e073d8300c984c73355c8f7a445cce77"
# };
PATTERN_M3U8 = re.compile(r'var src = {\s*\"hls\":\s*\"(http.*.m3u8.*)\"')


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    url_root = URL_ROOT[item_id]
    if url_root is None:
        return False

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-User": "?1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "referrer": url_root
    }

    resp = urlquick.get(url_root, headers=headers, max_age=-1)
    frame_url = PATTERN_EMBEDDED_FRAME.findall(resp.text)
    if len(frame_url) == 0:
        return False

    player_url = frame_url[0]
    resp2 = urlquick.get(player_url, max_age=-1)
    m3u8_array = PATTERN_M3U8.findall(resp2.text)
    if len(m3u8_array) == 0:
        plugin.notify(plugin.localize(30600), plugin.localize(30716) + " - " + resp2.parse().findtext(".//h2"))
        return False
    video_url = m3u8_array[0]

    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url, manifest_type="hls")
