# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re
import urlquick

# noinspection PyUnresolvedReferences
from codequick import Resolver

from resources.lib import resolver_proxy, web_utils

URL_LIVES = 'https://www.medi1tv.com/ar/live.aspx'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVES)
    for possibility in resp.parse().findall('.//iframe'):
        video_page = possibility.get('src')
        if item_id in video_page:
            resp2 = urlquick.get(video_page)
            video_url = 'http:' + re.compile(r"file: \'(.*?)\'").findall(resp2.text)[0]
            return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")
