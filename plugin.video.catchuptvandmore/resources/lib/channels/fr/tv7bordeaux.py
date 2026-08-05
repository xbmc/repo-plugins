# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

# noinspection PyUnresolvedReferences
from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy, web_utils

# TODO
# Add Replay

URL_LIVE = "https://www.sudouest.fr/lachainetv7/"

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    video_page = None
    resp = urlquick.get(URL_LIVE, headers=GENERIC_HEADERS, max_age=-1)
    for possibility in resp.parse().findall('.//iframe'):
        if possibility.get('allowfullscreen'):
            video_page = possibility.get('src')
            resp = urlquick.get(video_page, headers=GENERIC_HEADERS, max_age=-1)
            video_id = re.compile(r'video_id\":\"(.*?)\"').findall(resp.text)[0]
            return resolver_proxy.get_stream_youtube(plugin, video_id)
