# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import re
import json
import urlquick

# noinspection PyUnresolvedReferences
from codequick import Resolver

from resources.lib import resolver_proxy, web_utils

URL_ROOT = 'https://www.rtvslo.si/tv/vzivo/tv%s'
API_URL = 'https://api.rtvslo.si/ava/getLiveStream/tv.%s'

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    shortcut = {
        'slo1': 's1',
        'slo2': 's2',
        'slo3': 's3',
        'mb1': 'mb',
        'kp1': 'kp',
        'mmctv': 'mmc'
    }

    client = urlquick.get(URL_ROOT % shortcut[item_id], headers=GENERIC_HEADERS, max_age=-1)
    client_id = re.compile('client_id\=(.*?)\&').findall(client.text)[0]

    params = {
        'callback': 'ava_',
        'client_id': client_id
    }

    datas_url = urlquick.get(API_URL % item_id, headers=GENERIC_HEADERS, params=params, max_age=-1)
    json_datas = datas_url.text
    startidx = json_datas.find('(')
    endidx = json_datas.rfind(')')
    datas = json.loads((json_datas)[startidx + 1:endidx])
    video_root = datas['response']['mediaFiles'][0]
    video_url = video_root['streamer'] + video_root['file']

    return resolver_proxy.get_stream_with_quality(plugin, video_url)
