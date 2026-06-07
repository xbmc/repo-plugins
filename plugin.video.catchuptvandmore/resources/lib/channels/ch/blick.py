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

URL_ROOT = 'https://www.blick.ch'
url_constructor = urljoin_partial(URL_ROOT)

URL_LIVE = url_constructor('/video/')

# "jwVideoId":"Z1UXIM6V"
ASSET_URL_PATTERN = re.compile(r'\"jwVideoId\":\"(.*?)\"')


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
    json_resp_api = urlquick.get("https://cdn.jwplayer.com/v2/media/%s" % asset_url_array[0], max_age=-1).json()
    if "playlist" not in json_resp_api:
        return False
    firs_element = json_resp_api["playlist"][0]
    if "VCH.M3U8" not in firs_element:
        return False
    resource_url = firs_element['VCH.M3U8']
    return resolver_proxy.get_stream_with_quality(plugin, video_url=resource_url, manifest_type="hls")
