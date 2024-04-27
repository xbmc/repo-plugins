# -*- coding: utf-8 -*-
# Copyright: (c) 2022, joaopa
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

URL_LIVE = "https://panamericana.pe/tvenvivo/"


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_LIVE, headers={"User-Agent": web_utils.get_random_ua()}, max_age=-1)

    live_id = re.compile(r'video\: \"(.*?)\"').findall(resp.text)[0]
    print('live_id = %s' % live_id)
    return resolver_proxy.get_stream_dailymotion(plugin, live_id, False)
