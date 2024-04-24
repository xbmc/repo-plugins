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

URL_LIVE = 'https://www.ert.gr/webtv/ert/tv/live-glm/%s.html'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    channel = {"ept1": "ert1", "ept2": "ert2", "ept3": "ert3", "eptnews": "ert-news", "eptsport": "ert-sports"}

    resp = urlquick.get(URL_LIVE % (channel[item_id]), headers={"User-Agent": web_utils.get_random_ua()}, max_age=-1)
    video_url = re.compile(r"var stream    = \'(.*?)\'").findall(resp.text)[0]

    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")
