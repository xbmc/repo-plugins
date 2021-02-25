# -*- coding: utf-8 -*-
"""
    Copyright (C) 2016-2020 Team Catch-up TV & More
    This file is part of Catch-up TV & More.
    SPDX-License-Identifier: GPL-2.0-or-later
"""

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals


from codequick import Route, Resolver, Listitem, utils, Script


from resources.lib import web_utils

import re
import urlquick

# TO DO
# Add Replay

URL_ROOT = 'https://www.telesambre.be'

URL_LIVE = URL_ROOT + '/direct'

URL_STREAM = 'https://telesambre.fcst.tv/player/embed/%s'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE, max_age=-1)
    live_id = re.compile(
        r'telesambre\.fcst\.tv\/player\/embed\/(.*?)\?').findall(resp.text)[0]
    resp2 = urlquick.get(URL_STREAM % live_id, max_age=-1)
    list_files = re.compile(
        r'file\"\:\"(.*?)\"').findall(resp2.text)
    url_stream = ''
    for stream_datas in list_files:
        if 'm3u8' in stream_datas:
            url_stream = stream_datas
    return url_stream + '|referer=https://telesambre.fcst.tv/'
