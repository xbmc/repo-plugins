# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy, web_utils

# TO DO
# Replay add emissions

URL_LIVE = 'https://ntvplus.ca'

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()
    live_url = root.find('.//iframe').get('src')
    resp = urlquick.get(live_url, headers=GENERIC_HEADERS, max_age=-1)
    for url in re.compile(r'\"url\"\:\"(.*?)\"').findall(resp.text):
        if 'm3u8' in url and 'msoNum' not in url:
            video_url = url
    return resolver_proxy.get_stream_with_quality(plugin, video_url)
