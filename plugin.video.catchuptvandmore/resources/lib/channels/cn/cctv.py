# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re
import socket
import requests

# noinspection PyUnresolvedReference
from codequick import Resolver
from resources.lib import resolver_proxy, web_utils

# TODO Add Replay

URL_LIVE = "https://vdn.live.cntv.cn/api2/liveHtml5.do"


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    live_id = 'cctv_p2p_hd%s' % item_id
    resp = requests.get(
        URL_LIVE + '?channel=pa://%s&client=html5&ip=%s' % (live_id, get_ip()),
        headers={
            "User-Agent": web_utils.get_random_ua(),
            'Cache-Control': 'max-age=-1, public'
        })

    replace = re.sub("^[^{]*", "", resp.text)
    replace = re.sub("(.*)}[^}]*", "\\1}", replace)
    json_parser = json.loads(replace)
    url = json_parser["hls_url"]["hls2"]

    if url.endswith('m3u8'):
        return resolver_proxy.get_stream_with_quality(plugin, video_url=url, manifest_type="hls")

    return url
