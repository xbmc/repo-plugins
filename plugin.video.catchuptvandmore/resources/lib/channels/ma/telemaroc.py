
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
from urllib.parse import urlparse
from resources.lib import resolver_proxy, web_utils

from resources.lib.kodi_utils import get_params_in_query

URL_LIVES = 'https://www.telemaroc.tv/liveTV'

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    page_html = urlquick.get(URL_LIVES, headers=GENERIC_HEADERS, max_age=-1).text
    iframe_pattern = r'<iframe[^>]+src="(https://player\.restream\.io/\?token=[^"]+)"'
    iframe_match = re.search(iframe_pattern, page_html)
    if iframe_match:
        iframe_url = iframe_match.group(1)

        params = get_params_in_query(urlparse(iframe_url).query)

        video_urls = json.loads(
            urlquick.get('https://player-backend.restream.io/public/videos/' + params['token'], max_age=-1).text)

        return resolver_proxy.get_stream_with_quality(plugin, video_urls.get('videoUrl'))

    return None
