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
    resp = urlquick.get(URL_ROOT, headers=GENERIC_HEADERS, max_age=-1)
    twitch_url = resp.parse().find('.//iframe').get('src')
    video_id = re.compile('channel=(.*?)\&').findall(twitch_url)[0]

    return resolver_proxy.get_stream_twitch(plugin, video_id)
