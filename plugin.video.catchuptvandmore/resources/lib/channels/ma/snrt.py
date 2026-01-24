# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import urlquick

from codequick import Resolver

from resources.lib import resolver_proxy, web_utils

URL_ROOT = 'https://snrtlive.ma/'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_windows_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    url_live = URL_ROOT + 'fr/' + item_id
    resp = urlquick.get(url_live, headers=GENERIC_HEADERS, max_age=-1)
    url_easy_brodcast = resp.parse('iframe').get('src')

    return resolver_proxy.get_easybroadcast_stream(plugin, url=url_easy_brodcast)
