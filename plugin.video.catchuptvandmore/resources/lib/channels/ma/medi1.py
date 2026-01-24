# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re
import urlquick

# noinspection PyUnresolvedReferences
from codequick import Resolver

from resources.lib import resolver_proxy, web_utils

URL_API = 'https://idara.medi1tv.ma/rss/medi1tv/live.aspx'

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    streams = json.loads(
        urlquick.get(URL_API, headers=GENERIC_HEADERS, max_age=-1).text)
    for stream in streams:
        if stream.get('titre') == item_id:
            return resolver_proxy.get_easybroadcast_stream(plugin, stream.get('link'))
