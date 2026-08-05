# -*- coding: utf-8 -*-
# Copyright: (c) 2024, Joaopa
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver, Route
import urlquick

from resources.lib import resolver_proxy, web_utils


# TODO Add Replay

URL_ROOT = 'https://moselle.tv'

URL_LIVE = URL_ROOT + '/direct/'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    try:
        resp = urlquick.get(URL_LIVE, headers=GENERIC_HEADERS, max_age=-1)
        src = resp.parse("iframe").get('src')
        live_id = re.compile(r'video=(.*?)$').findall(src)[0]

    except Exception:
        live_id = 'x9lgbik'

    return resolver_proxy.get_stream_dailymotion(plugin, live_id, embeder=URL_ROOT)
