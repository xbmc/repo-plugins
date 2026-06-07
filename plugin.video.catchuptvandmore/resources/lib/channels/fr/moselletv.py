# -*- coding: utf-8 -*-
# Copyright: (c) 2024, Joaopa
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver, Route
import urlquick

from resources.lib import resolver_proxy, web_utils


# TODO Add Replay

URL_ROOT = 'https://moselle.tv'

URL_LIVE = URL_ROOT + '/direct-tv/'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    live_html = urlquick.get(URL_LIVE, headers=GENERIC_HEADERS, max_age=-1)

    root = live_html.parse()
    for datas in root.iterfind('.//iframe'):
        if datas.get('src') is not None:
            creacast_url = datas.get('src')

    resp = urlquick.get(creacast_url, headers=GENERIC_HEADERS, max_age=-1)
    video_url = re.compile(r'file\: \"(.*?)\"').findall(resp.text)[0]

    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url)
