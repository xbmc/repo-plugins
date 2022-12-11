# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Joaopa
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json

from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy, web_utils


# TODO
# Add Replay

URL_ROOT = "https://www.sudradio.fr/"


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    root = urlquick.get(URL_ROOT,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1).parse()
    try:
        live_id = root.find(".//div[@class='dailymotion-cpe']").get('video-id')
    except Exception:
        live_id = 'x75yzts'
    return resolver_proxy.get_stream_dailymotion(plugin, live_id, False)
