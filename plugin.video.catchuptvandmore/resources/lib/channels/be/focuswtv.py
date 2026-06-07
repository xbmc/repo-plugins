# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

from codequick import Resolver
from resources.lib import resolver_proxy


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    headers = {
        'Referer': 'https://player.clevercast.com'
    }
    video_url = 'https://hls-origin01-focus-wtv.cdn01.rambla.be/main/adliveorigin-focus-wtv/_definst_/WqY7Y3.smil/playlist.m3u8'
    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url, headers=headers)
