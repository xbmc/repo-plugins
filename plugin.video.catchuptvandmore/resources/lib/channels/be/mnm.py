# -*- coding: utf-8 -*-
# Copyright: (c) 2022, darodi
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import urlquick
# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route
# noinspection PyUnresolvedReferences
from codequick.utils import urljoin_partial

from resources.lib import resolver_proxy

API = urljoin_partial("https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v1/")


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    token = urlquick.post(API("tokens")).json()['vrtPlayerToken']
    resp_json = urlquick.get(API('videos/vualto_mnm?vrtPlayerToken=%s&client=mnm@PROD') % token).json()
    video_url = resp_json['targetUrls'][1]['url']
    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url, manifest_type="hls")
