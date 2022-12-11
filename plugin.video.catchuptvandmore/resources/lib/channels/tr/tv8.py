# -*- coding: utf-8 -*-
# Copyright: (c) 2022, itasli
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy


URL_ROOT = 'https://www.tv8.com.tr'

URL_LIVE = URL_ROOT + '/canli-yayin'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE)
    video_url = re.compile('file: \"(.*?)\"').findall(resp.text)[0]
    live_url = "https://tv8-tb-live.ercdn.net/tv8-geo/"

    resp = urlquick.get(video_url)

    if item_id == "tv8":
        tokens = re.compile('(\?.*)').findall(resp.text)[0]
        video_url = live_url + "tv8hd.m3u8" + tokens
    elif item_id == "tv8int":
        tokens = re.compile('(\?.*)').findall(resp.text)[0]
        video_url = live_url + "tv8int.m3u8" + tokens

    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")
