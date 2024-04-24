# -*- coding: utf-8 -*-
# Copyright: (c) 2023, Joaopa
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json

# noinspection PyUnresolvedReferences
from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy, web_utils

# TODO
# Add Replay

URL_LIVE = "https://video.lefigaro.fr/"

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_LIVE, headers=GENERIC_HEADERS, max_age=-1)
    json_text = resp.parse().findall(".//script[@id='__NEXT_DATA__']")[0].text
    json_parser = json.loads(json_text)
    video_url = json_parser['runtimeConfig']['TNT_STREAM_URL']

    return resolver_proxy.get_stream_with_quality(plugin, video_url)
