# -*- coding: utf-8 -*-
# Copyright: (c) 2025
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import re
import urlquick
from codequick import Resolver

from resources.lib import resolver_proxy, web_utils

URL_ROOT = 'https://cula4.com'

URL_LIVE = URL_ROOT + '/live'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_windows_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    html_text = urlquick.get(URL_LIVE, headers=GENERIC_HEADERS, max_age=-1).text

    data_video_id = re.search(r'videoId\s*:\s*"(\d+)"', html_text).group(1)
    data_account = re.search(r'accountId\s*:\s*"(\d+)"', html_text).group(1)
    data_player = re.search(r'playerId\s*:\s*"([^"]+)"', html_text).group(1)

    headers = {
        'origin': URL_ROOT,
        'referer': URL_ROOT
    }
    return resolver_proxy.get_brightcove_video_json(plugin, data_account, data_player, data_video_id, headers=headers)
