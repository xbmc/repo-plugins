# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import os
import re

from codequick import Resolver
import urlquick

from resources.lib import web_utils


# TODO
# Add Replay

URL_ROOT = "http://www.biptv.tv"

URL_LIVE = URL_ROOT + "/direct.html"


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(
        URL_LIVE, headers={"User-Agent": web_utils.get_random_ua()}, max_age=-1)
    url_m3u8 = re.compile(r'source src=\"(.*?)\"').findall(resp.text)[0]
    root = os.path.dirname(url_m3u8)
    manifest = urlquick.get(
        url_m3u8,
        headers={'User-Agent': web_utils.get_random_ua()},
        max_age=-1)

    real_stream = ''
    lines = manifest.text.splitlines()
    for k in range(0, len(lines) - 1):
        if 'biptvstream_orig' in lines[k]:
            real_stream = root + '/' + lines[k]
    return real_stream
