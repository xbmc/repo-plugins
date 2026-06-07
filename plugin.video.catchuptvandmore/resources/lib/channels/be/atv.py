# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

# noinspection PyUnresolvedReferences
from codequick import Resolver

from resources.lib import resolver_proxy

URL_LIVE_STREAM = 'https://live.zendzend.com/cmaf/29375_107244/master.m3u8?HLS_version=ts'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    return resolver_proxy.get_stream_with_quality(plugin, video_url=URL_LIVE_STREAM, manifest_type="hls")
