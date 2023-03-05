# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Script
import urlquick

from codequick import Listitem, Route
# noinspection PyUnresolvedReferences
from codequick import Resolver
from resources.lib import resolver_proxy, web_utils


# TODO
# Replay add emissions
# Add info LIVE TV

URL_ROOT = 'https://www.dw.com/de/live-tv/s-100817'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    channels = {"EN": "1", "AR": "2", "ES": "3", "DE": "5", "DE+": "4"}
    final_language = kwargs.get('language', Script.setting['dw.language'])
    channel = channels[final_language]

    resp = urlquick.get(URL_ROOT, headers={"User-Agent": web_utils.get_random_ua()}, max_age=-1)
    root = resp.parse()

    for video_data in root.iterfind('.//div[@class="mediaItem"]'):
        video_channel = video_data.get('data-channel-id')
        if video_channel == channel:
            video_url = video_data.find(".//source").get('src')

    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")
