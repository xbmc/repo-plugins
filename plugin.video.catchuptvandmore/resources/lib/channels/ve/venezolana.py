# -*- coding: utf-8 -*-
# Copyright: (c) 2022, joaopa
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

URL_ROOT = 'https://www.vtv.gob.ve'
URL_LIVE = URL_ROOT + '/en-vivo/'


@Resolver.register
def get_live_url(plugin, item_id, download_mode=False, **kwargs):
    try:
        resp = urlquick.get(URL_LIVE, headers={'User-Agent': web_utils.get_random_ua()}, max_age=-1)
        root = resp.parse()
        video_url = root.find(".//iframe").get('src')
        video_id = re.compiler(r'embed\/video\/(.*?)\?').findall(video_url)[0]
    except Exception:
        video_id = 'x828i6j'

    return resolver_proxy.get_stream_dailymotion(plugin, video_id, download_mode)
