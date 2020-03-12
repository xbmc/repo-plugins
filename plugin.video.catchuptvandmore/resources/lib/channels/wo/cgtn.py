# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2018  SylvainCecchetto

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

from resources.lib.labels import LABELS
from resources.lib import web_utils

import urlquick

# TO DO

# Live
# https://www.cgtn.com/public/bundle/js/live.js
URL_LIVE_CGTN = 'https://news.cgtn.com/resource/live/%s/cgtn-%s.m3u8'
# Channel (FR|ES|AR|EN|RU|DO(documentary))


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def get_live_url(plugin, item_id, video_id, **kwargs):
    final_language = kwargs.get('language', Script.setting['cgtn.language'])

    if item_id == 'cgtndocumentary':
        stream_url = URL_LIVE_CGTN % ('document', 'doc')
    else:
        if final_language == 'FR':
            stream_url = URL_LIVE_CGTN % ('french', 'f')
        elif final_language == 'EN':
            stream_url = URL_LIVE_CGTN % ('english', 'news')
        elif final_language == 'AR':
            stream_url = URL_LIVE_CGTN % ('arabic', 'r')
        elif final_language == 'ES':
            stream_url = URL_LIVE_CGTN % ('espanol', 'e')
        elif final_language == 'RU':
            stream_url = URL_LIVE_CGTN % ('russian', 'r')
    return stream_url
