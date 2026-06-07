# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Joaopa
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More


from codequick import Listitem

# noinspection PyUnresolvedReferences
from codequick import Resolver

import urlquick
import json
from resources.lib import resolver_proxy, web_utils

# TODO
# Add Replay

URL_ROOT = "https://www.lrt.lt"

URL_API = URL_ROOT + "/servisai/stream_url/live/get_live_url.php?channel=%s"


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_API % item_id, headers={'User-Agent': web_utils.get_random_ua()}, max_age=-1).json()
    video_url = resp['response']['data']['content']

    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")
