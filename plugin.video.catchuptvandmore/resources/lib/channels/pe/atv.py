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

URL_LIVE = "https://www.atv.pe/envivo-%s"


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE % item_id, headers={'User-Agent': web_utils.get_random_ua()}, max_age=-1)
    video_url = re.compile(r"var LIVE_URL \= \'(.*?)\'").findall(resp.text)[0]

    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")
