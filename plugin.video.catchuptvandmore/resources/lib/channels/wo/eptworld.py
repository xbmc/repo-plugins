# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Joaopa
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy, web_utils


# TO DO
# Add Replay

URL_LIVE = 'https://ept-live-bcbs15228.siliconweb.com/media/%s/%s.m3u8'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    channel = {"eptw": "ert_1"}

    resp = urlquick.get(URL_LIVE % (channel[item_id], channel[item_id]), headers={"User-Agent": web_utils.get_random_ua()}, max_age=-1)
    live_id = re.compile(r"var streamww = \'(.*?)\'").findall(resp.text)[0]

    return resolver_proxy.get_quality(plugin, live_id)
