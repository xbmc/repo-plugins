# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy, web_utils

# channel_name
URL_ROOT = 'http://www.%s.tn/'

# Live
URL_LIVE = URL_ROOT + 'البث-المباشر/محتوى'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_ua()}


# TODO
# Add Replay


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE % item_id, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()

    for link in root.iterfind('.//script'):
        source = link.get('src')
        if source is not None and 'global.js' in source:
            break

    resp = urlquick.get(source, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.text
    video_url = re.compile("source\: \'(.*?)\'").findall(root)[0]
    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url)
