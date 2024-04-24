# -*- coding: utf-8 -*-
# Copyright: (c) 2023, Joaopa
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json

from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment

URL_ROOT = 'https://play.rtl.lu'
URL_LIVE = URL_ROOT + '/live'

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_LIVE, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()
    data = root.find('.//script[@id="__NEXT_DATA__"]').text
    data_json = json.loads(data)
    livestreams = data_json['props']['pageProps']['initialState']['data']['livestreams']['active']['items']
    for channel in livestreams:
        if channel['channel_id'] == item_id:
            if channel['video_playback'] is not None:
                video_url = channel['video_playback']
            else:
                video_url = channel['audio_playback']['hls']

    return resolver_proxy.get_stream_with_quality(plugin, video_url)
