# -*- coding: utf-8 -*-
# Copyright: (c) 2022, itasli
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

from codequick import Resolver

from resources.lib import resolver_proxy


URL_LIVE = 'https://tv-%s.medya.trt.com.tr/master.m3u8'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    video_url = URL_LIVE % item_id

    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")
