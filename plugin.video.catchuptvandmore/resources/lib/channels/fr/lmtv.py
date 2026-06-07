# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Listitem, Resolver
import urlquick

from resources.lib import resolver_proxy, web_utils


# TO DO
# Rework Date/AIred
URL_ROOT = 'https://lmtv.fr/'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    try:
        resp = urlquick.get(URL_ROOT, headers=GENERIC_HEADERS, max_age=-1)
        root = resp.parse("iframe", attrs={"allowfullscreen": None})
        live_url = root.get('src')
        live_id = re.compile(r'embed/(.*?)\?').findall(live_url)[0]
    except Exception:
        live_id = 'r1mbPY0BlYk'

    return resolver_proxy.get_stream_youtube(plugin, live_id)
