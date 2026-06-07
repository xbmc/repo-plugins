# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

# noinspection PyUnresolvedReferences
from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy, web_utils

# TODO
# Add Replay

URL_LIVE = "https://www.sudouest.fr/lachainetv7/"

PATTERN_FILE = re.compile(r'live\":{\"src\":\"(.*?)\"')


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    video_page = None
    resp = urlquick.get(URL_LIVE, headers={"User-Agent": web_utils.get_random_ua()}, max_age=-1)
    for possibility in resp.parse().findall('.//iframe'):
        if possibility.get('allowfullscreen'):
            video_page = 'https:' + possibility.get('src')

    if video_page is None:
        return False

    # In a perfect world, digiteka extractor would not be broken in youtube-dl
    resp2 = urlquick.get(video_page, headers={"User-Agent": web_utils.get_random_ua()}, max_age=-1)
    found_files = PATTERN_FILE.findall(resp2.text)
    if len(found_files) == 0:
        return False

    video_url = found_files[0].replace("\\", "")
    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")
