# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy, web_utils


# TODO
# Add Replay

URL_ROOT = "https://www.europe1.fr/"

URL_LIVE = URL_ROOT + 'direct-video'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_windows_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    try:
        resp = urlquick.get(URL_LIVE, headers=GENERIC_HEADERS, max_age=-1)
        root = resp.parse()
        live_id = root.find(".//div[@data-muted='true']").get('data-videoid')

    except Exception:
        live_id = 'xqjkfz'

    return resolver_proxy.get_stream_dailymotion(plugin, live_id, embeder=URL_ROOT)
