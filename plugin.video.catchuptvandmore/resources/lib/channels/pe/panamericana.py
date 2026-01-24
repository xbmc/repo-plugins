# -*- coding: utf-8 -*-
# Copyright: (c) 2022, joaopa
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re

# noinspection PyUnresolvedReferences
from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy, web_utils

# TODO
# Add Replay

URL_ROOT = 'https://panamericana.pe/'
URL_LIVE = URL_ROOT + 'tvenvivo'

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse("iframe", attrs={"allowfullscreen": None})
    live_api = root.get('src')
    resp = urlquick.get(live_api, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()
    for push in root.iterfind(".//script"):
        if (push.text is not None) and ('streamUrl' in push.text):
            match = re.search(r'"streamUrl":"([^"]+)"', push.text.replace('\\"', '"'))
            video_url = match.group(1)
            headers = {
                "User-Agent": web_utils.get_random_ua(),
                "Referer": "https://iblups.com"
            }

            return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url, sheaders=headers)
