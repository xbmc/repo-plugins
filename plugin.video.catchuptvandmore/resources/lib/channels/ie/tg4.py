# -*- coding: utf-8 -*-
# Copyright: (c) 2025
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import re
import urlquick
from codequick import Resolver

from resources.lib import resolver_proxy, web_utils

URL_ROOT = 'https://www.tg4.ie'

URL_LIVE = URL_ROOT + '/en/player/watch-live/home'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_windows_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    html_text = urlquick.get(URL_LIVE, headers=GENERIC_HEADERS, max_age=-1).text

    data_video_id = re.compile(r'VideoID = (.*?)\;').findall(html_text)[0]
    data_account = re.compile(r"data-account\'\, (.*?)\)").findall(html_text)[0]
    data_player = re.compile(r"data-player\'\, \'(.*?)\'").findall(html_text)[0]

    return resolver_proxy.get_brightcove_video_json(plugin, data_account, data_player, data_video_id)
