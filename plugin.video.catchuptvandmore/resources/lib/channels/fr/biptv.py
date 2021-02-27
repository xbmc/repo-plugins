# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2019  SylvainCecchetto

    This file is part of Catch-up TV & More.

    Catch-up TV & More is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Catch-up TV & More is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with Catch-up TV & More; if not, write to the Free Software Foundation,
    Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

from codequick import Route, Resolver, Listitem, utils, Script


from resources.lib import web_utils
from resources.lib.menu_utils import item_post_treatment

import os
import re
import urlquick

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
