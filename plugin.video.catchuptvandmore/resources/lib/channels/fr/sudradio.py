# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Joaopa
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re

from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy, web_utils


# TODO
# Add Replay

URL_ROOT = "https://www.sudradio.fr/"

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    try:
        root = urlquick.get(URL_ROOT, headers=GENERIC_HEADERS, max_age=-1).parse()
        video_link = root.find(".//iframe").get("data-src")
        live_id = re.compile(r'video\/(.*?)$').findall(video_link)[0]
    except Exception:
        live_id = 'x8jqxru'

    return resolver_proxy.get_stream_dailymotion(plugin, live_id, False)
