# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Joaopa
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json

# noinspection PyUnresolvedReferences
from codequick import Resolver, Route
# noinspection PyUnresolvedReferences
import urlquick

from resources.lib import download, resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment

URL_ROOT = 'https://videos.tvmonaco.com/content/'

URL_LIVE_API = 'https://videos.tvmonaco.com/api/media/v7/media/le-direct'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    headers = {
        'User-Agent': web_utils.get_random_ua(),
        'Referer': URL_ROOT + 'le-direct'
    }
    resp = urlquick.get(URL_LIVE_API, headers=headers, max_age=-1)
    datas = json.loads(resp.text)
    video_url = datas['external_stream']['url']

    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url)
