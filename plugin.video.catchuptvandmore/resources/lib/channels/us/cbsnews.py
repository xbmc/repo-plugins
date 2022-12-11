# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json

from codequick import Listitem, Route
# noinspection PyUnresolvedReferences
from codequick import Resolver
from resources.lib import resolver_proxy, web_utils

import urlquick


URL_ROOT = 'https://www.cbsnews.com'

# Live
URL_LIVE = URL_ROOT + '/live'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE)
    for line in resp.text.split('\n'):
        if "CBSNEWS.defaultPayload" in line:
            defaultPayload_line = line.replace('CBSNEWS.defaultPayload =', '')
            break

    jsonparser = json.loads(defaultPayload_line)

    video_url = jsonparser["items"][0]["video2"]
    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")
