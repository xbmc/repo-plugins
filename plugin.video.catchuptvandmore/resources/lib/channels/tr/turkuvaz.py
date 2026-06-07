# -*- coding: utf-8 -*-
# Copyright: (c) 2022, itasli
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy, web_utils


URL_ROOT = 'https://www.atv.com.tr'

URL_LIVE = URL_ROOT + '/canli-yayin'

URL_LICENCE_KEY = "http://videotoken.tmgrup.com.tr/webtv/secure?url=http://trkvz-live.ercdn.net/%s/%s.m3u8"


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    headers = {"User-Agent": web_utils.get_random_ua(), 'Referer': URL_LIVE}

    resp = urlquick.get(URL_LICENCE_KEY % (item_id, item_id), headers=headers, max_age=-1)
    video_url = re.compile('\"Url\":\"(.*?)\"').findall(resp.text)[0]

    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls", headers=headers)
