# -*- coding: utf-8 -*-
# Copyright: (c) 2022, darodi
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

# noinspection PyUnresolvedReferences
from codequick import Resolver

# noinspection PyUnresolvedReferences
import urlquick

from resources.lib import resolver_proxy, web_utils

URL_ROOT = 'https://latele.ch/'
URL_LIVE = URL_ROOT + 'live'
URL_LIVE_M3U8 = 'https://latele2.vedge.infomaniak.com/livecast/ik:latele2/manifest.m3u8'

URL_BUILD = 'https://latele.ch/build/assets/'

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


# REPLAY TODO


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    try:
        resp = urlquick.get(URL_LIVE, headers=GENERIC_HEADERS, max_age=-1)
        root = resp.parse()

        for bundle in root.iterfind(".//script[@type='module']"):
            source = bundle.get('src')
            if (source is not None) and ('app-' in source):
                app_url = source

        resp = urlquick.get(app_url, headers=GENERIC_HEADERS, max_age=-1)
        root = resp.text
        available_assets = re.compile('assets\/(.+?)"').findall(root)

        for asset in available_assets:
            if 'LiveTV' in asset:
                live_bundle = URL_BUILD + asset

        resp = urlquick.get(live_bundle, headers=GENERIC_HEADERS, max_age=-1)
        root = resp.text
        match = re.search(r'file:"([^"]+)"', root)
        if match:
            video = match.group(1)

    except Exception:
        video = URL_LIVE_M3U8

    return resolver_proxy.get_stream_with_quality(plugin, video)
