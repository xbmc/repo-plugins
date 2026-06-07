# -*- coding: utf-8 -*-
# Copyright: (c) 2024, JimmyGilles
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import re

import urlquick
# noinspection PyUnresolvedReferences
from codequick import Resolver, Route
# noinspection PyUnresolvedReferences
from codequick.utils import urljoin_partial

from resources.lib import resolver_proxy, web_utils

URL_ROOT = 'https://www.atb.com.bo/'
url_constructor = urljoin_partial(URL_ROOT)
URL_LIVE = url_constructor('atb-en-vivo/')

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_LIVE, headers=GENERIC_HEADERS, max_age=-1)
    try:
        dailymotion_url = resp.parse().find(".//meta[@itemprop='embedUrl']").get('content')
        live_id = re.compile(r'video\/(.*?)$').findall(dailymotion_url)[0]
    except Exception:
        live_id = 'x84eirw'

    return resolver_proxy.get_stream_dailymotion(plugin, live_id, False)
