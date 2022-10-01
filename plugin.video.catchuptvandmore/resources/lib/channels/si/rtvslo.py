# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

# noinspection PyUnresolvedReferences
from codequick import Resolver

from resources.lib import resolver_proxy, web_utils


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    m3u8 = {
        'slo1': 'https://31-rtvslo-tv-slo1-int.cdn.eurovisioncdn.net/playlist.m3u8',
        'slo2': 'https://21-rtvslo-tv-slo2-int.cdn.eurovisioncdn.net/playlist.m3u8',
        'slo3': 'https://16-rtvslo-tv-slo3-int.cdn.eurovisioncdn.net/playlist.m3u8',
        'koper': 'https://27-rtvslo-tv-kp-int.cdn.eurovisioncdn.net/playlist.m3u8',
        'maribor': 'https://25-rtvslo-tv-mb-int.cdn.eurovisioncdn.net/playlist.m3u8',
        'mmc': 'https://29-rtvslo-tv-mmc-int.cdn.eurovisioncdn.net/playlist.m3u8'
    }

    video_url = m3u8[item_id]
    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")
