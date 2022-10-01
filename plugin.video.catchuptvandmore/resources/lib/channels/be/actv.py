# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

import json
# noinspection PyUnresolvedReferences
from codequick import Resolver, Route
# noinspection PyUnresolvedReferences
from codequick.utils import urljoin_partial
import urlquick

from resources.lib import resolver_proxy
from resources.lib.web_utils import get_random_ua

URL_ROOT = 'https://www.antennecentre.tv/'
URL_LIVE = URL_ROOT + 'direct'

LIVE_PLAYER = 'https://tvlocales-player.freecaster.com/embed/%s.json'

PATTERN_PLAYER = re.compile(r'actv\.fcst\.tv/player/embed/(.*?)\?')
PATTERN_STREAM = re.compile(r'file\":\"(.*?)\"')


@Route.register
def list_programs(plugin, item_id, **kwargs):
    # TODO Add Replay
    pass


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_LIVE, max_age=-1)
    root = resp.parse()

    live_data = root.findall(".//div[@class='freecaster-player']")[0].get('data-fc-token')
    resp2 = urlquick.get(LIVE_PLAYER % live_data, max_age=-1)
    video_url = json.loads(resp2.text)['video']['src'][0]['src']

    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")
