
# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re
import json
import urlquick

# noinspection PyUnresolvedReferences
from codequick import Resolver

from resources.lib import resolver_proxy, web_utils

URL_LIVES = 'https://www.telemaroc.tv/liveTV'
STREAM_INFO_URL = 'https://player-api.new.livestream.com/accounts/%s/events/%s/stream_info'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVES)
    accout_id = re.compile(
        r'\<iframe.*accounts\/(.*)\/events').findall(resp.text)[0]
    event_id = re.compile(
        r'\<iframe.*events\/(.*)\/player').findall(resp.text)[0]
    resp2 = urlquick.get(STREAM_INFO_URL % (accout_id, event_id))
    json_parser = json.loads(resp2.text)
    video_url = re.compile(r'(.*?)m3u8').findall(json_parser['secure_m3u8_url'])[0] + 'm3u8'

    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")
