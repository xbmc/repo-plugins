# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy, web_utils

# TODO
# Add Replay

URL_ROOT = "https://www.sportenfrance.com"
API_URL = 'https://apisef.mytvchain.com/public/api.php'

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    try:
        headers = {
            "User-Agent": web_utils.get_random_ua(),
            "referer": URL_ROOT
        }

        params = {
            'a': 'getVideos',
            'mode': 'live',
            'onair': 'yes',
            'reallyLive': 'false',
        }

        resp = urlquick.get(API_URL, headers=headers, params=params, max_age=-1)
        json_parser = resp.json()
        live_id = json_parser['videos'][0]['daily_id']

        return resolver_proxy.get_stream_dailymotion(plugin, live_id, embeder=URL_ROOT)

    except Exception:
        return resolver_proxy.get_stream_dailymotion(plugin, 'x8sayn8', embeder=URL_ROOT)
