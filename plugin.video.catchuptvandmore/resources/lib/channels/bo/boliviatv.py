# -*- coding: utf-8 -*-
# Copyright: (c) 2024, JimmyGilles
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import re
import urlquick

from codequick import Resolver

from resources.lib import resolver_proxy, web_utils

URL_ROOT = 'https://www.boliviatv.bo/'
URL_LIVE = URL_ROOT + 'principal/vivo71.php'

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_LIVE, headers=GENERIC_HEADERS, max_age=-1)
    frame_url = resp.parse("iframe").get('src')

    video_id = re.search(r'video=(.*?)$', frame_url).group(1)

    return resolver_proxy.get_stream_dailymotion(plugin, video_id=video_id)
