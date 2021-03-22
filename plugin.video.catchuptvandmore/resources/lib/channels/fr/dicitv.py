# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re

from codequick import Resolver
import urlquick

from resources.lib import web_utils

# TODO
# Add Replay

URL_ROOT = "https://www.dici.fr"

URL_LIVE = URL_ROOT + "/player?tab=tv"

URL_STREAM = 'https://player.infomaniak.com/playerConfig.php?channel=%s'
# channel


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    channel_id = re.compile(r'\?channel\=(.*?)\&').findall(resp.text)[0]
    resp2 = urlquick.get(
        URL_STREAM % channel_id,
        headers={'User-Agent': web_utils.get_random_ua()},
        max_age=-1)
    json_parser = json.loads(resp2.text)
    stream_url = ''
    for stram_datas in json_parser['data']['integrations']:
        if 'hls' in stram_datas['type']:
            stream_url = stram_datas['url']
    return stream_url
