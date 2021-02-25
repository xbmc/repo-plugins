# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2017  SylvainCecchetto

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
from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment

import json
import time
import urlquick

# TO DO
# Add info LIVE TV, Replay

URL_API = 'https://beacon.playback.api.brightcove.com/telequebec/api'

URL_LIVE_DATAS = URL_API + '/epg?device_type=web&device_layout=web&datetimestamp=%s'
# datetimestamp

URL_BRIGHTCOVE_DATAS = URL_API + '/assets/%s/streams/%s'
# ContentId, StreamId


@Route.register
def list_programs(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    # TODO readd Catchup TV
    return False


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    unix_time = time.time()
    resp = urlquick.get(URL_LIVE_DATAS % unix_time)
    json_parser = json.loads(resp.text)

    content_id = json_parser["data"]["blocks"][0]["widgets"][0]["playlist"]["contents"][0]["id"]
    stream_id = json_parser["data"]["blocks"][0]["widgets"][0]["playlist"]["contents"][0]["streams"][0]["id"]

    # Build PAYLOAD
    payload = {
        "device_layout": "web",
        "device_type": "web"
    }
    resp2 = urlquick.post(URL_BRIGHTCOVE_DATAS % (content_id, stream_id),
                          data=payload)
    json_parser2 = json.loads(resp2.text)

    data_account = json_parser2["data"]["stream"]["video_provider_details"]["account_id"]
    data_player = 'default'
    data_live_id = json_parser2["data"]["stream"]["url"]
    return resolver_proxy.get_brightcove_video_json(plugin, data_account,
                                                    data_player, data_live_id)
