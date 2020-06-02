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

from resources.lib.codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment

import re
from resources.lib import urlquick

# TO DO
# Add Replay

# Live
URL_ROOT = 'http://www.%s.tn'
# channel_name


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def get_live_url(plugin, item_id, video_id, **kwargs):

    resp = urlquick.get(URL_ROOT % item_id)
    root = resp.parse()

    if root.find(".//section[@id='block-block-2']") is not None:
        live_url = root.find(".//section[@id='block-block-2']").findall(
            './/a')[0].get('href')
    else:
        live_url = root.find(".//section[@id='block-block-4']").findall(
            './/a')[0].get('href')
    live_html = urlquick.get(live_url)
    live_id_channel = re.compile('www.youtube.com/embed/(.*?)\"').findall(
        live_html.text)[1]
    live_youtube_html = urlquick.get('https://www.youtube.com/embed/' +
                                     live_id_channel)
    live_id = re.compile('\'VIDEO_ID\'\: \"(.*?)\"').findall(
        live_youtube_html.text)[0]
    return resolver_proxy.get_stream_youtube(plugin, live_id, False)
