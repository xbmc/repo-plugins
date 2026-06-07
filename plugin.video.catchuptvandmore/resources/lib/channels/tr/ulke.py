# -*- coding: utf-8 -*-
# Copyright: (c) 2022, itasli
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy, web_utils


URL_ROOT = 'https://www.ulketv.com'

URL_LIVE = URL_ROOT + '/ulke-tv-canli-yayin'

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse("iframe", attrs={"allowfullscreen": ""})
    live_url = root.get('src')
    live_id = re.compile(r'embed/(.*?)\?').findall(live_url)[0]

    return resolver_proxy.get_stream_youtube(plugin, live_id)
