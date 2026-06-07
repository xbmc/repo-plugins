# -*- coding: utf-8 -*-
# Copyright: (c) 2022, darodi
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route
# noinspection PyUnresolvedReferences
from codequick.utils import urljoin_partial

from resources.lib import resolver_proxy

URL_ROOT = 'https://latele.ch/'
url_constructor = urljoin_partial(URL_ROOT)

URL_LIVE = url_constructor('live')
URL_LIVE_M3U8 = "https://latele2.vedge.infomaniak.com/livecast/latele2/manifest.m3u8"


@Route.register
def list_programs(plugin, item_id, **kwargs):
    # TODO
    return False


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    # TODO get m3u8 from URL_LIVE

    # headers = {
    #     "User-Agent": get_random_ua(),
    #     "Accept": "*/*",
    #     "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
    #     "Sec-Fetch-Dest": "empty",
    #     "Sec-Fetch-Mode": "cors",
    #     "Sec-Fetch-Site": "cross-site",
    #     "Pragma": "no-cache",
    #     "Cache-Control": "no-cache",
    #     "referrer": "https://latele.ch/"
    # }

    return resolver_proxy.get_stream_with_quality(plugin, video_url=URL_LIVE_M3U8, manifest_type="hls")
