# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver
import urlquick
import json

from resources.lib import resolver_proxy, web_utils

URL_ROOT = 'https://www.%s.fr'

URL_LIVE = URL_ROOT + '/ws/live/live'


# TODO
# Add Replay


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    try:
        resp = urlquick.get(URL_LIVE % item_id, headers={'User-Agent': web_utils.get_random_ua()}, max_age=-1)
        json_parser = json.loads(resp.text)
        live_id = json_parser['video']['dailymotionId']
    except Exception:
        # Links seem to be stable
        if item_id == 'funradio':
            live_id = 'xxtuy6'
        elif item_id == 'rtl':
            live_id = 'xl1km0'
        else:
            live_id = 'x2tzzpj'

    return resolver_proxy.get_stream_dailymotion(plugin, live_id, False)
