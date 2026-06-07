# -*- coding: utf-8 -*-
# Copyright: (c) 2022, darodi
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import re

import urlquick
# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route
# noinspection PyUnresolvedReferences
from codequick.utils import urljoin_partial

from resources.lib import resolver_proxy

URL_ROOT = 'https://drita.tv'
url_constructor = urljoin_partial(URL_ROOT)

URL_LIVE = url_constructor('/live-tv/')

#  {"dataProvider":{"source":[{"url":"https:\/\/protokolldns.xyz\/dritaweb5587989\/index.m3u8"}
ASSET_URL_PATTERN = re.compile('{"dataProvider":\\{"source":\\[\\{"url":"(.*?)"}')


@Route.register
def list_programs(plugin, item_id, **kwargs):
    # TODO
    return False


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_LIVE, max_age=-1)
    asset_url_array = ASSET_URL_PATTERN.findall(resp.text)
    if len(asset_url_array) == 0:
        return False
    video_url = re.sub('\\\\/', '/', asset_url_array[0])
    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url, manifest_type="hls")
