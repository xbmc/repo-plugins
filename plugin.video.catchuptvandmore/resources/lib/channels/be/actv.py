# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import json
import re

import urlquick
# noinspection PyUnresolvedReferences
from codequick import Resolver, Route
# noinspection PyUnresolvedReferences
from codequick.utils import urljoin_partial

from resources.lib import resolver_proxy, web_utils

URL_ROOT = 'https://www.antennecentre.tv/'
URL_LIVE = URL_ROOT + 'direct'

LIVE_PLAYER = 'https://tvlocales-player.freecaster.com/embed/%s.json'

PATTERN_PLAYER = re.compile(r'actv\.fcst\.tv/player/embed/(.*?)\?')
PATTERN_STREAM = re.compile(r'file\":\"(.*?)\"')

PATTERN_LIVE_TOKEN = re.compile(r'\"live_token\":\s*\"(.*?)\"')


@Route.register
def list_programs(plugin, item_id, **kwargs):
    # TODO Add Replay
    pass


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    headers = {
        "User-Agent": web_utils.get_random_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "fr-BE,en-US;q=0.7,en;q=0.3",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "referrer": URL_ROOT,
    }

    resp = urlquick.get(URL_LIVE, headers=headers, max_age=-1)
    m3u8_array = PATTERN_LIVE_TOKEN.findall(resp.text)
    if len(m3u8_array) == 0:
        plugin.notify(plugin.localize(30600), plugin.localize(30716))
        return False

    resp = urlquick.get(LIVE_PLAYER % m3u8_array[0], max_age=-1)
    video_url = json.loads(resp.text)['video']['src'][0]['src']

    return resolver_proxy.get_stream_with_quality(plugin, video_url)
