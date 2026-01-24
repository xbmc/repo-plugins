# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Joaopa
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re
import urlquick
import json

# noinspection PyUnresolvedReferences
from codequick import Resolver

from resources.lib import resolver_proxy, web_utils

URL_LIVE = 'https://play.mrt.com.mk/live'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_windows_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_LIVE, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse('ul', attrs={"class": "dropdown-menu"})
    for channel in root.iterfind('.//a'):
        if (channel.text) is not None and (channel.text == item_id):
            live_player_url = channel.get('href')
            break

    resp = urlquick.get(live_player_url, headers=GENERIC_HEADERS, max_age=-1)
    match = re.compile(r'gxArCurrPlaylist\s*=\s*(\[\[(.*?)\]\])', re.S).search(resp.text)
    data = json.loads(match.group(1))
    video_url = video_url = data[0][0]['src']

    return resolver_proxy.get_stream_with_quality(plugin, video_url)
