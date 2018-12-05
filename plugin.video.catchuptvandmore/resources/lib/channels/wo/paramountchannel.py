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
from resources.lib import resolver_proxy

import json
import re
import urlquick

# TO DO
# Add Replay ES, FR, ....

DESIRED_LANGUAGE = Script.setting['paramountchannel.language']

URL_LIVE_ES = 'http://www.paramountnetwork.es/en-directo/4ypes1'

# URL_LIVE_US = 'https://www.paramountnetwork.com/live-tv/oeojy2'

URL_LIVE_IT = 'http://www.paramountchannel.it/tv/diretta'

URL_LIVE_URI = 'http://media.mtvnservices.com/pmt/e1/access/index.html?uri=%s&configtype=edge'


def live_entry(plugin, item_id, item_dict):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict):

    if DESIRED_LANGUAGE.lower() == 'es':
        resp = urlquick.get(URL_LIVE_ES)
        video_uri = re.compile(
            r'\"config"\:\{\"uri\"\:\"(.*?)\"').findall(resp.text)[0]
    # elif DESIRED_LANGUAGE.lower() == 'us':
    #     resp = urlquick.get(URL_LIVE_US)
    #     video_uri = re.compile(
    #         r'\"config"\:\{\"uri\"\:\"(.*?)\"').findall(resp.text)[0]
    elif DESIRED_LANGUAGE.lower() == 'it':
        resp = urlquick.get(URL_LIVE_IT)
        video_uri_1 = re.compile(
            r'data-mtv-uri="(.*?)"').findall(resp.text)[0]
        headers = {'Content-Type': 'application/json', 'referer': 'http://www.paramountchannel.it/tv/diretta'}
        resp2 = urlquick.get(
            URL_LIVE_URI % video_uri_1, headers=headers)
        json_parser = json.loads(resp2.text)
        if 'items' not in json_parser["feed"]:
            plugin.notify('ERROR', plugin.localize(30713))
            return False
        video_uri = json_parser["feed"]["items"][0]["guid"]
    else:
        return ''
    return resolver_proxy.get_mtvnservices_stream(plugin, video_uri)
