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
from resources.lib import download

import base64
import json
import re
import urlquick

# TO DO
# Replay

URL_ROOT = 'https://www.heart.co.uk'

URL_LIVE_ID = URL_ROOT + '/tv/player/'

URL_VIDEO_VOD = 'https://player.ooyala.com/sas/player_api/v2/authorization/' \
                'embed_code/%s/%s?device=html5&domain=www.channelnewsasia.com'
# pcode, liveId

URL_GET_JS_PCODE = 'https://player.ooyala.com/core/%s'
# playeId


def live_entry(plugin, item_id, item_dict):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict):

    """Get video URL and start video player"""
    resp = urlquick.get(URL_LIVE_ID)
    live_id = re.compile(
        'div id="ooyala_(.*?)"').findall(resp.text)[0]
    player_id = re.compile(
        'player.ooyala.com/core/(.*?)"').findall(resp.text)[0]
    stream_pcode = urlquick.get(
        URL_GET_JS_PCODE % player_id)
    pcode = re.compile(
        'internal.playerParams.pcode=\'(.*?)\'').findall(stream_pcode.text)[0]
    stream_json = urlquick.get(
        URL_VIDEO_VOD % (pcode, live_id))
    stream_jsonparser = json.loads(stream_json.text)
    # Get Value url encodebase64
    for stream in stream_jsonparser["authorization_data"][live_id]["streams"]:
        if stream["delivery_type"] == 'hls':
            url_base64 = stream["url"]["data"]
    return base64.standard_b64decode(url_base64)
