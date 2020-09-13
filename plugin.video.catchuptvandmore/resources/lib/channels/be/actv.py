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

import re
import urlquick
# Working for Python 2/3
try:
    from urllib.parse import unquote_plus
except ImportError:
    from urllib import unquote_plus

# TO DO
# Add Replay

URL_ROOT = 'https://www.antennecentre.tv'

URL_LIVE = URL_ROOT + '/direct'

URL_STREAM = 'https://actv.fcst.tv/player/embed/%s'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE, max_age=-1)
    live_id = re.compile(
        r'actv\.fcst\.tv\/player\/embed\/(.*?)\?').findall(resp.text)[0]
    resp2 = urlquick.get(URL_STREAM % live_id, max_age=-1)
    list_files = re.compile(
        r'file\"\:\"(.*?)\"').findall(resp2.text)
    url_stream = ''
    for stream_datas in list_files:
        if 'm3u8' in stream_datas:
            url_stream = stream_datas
    return url_stream
