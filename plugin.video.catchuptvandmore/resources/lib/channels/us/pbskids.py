# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json

import urlquick

# noinspection PyUnresolvedReferences
from codequick import Resolver

from resources.lib import resolver_proxy, web_utils

# TODO
# Add replay

URL_ROOT = 'https://pbskids.org'

# Live
URL_LIVE = URL_ROOT + '/api/video/v1/livestream?station=KIDS'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE)
    json_parser = json.loads(resp.text)
    video_url = json_parser["livestream_drm"]["non_drm_url"]

    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")
